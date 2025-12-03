# Integration Examples

This document provides practical examples for integrating `pdf2json-dsr` into other projects.

## Table of Contents

1. [Installation](#installation)
2. [As a Python Library](#as-a-python-library)
3. [As a Web Service (Flask Integration)](#as-a-web-service-flask-integration)
4. [As a Microservice (Docker)](#as-a-microservice-docker)
5. [As an API Client](#as-an-api-client)
6. [Django Integration](#django-integration)
7. [FastAPI Integration](#fastapi-integration)
8. [AWS Lambda Function](#aws-lambda-function)

---

## Installation

### From PyPI (after publishing)
```bash
pip install pdf2json-dsr
```

### From Source
```bash
git clone https://github.com/Rahulcdry07/PDF2JSON.git
cd PDF2JSON
pip install -e .
```

---

## As a Python Library

### Example 1: PDF Conversion
```python
from pdf2json import PDFToXMLConverter
from pathlib import Path

# Initialize converter
converter = PDFToXMLConverter()

# Convert PDF to JSON
input_pdf = Path("construction_project.pdf")
output_json = Path("output.json")

result = converter.convert_pdf_to_json(input_pdf, output_json)
print(f"Converted: {result}")

# Read the JSON data
import json
with open(output_json) as f:
    data = json.load(f)
    print(f"Pages: {len(data['pages'])}")
```

### Example 2: DSR Rate Matching
```python
from pdf2json import (
    load_dsr_database,
    match_with_database,
    load_input_file
)
from pathlib import Path

# Load DSR database
db_path = Path("data/reference/DSR_combined.db")
db_conn = load_dsr_database(db_path)

# Load input items (construction items to match)
input_file = Path("project_items.json")
items = load_input_file(input_file)

# Match items with DSR rates
matched_results = match_with_database(
    items, 
    db_conn, 
    similarity_threshold=0.3
)

# Process results
for result in matched_results:
    print(f"Code: {result['dsr_code']}")
    print(f"Description: {result['description']}")
    print(f"Rate: ₹{result['rate']}")
    print(f"Total Cost: ₹{result['total_cost']}")
    print("---")

db_conn.close()
```

### Example 3: Text Similarity
```python
from pdf2json import calculate_text_similarity

text1 = "Excavation of earth for foundation"
text2 = "Earth excavation for building foundation"

similarity = calculate_text_similarity(text1, text2)
print(f"Similarity: {similarity:.2%}")  # e.g., 85%
```

### Example 4: Excel to PDF Conversion
```python
from pdf2json import ExcelToPDFConverter
from pathlib import Path

# Initialize converter
converter = ExcelToPDFConverter("project_data.xlsx")

# Convert specific sheet
output_pdf = Path("sheet1.pdf")
converter.convert_sheet_to_pdf(
    sheet_name="Sheet1",
    output_path=output_pdf,
    page_size="A4",
    orientation="portrait"
)

# Convert all sheets to separate PDFs
for sheet in converter.get_sheet_names():
    converter.convert_sheet_to_pdf(
        sheet_name=sheet,
        output_path=Path(f"{sheet}.pdf")
    )

converter.close()
```

---

## As a Web Service (Flask Integration)

### Example 1: Embed in Existing Flask App
```python
from flask import Flask
from pdf2json import create_app as create_pdf2json_app

# Your main application
app = Flask(__name__)

@app.route('/')
def home():
    return "Main Application"

# Mount PDF2JSON as a blueprint
pdf_app = create_pdf2json_app()

# Register routes under /pdf2json prefix
from werkzeug.middleware.dispatcher import DispatcherMiddleware
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/pdf2json': pdf_app
})

if __name__ == '__main__':
    app.run(port=5000)
```

### Example 2: Custom Configuration
```python
from pdf2json import create_app

# Create app with custom config
app = create_app({
    'SECRET_KEY': 'your-production-secret',
    'MAX_CONTENT_LENGTH': 100 * 1024 * 1024,  # 100 MB
    'UPLOAD_FOLDER': '/var/uploads',
    'DEBUG': False
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Example 3: Add Custom Routes
```python
from pdf2json import app
from flask import jsonify

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'pdf2json-dsr',
        'version': '1.0.0'
    })

@app.route('/api/custom-endpoint')
def custom_endpoint():
    # Your custom logic using pdf2json functions
    from pdf2json import calculate_text_similarity
    
    result = calculate_text_similarity("text1", "text2")
    return jsonify({'similarity': result})

if __name__ == '__main__':
    app.run()
```

---

## As a Microservice (Docker)

### Example 1: Docker Compose Integration
Create `docker-compose.yml` in your project:

```yaml
version: '3.8'

services:
  # Your main application
  webapp:
    build: ./webapp
    ports:
      - "3000:3000"
    depends_on:
      - pdf2json
    environment:
      - PDF_SERVICE_URL=http://pdf2json:8000

  # PDF2JSON service
  pdf2json:
    image: ghcr.io/rahulcdry07/pdf2json:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${PDF_SECRET_KEY}

  # Optional: Database for DSR rates
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=dsr_rates
      - POSTGRES_USER=dsr_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Example 2: Call from Another Service
```python
import requests

# Your application code
def convert_pdf_via_microservice(pdf_path):
    """Call PDF2JSON microservice"""
    url = "http://pdf2json:8000/upload"
    
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Conversion failed: {response.text}")

# Usage
result = convert_pdf_via_microservice("project.pdf")
print(result)
```

---

## As an API Client

### Example 1: Python Requests
```python
import requests
from pathlib import Path

class PDF2JSONClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_pdf(self, pdf_path):
        """Upload and convert PDF"""
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/upload",
                files=files
            )
        return response.json()
    
    def cost_estimation(self, input_json, db_path):
        """Run cost estimation"""
        data = {
            'input_file': input_json,
            'db_path': db_path
        }
        response = requests.post(
            f"{self.base_url}/cost-estimation",
            json=data
        )
        return response.json()
    
    def get_analytics(self):
        """Get analytics data"""
        response = requests.get(f"{self.base_url}/analytics/api/stats")
        return response.json()

# Usage
client = PDF2JSONClient()
result = client.upload_pdf("project.pdf")
print(result)
```

### Example 2: JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

class PDF2JSONClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async uploadPDF(pdfPath) {
        const form = new FormData();
        form.append('file', fs.createReadStream(pdfPath));

        const response = await axios.post(
            `${this.baseUrl}/upload`,
            form,
            { headers: form.getHeaders() }
        );
        
        return response.data;
    }

    async costEstimation(inputJson, dbPath) {
        const response = await axios.post(
            `${this.baseUrl}/cost-estimation`,
            { input_file: inputJson, db_path: dbPath }
        );
        
        return response.data;
    }

    async getAnalytics() {
        const response = await axios.get(
            `${this.baseUrl}/analytics/api/stats`
        );
        
        return response.data;
    }
}

// Usage
const client = new PDF2JSONClient();
client.uploadPDF('project.pdf')
    .then(result => console.log(result))
    .catch(err => console.error(err));
```

---

## Django Integration

### Example: Django View Integration
```python
# views.py
from django.shortcuts import render
from django.http import JsonResponse
from pdf2json import PDFToXMLConverter, match_with_database, load_dsr_database
from pathlib import Path

def convert_pdf_view(request):
    if request.method == 'POST':
        pdf_file = request.FILES['pdf']
        
        # Save temporarily
        temp_path = Path(f'/tmp/{pdf_file.name}')
        with open(temp_path, 'wb') as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)
        
        # Convert
        converter = PDFToXMLConverter()
        output_path = temp_path.with_suffix('.json')
        converter.convert_pdf_to_json(temp_path, output_path)
        
        # Read result
        import json
        with open(output_path) as f:
            result = json.load(f)
        
        return JsonResponse({'success': True, 'data': result})
    
    return render(request, 'upload.html')

def cost_estimation_view(request):
    if request.method == 'POST':
        input_data = request.POST.get('input_data')
        
        # Load DSR database
        db_path = Path('data/reference/DSR_combined.db')
        db_conn = load_dsr_database(db_path)
        
        # Match rates
        items = json.loads(input_data)
        results = match_with_database(items, db_conn)
        
        db_conn.close()
        
        return JsonResponse({'results': results})
    
    return render(request, 'cost_estimation.html')
```

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('convert/', views.convert_pdf_view, name='convert_pdf'),
    path('estimate/', views.cost_estimation_view, name='cost_estimation'),
]
```

---

## FastAPI Integration

### Example: FastAPI Service
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdf2json import PDFToXMLConverter, match_with_database, load_dsr_database
from pathlib import Path
import json
import tempfile

app = FastAPI(title="PDF2JSON API Service")

# Initialize converter
converter = PDFToXMLConverter()
db_conn = None

@app.on_event("startup")
async def startup_event():
    global db_conn
    db_path = Path("data/reference/DSR_combined.db")
    db_conn = load_dsr_database(db_path)

@app.on_event("shutdown")
async def shutdown_event():
    if db_conn:
        db_conn.close()

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """Convert PDF to JSON"""
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        # Convert
        output_path = tmp_path.with_suffix('.json')
        converter.convert_pdf_to_json(tmp_path, output_path)
        
        # Read result
        with open(output_path) as f:
            result = json.load(f)
        
        # Cleanup
        tmp_path.unlink()
        output_path.unlink()
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/estimate")
async def cost_estimation(items: list):
    """Estimate costs for construction items"""
    try:
        results = match_with_database(items, db_conn)
        return JSONResponse(content={'results': results})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pdf2json-dsr"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## AWS Lambda Function

### Example: Lambda Handler
```python
import json
import boto3
from pdf2json import PDFToXMLConverter
from pathlib import Path
import tempfile

s3 = boto3.client('s3')
converter = PDFToXMLConverter()

def lambda_handler(event, context):
    """
    AWS Lambda function to convert PDF from S3
    
    Event format:
    {
        "bucket": "my-bucket",
        "key": "input/project.pdf",
        "output_key": "output/project.json"
    }
    """
    try:
        bucket = event['bucket']
        input_key = event['key']
        output_key = event.get('output_key', input_key.replace('.pdf', '.json'))
        
        # Download from S3
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_pdf:
            s3.download_fileobj(bucket, input_key, tmp_pdf)
            tmp_pdf.flush()
            
            # Convert
            with tempfile.NamedTemporaryFile(suffix='.json', mode='w') as tmp_json:
                converter.convert_pdf_to_json(
                    Path(tmp_pdf.name),
                    Path(tmp_json.name)
                )
                
                # Upload to S3
                tmp_json.seek(0)
                s3.upload_fileobj(tmp_json, bucket, output_key)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Conversion successful',
                'output_key': output_key
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
```

### Requirements for Lambda
```txt
# requirements.txt for Lambda layer
pdf2json-dsr
PyMuPDF
boto3
```

---

## Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Resource Management**: Close database connections and file handles
3. **Configuration**: Use environment variables for paths and settings
4. **Logging**: Implement proper logging for debugging
5. **Testing**: Test integration in isolated environments first
6. **Security**: Validate file uploads, sanitize inputs
7. **Performance**: Use connection pooling for database access
8. **Monitoring**: Implement health checks and metrics

## Support

For more examples and support:
- GitHub Issues: https://github.com/Rahulcdry07/PDF2JSON/issues
- Documentation: See `docs/` directory
- API Docs: http://localhost:8000/api/docs (when running)
