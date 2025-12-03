# API Documentation & Analytics Guide

## 📖 Overview

PDF2JSON now includes comprehensive API documentation and a real-time analytics dashboard to monitor usage, performance, and system health.

## 🎯 Features

### API Documentation
- **Interactive Documentation**: Browse all API endpoints with detailed descriptions
- **Request/Response Examples**: See example requests and responses for each endpoint
- **Search & Filter**: Search for specific endpoints or filter by category
- **Try It Out**: Test endpoints directly from the documentation interface

### Analytics Dashboard
- **Real-time Metrics**: Track API calls, conversions, and performance in real-time
- **Visual Charts**: Interactive charts showing usage trends and distributions
- **Performance Monitoring**: Monitor response times and error rates
- **Activity Logs**: View recent API activity with detailed information

## 🚀 Quick Start

### Accessing API Documentation

Visit: `http://localhost:8000/api/docs`

The documentation provides:
- Complete list of all available endpoints
- HTTP methods (GET, POST, PUT, DELETE)
- Request parameters and body schemas
- Response formats and status codes
- Example cURL commands

### Accessing Analytics Dashboard

Visit: `http://localhost:8000/analytics`

The dashboard shows:
- Total API calls
- PDF conversions count
- Cost estimations performed
- Average response time
- Success/error rates
- Hourly usage charts
- Endpoint distribution
- Recent activity logs

## 📊 API Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-04T10:30:00Z",
  "service": "pdf2json-dsr"
}
```

#### API Statistics
```http
GET /api/stats
```

**Response:**
```json
{
  "total_api_calls": 1543,
  "total_conversions": 234,
  "total_cost_estimations": 89,
  "avg_response_time": 145.6,
  "error_rate": 2.3,
  "popular_endpoints": [...],
  "recent_activity": [...]
}
```

### PDF Conversion Endpoints

#### Upload PDF
```http
POST /upload
Content-Type: multipart/form-data

pdf: <file>
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "pdf=@document.pdf"
```

#### View File
```http
GET /view/{filepath}
```

**Example:**
```bash
curl http://localhost:8000/view/input_files/example.json
```

#### Search Files
```http
POST /search
Content-Type: application/x-www-form-urlencoded

search_term=keyword
```

### DSR Matching Endpoints

#### Cost Estimation
```http
POST /cost-estimation
Content-Type: application/x-www-form-urlencoded

input_file=example.json
reference_files[]=civil_dsr.json
reference_files[]=electrical_dsr.json
```

### Excel Operations Endpoints

#### List Excel Sheets
```http
POST /api/excel/sheets
Content-Type: multipart/form-data

file: <excel_file>
```

**Response:**
```json
{
  "success": true,
  "sheets": ["Sheet1", "Data", "Summary"]
}
```

#### Convert Excel to PDF
```http
POST /api/excel/convert
Content-Type: multipart/form-data

file: <excel_file>
sheets: ["Sheet1", "Sheet2"]
orientation: portrait
page_size: A4
output_mode: combined
```

## 📈 Analytics Features

### Tracked Metrics

1. **API Calls**
   - Total number of API requests
   - Requests per hour/day
   - Growth rate

2. **Conversions**
   - Total PDF conversions
   - Success rate
   - Failed conversions

3. **Cost Estimations**
   - Total estimations performed
   - Average match rate
   - Items processed

4. **Performance**
   - Average response time
   - Response time by endpoint
   - Performance trends

5. **Errors**
   - Total errors
   - Error rate percentage
   - Error types and frequency

### Dashboard Sections

#### Summary Cards
- Quick overview of key metrics
- Percentage changes from previous period
- Color-coded status indicators

#### Charts
- **API Calls Over Time**: Line chart showing hourly activity
- **Endpoint Distribution**: Pie chart of most used endpoints

#### Tables
- **Popular Endpoints**: Most frequently called endpoints with performance metrics
- **Recent Activity**: Last 20 API calls with timestamps and status codes

## 🔧 Configuration

### Analytics Settings

The analytics tracker stores data in memory by default. For production use:

1. **Redis Integration** (Recommended):
```python
# In web.py
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

2. **Database Storage**:
```python
# Store analytics in SQLite/PostgreSQL
# Implement persistent storage for long-term analysis
```

3. **History Limit**:
```python
# Adjust max_history to control memory usage
analytics_tracker.max_history = 1000  # Keep last 1000 requests
```

### Customization

#### Adding Custom Metrics

```python
# In web.py
def track_custom_metric(metric_name, value):
    analytics_tracker.custom_metrics[metric_name] = value
```

#### Filtering Sensitive Data

```python
# Exclude certain paths from tracking
EXCLUDED_PATHS = ['/admin', '/private']

@app.before_request
def filter_tracking():
    if request.path in EXCLUDED_PATHS:
        g.skip_tracking = True
```

## 📊 Using the Analytics API

### Python Client Example

```python
import requests

# Get current statistics
response = requests.get('http://localhost:8000/api/stats')
stats = response.json()

print(f"Total API Calls: {stats['total_api_calls']}")
print(f"Error Rate: {stats['error_rate']}%")
print(f"Avg Response Time: {stats['avg_response_time']}ms")
```

### Monitoring Integration

```python
# Prometheus-style metrics
from prometheus_client import Counter, Histogram

api_requests = Counter('api_requests_total', 'Total API requests')
response_time = Histogram('response_time_seconds', 'Response time')

@app.after_request
def track_metrics(response):
    api_requests.inc()
    response_time.observe(g.response_time)
    return response
```

## 🎨 Dashboard Customization

### Custom Charts

Edit `templates/analytics_dashboard.html` to add custom charts:

```html
<div class="chart-section">
    <h2>Custom Metric</h2>
    <canvas id="customChart"></canvas>
</div>

<script>
new Chart(document.getElementById('customChart'), {
    type: 'bar',
    data: {
        labels: {{ custom_labels | tojson }},
        datasets: [{
            label: 'Custom Data',
            data: {{ custom_data | tojson }}
        }]
    }
});
</script>
```

### Styling

Modify the gradient colors in the CSS:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
/* Change to your brand colors */
background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
```

## 🔐 Security Considerations

### Authentication

Add authentication to protect sensitive endpoints:

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not verify_token(auth):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/stats')
@require_auth
def api_stats():
    # Protected endpoint
    pass
```

### Rate Limiting

Implement rate limiting for API endpoints:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/stats')
@limiter.limit("100 per hour")
def api_stats():
    # Rate-limited endpoint
    pass
```

## 📱 API Response Formats

### Success Response
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2025-12-04T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-12-04T10:30:00Z"
}
```

## 🐛 Troubleshooting

### Analytics Not Showing Data

1. Check that requests are being tracked:
```python
print(len(analytics_tracker.api_calls))
```

2. Verify middleware is enabled:
```python
# Should see before_request and after_request decorators
```

3. Clear browser cache and reload dashboard

### High Memory Usage

Reduce history limit:
```python
analytics_tracker.max_history = 500  # Reduce from 1000
```

### Dashboard Not Loading

1. Check template file exists: `templates/analytics_dashboard.html`
2. Verify Chart.js CDN is accessible
3. Check browser console for JavaScript errors

## 📚 Best Practices

1. **Monitor Regularly**: Check dashboard daily for anomalies
2. **Set Alerts**: Configure alerts for high error rates or slow response times
3. **Archive Data**: Periodically export and archive analytics data
4. **Optimize Slow Endpoints**: Use metrics to identify performance bottlenecks
5. **Track Business Metrics**: Add custom metrics for business-specific KPIs

## 🔄 Export Analytics Data

### CSV Export

```python
import csv

@app.route('/api/stats/export')
def export_stats():
    stats = analytics_tracker.api_calls
    # Generate CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['timestamp', 'method', 'path', 'status_code', 'response_time'])
    writer.writeheader()
    writer.writerows(stats)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=analytics.csv'}
    )
```

### JSON Export

```python
@app.route('/api/stats/export.json')
def export_stats_json():
    stats = analytics_tracker.get_stats()
    return jsonify(stats)
```

## 🎯 Next Steps

1. **Integrate with Monitoring Tools**: Connect to Datadog, New Relic, or Grafana
2. **Add More Metrics**: Track custom business metrics
3. **Implement Alerts**: Set up email/Slack alerts for critical events
4. **Create Reports**: Generate weekly/monthly usage reports
5. **A/B Testing**: Use analytics to measure feature adoption

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review logs: `data/logs/`
- Open an issue on GitHub: https://github.com/Rahulcdry07/PDF2JSON

---

**Last Updated**: December 4, 2025
