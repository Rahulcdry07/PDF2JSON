#!/usr/bin/env python3
"""
Database Management Interface for DSR System

Provides a web-based UI for managing DSR codes with:
- View, add, edit, delete DSR codes
- Bulk import from CSV/Excel
- Version control and audit logs
- Search and filter capabilities
- Database backup/restore
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import sqlite3
import csv
import json
import os
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
import shutil
import sys

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

app = Flask(__name__)
app.secret_key = 'database-manager-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

REFERENCE_FILES = PROJECT_ROOT / 'reference_files'
BACKUP_DIR = PROJECT_ROOT / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

# Available categories
CATEGORIES = []
for cat_dir in REFERENCE_FILES.iterdir():
    if cat_dir.is_dir():
        db_file = cat_dir / f"DSR_{cat_dir.name.title()}_combined.db"
        if db_file.exists():
            CATEGORIES.append(cat_dir.name)


def get_db_connection(category='civil'):
    """Get database connection for a category."""
    db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found for category: {category}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_audit_log_table(conn):
    """Create audit log table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id TEXT,
            old_value TEXT,
            new_value TEXT,
            user TEXT,
            ip_address TEXT
        )
    """)
    conn.commit()


def log_audit(conn, action, table_name, record_id=None, old_value=None, new_value=None):
    """Log an audit entry."""
    create_audit_log_table(conn)
    
    conn.execute("""
        INSERT INTO audit_log (timestamp, action, table_name, record_id, old_value, new_value, user, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        action,
        table_name,
        record_id,
        json.dumps(old_value) if old_value else None,
        json.dumps(new_value) if new_value else None,
        'admin',  # TODO: Add proper user authentication
        request.remote_addr if request else 'system'
    ))
    conn.commit()


@app.route('/')
def index():
    """Database management home page."""
    return render_template('database_manager.html', categories=CATEGORIES)


@app.route('/api/stats/<category>')
def get_stats(category):
    """Get database statistics for a category."""
    try:
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        # Total codes
        cursor.execute("SELECT COUNT(*) FROM dsr_codes")
        total_codes = cursor.fetchone()[0]
        
        # Total chapters
        cursor.execute("SELECT COUNT(DISTINCT chapter) FROM dsr_codes")
        total_chapters = cursor.fetchone()[0]
        
        # Rate statistics
        cursor.execute("SELECT MIN(rate), MAX(rate), AVG(rate) FROM dsr_codes")
        rate_stats = cursor.fetchone()
        
        # Recent changes
        cursor.execute("""
            SELECT COUNT(*) FROM audit_log 
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        recent_changes = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_codes': total_codes,
                'total_chapters': total_chapters,
                'min_rate': rate_stats[0],
                'max_rate': rate_stats[1],
                'avg_rate': round(rate_stats[2], 2) if rate_stats[2] else 0,
                'recent_changes': recent_changes
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/codes/<category>')
def get_codes(category):
    """Get DSR codes with pagination and filtering."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        chapter_filter = request.args.get('chapter', '')
        
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM dsr_codes WHERE category = ?"
        params = [category]
        
        if search:
            query += " AND (code LIKE ? OR description LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if chapter_filter:
            query += " AND chapter LIKE ?"
            params.append(f'%{chapter_filter}%')
        
        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        query += " ORDER BY code LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        codes = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'codes': codes,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/code/<category>/<code>')
def get_code(category, code):
    """Get a single DSR code."""
    try:
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM dsr_codes WHERE code = ? AND category = ?", (code, category))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return jsonify({'success': True, 'code': dict(result)})
        else:
            return jsonify({'success': False, 'error': 'Code not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/code/<category>', methods=['POST'])
def add_code(category):
    """Add a new DSR code."""
    try:
        data = request.get_json()
        
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        # Check if code already exists
        cursor.execute("SELECT code FROM dsr_codes WHERE code = ? AND category = ?", 
                      (data['code'], category))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Code already exists'}), 400
        
        # Insert new code
        cursor.execute("""
            INSERT INTO dsr_codes (code, chapter, section, description, unit, rate, volume, page, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['code'],
            data.get('chapter', ''),
            data.get('section', ''),
            data['description'],
            data['unit'],
            float(data['rate']),
            data.get('volume', ''),
            data.get('page', ''),
            category
        ))
        
        # Log audit
        log_audit(conn, 'INSERT', 'dsr_codes', data['code'], None, data)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Code added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/code/<category>/<code>', methods=['PUT'])
def update_code(category, code):
    """Update an existing DSR code."""
    try:
        data = request.get_json()
        
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        # Get old value
        cursor.execute("SELECT * FROM dsr_codes WHERE code = ? AND category = ?", (code, category))
        old_row = cursor.fetchone()
        if not old_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Code not found'}), 404
        
        old_value = dict(old_row)
        
        # Update code
        cursor.execute("""
            UPDATE dsr_codes 
            SET chapter = ?, section = ?, description = ?, unit = ?, rate = ?, volume = ?, page = ?
            WHERE code = ? AND category = ?
        """, (
            data.get('chapter', ''),
            data.get('section', ''),
            data['description'],
            data['unit'],
            float(data['rate']),
            data.get('volume', ''),
            data.get('page', ''),
            code,
            category
        ))
        
        # Log audit
        log_audit(conn, 'UPDATE', 'dsr_codes', code, old_value, data)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Code updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/code/<category>/<code>', methods=['DELETE'])
def delete_code(category, code):
    """Delete a DSR code."""
    try:
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        # Get old value for audit
        cursor.execute("SELECT * FROM dsr_codes WHERE code = ? AND category = ?", (code, category))
        old_row = cursor.fetchone()
        if not old_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Code not found'}), 404
        
        old_value = dict(old_row)
        
        # Delete code
        cursor.execute("DELETE FROM dsr_codes WHERE code = ? AND category = ?", (code, category))
        
        # Log audit
        log_audit(conn, 'DELETE', 'dsr_codes', code, old_value, None)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Code deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chapters/<category>')
def get_chapters(category):
    """Get list of all chapters in a category."""
    try:
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT chapter, COUNT(*) as count
            FROM dsr_codes
            WHERE category = ?
            GROUP BY chapter
            ORDER BY chapter
        """, (category,))
        
        chapters = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'chapters': chapters})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/import/<category>', methods=['POST'])
def bulk_import(category):
    """Bulk import DSR codes from CSV file."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Only CSV files are supported'}), 400
        
        # Read CSV
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(content.splitlines())
        
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        errors = []
        
        for row in csv_reader:
            try:
                # Check if code exists
                cursor.execute("SELECT code FROM dsr_codes WHERE code = ? AND category = ?",
                             (row['code'], category))
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                # Insert
                cursor.execute("""
                    INSERT INTO dsr_codes (code, chapter, section, description, unit, rate, volume, page, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['code'],
                    row.get('chapter', ''),
                    row.get('section', ''),
                    row['description'],
                    row['unit'],
                    float(row['rate']),
                    row.get('volume', ''),
                    row.get('page', ''),
                    category
                ))
                
                imported += 1
            except Exception as e:
                errors.append(f"Row {imported + skipped + 1}: {str(e)}")
        
        # Log audit
        log_audit(conn, 'BULK_INSERT', 'dsr_codes', None, None, 
                 {'imported': imported, 'skipped': skipped})
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/<category>')
def export_codes(category):
    """Export DSR codes to CSV."""
    try:
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM dsr_codes WHERE category = ? ORDER BY code", (category,))
        rows = cursor.fetchall()
        
        # Create CSV
        output = []
        if rows:
            output.append(','.join(rows[0].keys()))
            for row in rows:
                output.append(','.join(str(v) for v in row))
        
        conn.close()
        
        # Save to file
        filename = f"DSR_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = BACKUP_DIR / filename
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(output))
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backup/<category>', methods=['POST'])
def backup_database(category):
    """Create a backup of the database."""
    try:
        db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"DSR_{category}_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename
        
        shutil.copy2(db_path, backup_path)
        
        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'filename': backup_filename,
            'size': backup_path.stat().st_size
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backups')
def list_backups():
    """List all database backups."""
    try:
        backups = []
        for backup_file in BACKUP_DIR.glob('*.db'):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'success': True, 'backups': backups})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/audit/<category>')
def get_audit_log(category):
    """Get audit log entries."""
    try:
        limit = int(request.args.get('limit', 100))
        
        conn = get_db_connection(category)
        cursor = conn.cursor()
        
        create_audit_log_table(conn)
        
        cursor.execute("""
            SELECT * FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Database Management Interface")
    print("=" * 60)
    print("\nStarting server on http://localhost:5002")
    print("\nFeatures:")
    print("  - View and search DSR codes")
    print("  - Add, edit, delete codes")
    print("  - Bulk import from CSV")
    print("  - Export to CSV")
    print("  - Database backup/restore")
    print("  - Audit logging")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, port=5002, host='0.0.0.0')
