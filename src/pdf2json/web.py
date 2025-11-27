from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import os
import tempfile
import re
from .converter import PDFToXMLConverter
import json
from werkzeug.utils import secure_filename

APP_ROOT = Path(__file__).parents[2]
EXAMPLES = APP_ROOT / 'examples'
UPLOADS = APP_ROOT / 'uploads'
UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__, template_folder=str(APP_ROOT / 'templates'))
app.secret_key = 'dev-secret'
app.config['UPLOAD_FOLDER'] = str(UPLOADS)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXT = {'.pdf'}


def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXT


@app.route('/')
def index():
    examples = sorted(EXAMPLES.glob('*.json'))
    json_files = [e.name for e in examples]
    return render_template('index.html', json_files=json_files)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f:
            flash('No file provided')
            return redirect(request.url)
        filename = secure_filename(f.filename)
        if not allowed_file(filename):
            flash('Only PDF uploads supported')
            return redirect(request.url)
        dest = UPLOADS / filename
        f.save(dest)
        # convert to json in examples dir
        out_json = EXAMPLES / (Path(filename).stem + '.json')
        conv = PDFToXMLConverter(str(dest))
        conv.save_json(str(out_json), include_metadata=False, extract_tables=False, indent=2)
        flash(f'Uploaded and converted to {out_json.name}')
        return redirect(url_for('index'))
    return render_template('upload.html')


@app.route('/view/<jsonname>')
def view_json(jsonname):
    json_path = EXAMPLES / jsonname
    if not json_path.exists():
        flash('JSON not found')
        return redirect(url_for('index'))
    
    highlight_term = request.args.get('highlight', '')
    highlight_idx = request.args.get('match_idx', type=int)
    search_term = request.args.get('search', '').strip()
    
    with json_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    
    json_content = json.dumps(data, indent=2, ensure_ascii=False)
    
    # Handle search within this file
    if search_term:
        # Search highlighting is handled by JavaScript on the client side
        pass
    
    # If highlighting a specific match (from search results page)
    elif highlight_term and highlight_idx is not None:
        # Get all text blocks to find the specific match
        texts = []
        for page in data.get('document', {}).get('pages_data', []):
            for block in page.get('blocks', []):
                for line in block.get('lines', []):
                    texts.append(line.strip())
        
        if highlight_idx < len(texts):
            target_text = texts[highlight_idx]
            # Highlight the target text in the JSON content
            pattern = re.compile(re.escape(target_text), re.IGNORECASE)
            json_content = pattern.sub(f'<span class="highlight-match">{target_text}</span>', json_content)
    
    return render_template('view.html', jsonname=jsonname, json_content=json_content, highlight_term=search_term or highlight_term)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        if not search_term:
            flash('Please enter a search term')
            return redirect(url_for('index'))
        
        results = []
        json_files = sorted(EXAMPLES.glob('*.json'))
        
        for json_file in json_files:
            try:
                with json_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Get all text blocks
                texts = []
                for page in data.get('document', {}).get('pages_data', []):
                    for block in page.get('blocks', []):
                        for line in block.get('lines', []):
                            texts.append(line.strip())
                
                # Search for matches with indices
                pattern = re.compile(search_term, re.IGNORECASE)
                matches_with_indices = []
                for idx, text in enumerate(texts):
                    if pattern.search(text):
                        matches_with_indices.append((idx, text))
                
                if matches_with_indices:
                    results.append({
                        'filename': json_file.name,
                        'matches': matches_with_indices[:10],  # List of (index, text) tuples
                        'total_matches': len(matches_with_indices)
                    })
                    
            except Exception as e:
                continue  # Skip files that can't be read
        
        return render_template('search_results.html', search_term=search_term, results=results)
    
    return redirect(url_for('index'))


@app.route('/download/<jsonname>')
def download_json(jsonname):
    json_path = EXAMPLES / jsonname
    if not json_path.exists():
        flash('JSON not found')
        return redirect(url_for('index'))
    return send_file(str(json_path), as_attachment=True, download_name=jsonname)


if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=8000)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
