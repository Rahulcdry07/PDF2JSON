from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import os
import tempfile
import re
from .converter import PDFToXMLConverter
import json
import markdown
from markupsafe import Markup
from werkzeug.utils import secure_filename
import sys
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from collections import defaultdict

APP_ROOT = Path(__file__).parents[2]
EXAMPLES = APP_ROOT / 'examples'
INPUT_FILES = EXAMPLES / 'input_files'
OUTPUT_REPORTS = EXAMPLES / 'output_reports'
UPLOADS = APP_ROOT / 'uploads'
UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__, template_folder=str(APP_ROOT / 'templates'))
app.secret_key = 'dev-secret'
app.config['UPLOAD_FOLDER'] = str(UPLOADS)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# Add markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    return Markup(markdown.markdown(text, extensions=['tables']))

# Add basename filter
@app.template_filter('basename')
def basename_filter(path):
    return Path(path).name

ALLOWED_EXT = {'.pdf'}


def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXT


@app.route('/')
def index():
    # Organize files by category
    files = {
        'input': [],
        'output': [],
        'reference': []
    }
    
    # Input files (original converted PDFs)
    if INPUT_FILES.exists():
        for json_file in sorted(INPUT_FILES.glob('*.json')):
            files['input'].append({
                'name': json_file.name,
                'type': 'json',
                'description': 'Input file with items to be priced'
            })
    
    # Output reports (DSR matching results)
    if OUTPUT_REPORTS.exists():
        for json_file in sorted(OUTPUT_REPORTS.glob('*.json')):
            files['output'].append({
                'name': json_file.name,
                'type': 'json',
                'description': 'DSR matching analysis report'
            })
        
        # Also include CSV and markdown reports
        for report_file in sorted(OUTPUT_REPORTS.glob('*.csv')):
            files['output'].append({
                'name': report_file.name,
                'type': 'csv',
                'description': 'Excel-compatible rate report'
            })
        
        for report_file in sorted(OUTPUT_REPORTS.glob('*.md')):
            files['output'].append({
                'name': report_file.name,
                'type': 'md',
                'description': 'Human-readable summary report'
            })
    
    # Reference files (DSR databases)
    reference_dir = EXAMPLES / 'reference_files'
    if reference_dir.exists():
        for ref_file in sorted(reference_dir.glob('*.json')):
            files['reference'].append({
                'name': ref_file.name,
                'type': 'json',
                'description': 'DSR reference database'
            })
        for ref_file in sorted(reference_dir.glob('*.xml')):
            files['reference'].append({
                'name': ref_file.name,
                'type': 'xml',
                'description': 'DSR reference database (XML)'
            })
    
    return render_template('index.html', files=files)


@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 100 MB.')
    return redirect(url_for('upload'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            f = request.files.get('pdf')
            if not f:
                flash('No file provided')
                return redirect(request.url)
            
            if f.filename == '':
                flash('No file selected')
                return redirect(request.url)
                
            filename = secure_filename(f.filename)
            if not filename:
                flash('Invalid filename')
                return redirect(request.url)
                
            if not allowed_file(filename):
                flash('Only PDF uploads supported')
                return redirect(request.url)
            
            dest = UPLOADS / filename
            f.save(dest)
            
            # Check if file was actually saved and has content
            if not dest.exists() or dest.stat().st_size == 0:
                flash('Failed to save file or file is empty')
                return redirect(request.url)
            
            # convert to json in input_files dir
            INPUT_FILES.mkdir(exist_ok=True)
            out_json = INPUT_FILES / (Path(filename).stem + '.json')
            conv = PDFToXMLConverter(str(dest))
            conv.save_json(str(out_json), include_metadata=False, extract_tables=False, indent=2)
            flash(f'Successfully uploaded and converted to {out_json.name}')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(request.url)
            
    return render_template('upload.html')


@app.route('/view/<path:filepath>')
def view_json(filepath):
    # Handle different file locations
    if filepath.startswith('input_files/'):
        json_path = INPUT_FILES / filepath[12:]  # Remove 'input_files/' prefix
    elif filepath.startswith('output_reports/'):
        json_path = OUTPUT_REPORTS / filepath[15:]  # Remove 'output_reports/' prefix
    elif filepath.startswith('reference_files/'):
        json_path = EXAMPLES / 'reference_files' / filepath[16:]  # Remove 'reference_files/' prefix
    else:
        json_path = EXAMPLES / filepath  # Legacy location
    
    if not json_path.exists():
        flash('File not found')
        return redirect(url_for('index'))
    
    # Determine file type and handle appropriately
    file_extension = json_path.suffix.lower()
    
    if file_extension == '.csv':
        # Handle CSV files
        with json_path.open('r', encoding='utf-8') as f:
            csv_content = f.read()
        return render_template('view_csv.html', filename=json_path.name, csv_content=csv_content)
    
    elif file_extension == '.md':
        # Handle Markdown files
        with json_path.open('r', encoding='utf-8') as f:
            md_content = f.read()
        return render_template('view_markdown.html', filename=json_path.name, md_content=md_content)
    
    elif file_extension == '.json':
        # Handle JSON files - check if it's a matched rates file
        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        # If it's a matched rates file, show it in a formatted table
        if 'matched_items' in data and 'summary' in data:
            return render_template('view_report.html',
                                 report=data,
                                 filename=json_path.name)
        else:
            # For other JSON files, show raw JSON
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            return f"<html><head><title>{json_path.name}</title></head><body><pre>{json_content}</pre></body></html>"
    
    else:
        flash('Unsupported file type')
        return redirect(url_for('index'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        if not search_term:
            flash('Please enter a search term')
            return redirect(url_for('index'))
        
        results = []
        
        # Search in all directories
        search_locations = [
            (INPUT_FILES, 'input_files/'),
            (OUTPUT_REPORTS, 'output_reports/'),
            (EXAMPLES / 'reference_files', 'reference_files/')
        ]
        
        for location_path, url_prefix in search_locations:
            if location_path.exists():
                for json_file in sorted(location_path.glob('*.json')):
                    try:
                        with json_file.open('r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Get all text blocks using correct JSON structure
                        texts = []
                        # Try both possible structures
                        pages_data = data.get('pages', []) or data.get('document', {}).get('pages_data', [])
                        
                        for page in pages_data:
                            for block in page.get('blocks', []):
                                # Handle both line formats
                                lines = block.get('lines', [])
                                for line in lines:
                                    if isinstance(line, str):
                                        # Simple string format
                                        texts.append(line.strip())
                                    elif isinstance(line, dict) and 'spans' in line:
                                        # Complex span format
                                        for span in line.get('spans', []):
                                            text = span.get('text', '').strip()
                                            if text:
                                                texts.append(text)
                        
                        # Search for matches with indices
                        pattern = re.compile(search_term, re.IGNORECASE)
                        matches_with_indices = []
                        for idx, text in enumerate(texts):
                            if pattern.search(text):
                                matches_with_indices.append((idx, text))
                        
                        if matches_with_indices:
                            results.append({
                                'filename': json_file.name,
                                'filepath': url_prefix + json_file.name,
                                'matches': matches_with_indices[:10],  # List of (index, text) tuples
                                'total_matches': len(matches_with_indices),
                                'search_term': search_term  # Include search term for highlighting
                            })
                            
                    except Exception as e:
                        continue  # Skip files that can't be read
        
        return render_template('search_results.html', search_term=search_term, results=results)
    
    return redirect(url_for('index'))


@app.route('/cost-estimation', methods=['GET', 'POST'])
def cost_estimation():
    if request.method == 'POST':
        try:
            input_file = request.form.get('input_file')
            reference_files = request.form.getlist('reference_files')
            
            if not input_file:
                flash('Please select an input file')
                return redirect(request.url)
            
            if not reference_files:
                flash('Please select at least one reference file')
                return redirect(request.url)
            
            # Process the cost estimation
            result = process_cost_estimation(input_file, reference_files)
            
            if result['success']:
                flash(f"Cost estimation completed! Total: ₹{result['total_amount']:,.2f}")
                return render_template('cost_estimation.html', 
                                     result=result, 
                                     input_files=get_input_files(),
                                     reference_files=get_reference_files())
            else:
                flash(f"Error: {result['error']}")
                return redirect(request.url)
                
        except Exception as e:
            flash(f'Error processing cost estimation: {str(e)}')
            return redirect(request.url)
    
    # GET request - show the form
    return render_template('cost_estimation.html', 
                         input_files=get_input_files(),
                         reference_files=get_reference_files())


@app.route('/download/<jsonname>')
def download_json(jsonname):
    json_path = EXAMPLES / jsonname
    if not json_path.exists():
        flash('JSON not found')
        return redirect(url_for('index'))
    return send_file(str(json_path), as_attachment=True, download_name=jsonname)


def get_input_files():
    """Get list of available input files"""
    files = []
    if INPUT_FILES.exists():
        for json_file in sorted(INPUT_FILES.glob('*.json')):
            files.append({
                'name': json_file.name,
                'path': f'input_files/{json_file.name}'
            })
    return files


def get_reference_files():
    """Get list of available reference files"""
    files = []
    reference_dir = EXAMPLES / 'reference_files'
    if reference_dir.exists():
        for json_file in sorted(reference_dir.glob('*.json')):
            files.append({
                'name': json_file.name,
                'path': f'reference_files/{json_file.name}'
            })
    return files


def process_cost_estimation(input_file: str, reference_files: List[str]) -> Dict:
    """Process cost estimation by running the DSR matching script."""
    try:
        import subprocess
        
        # Use the new SQLite-based matching script
        script_path = APP_ROOT / 'scripts' / 'match_dsr_rates_sqlite.py'
        database_path = EXAMPLES / 'reference_files' / 'DSR_combined.db'
        
        if not script_path.exists():
            return {'success': False, 'error': 'DSR matching script not found. Please ensure match_dsr_rates_sqlite.py exists.'}
        
        if not database_path.exists():
            return {'success': False, 'error': 'DSR database not found. Please run create_alternative_formats.py first to generate DSR_combined.db'}
        
        # Determine input file path
        if input_file.startswith('input_files/'):
            input_path = INPUT_FILES / input_file[12:]
        else:
            input_path = INPUT_FILES / input_file
        
        if not input_path.exists():
            return {'success': False, 'error': f'Input file not found: {input_file}'}
        
        # Run the DSR matching script with the new SQLite approach
        result = subprocess.run([
            sys.executable, 
            str(script_path),
            '-i', str(input_path),
            '-d', str(database_path),
            '-o', str(OUTPUT_REPORTS)
        ], capture_output=True, text=True, cwd=str(APP_ROOT / 'scripts'))
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            return {'success': False, 'error': f'Script failed: {error_msg}'}
        
        # Determine output file name based on input file name
        output_filename = f"{input_path.stem}_matched_rates.json"
        output_file = OUTPUT_REPORTS / output_filename
        
        if not output_file.exists():
            return {'success': False, 'error': f'Output file not found: {output_filename}'}
        
        with open(output_file, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        # Adapt the output format for the web interface
        summary = output_data.get('summary', {})
        items = output_data.get('matched_items', [])
        
        return {
            'success': True,
            'total_amount': summary.get('total_estimated_amount', 0),
            'matched_items': items,
            'summary': {
                'total_items': summary.get('total_items', 0),
                'matched_items': summary.get('exact_matches', 0) + summary.get('code_match_description_mismatch', 0),
                'unmatched_items': summary.get('not_found', 0),
                'total_amount': summary.get('total_estimated_amount', 0)
            },
            'result_file': output_filename,
            'script_output': result.stdout
        }
        
    except Exception as e:
        import traceback
        return {'success': False, 'error': f'{str(e)}\n\nTraceback:\n{traceback.format_exc()}'}


if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=8000)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
