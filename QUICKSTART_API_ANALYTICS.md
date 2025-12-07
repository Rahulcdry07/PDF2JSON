# 🚀 Quick Start Guide - API Documentation & Analytics

## Overview

Your EstimateX project now includes comprehensive API documentation and real-time analytics!

## 🎯 What You Get

### 1. Interactive API Documentation
Browse all API endpoints with examples and try them out directly from the browser.

**URL**: `http://localhost:8000/api/docs`

**Features**:
- 📖 All endpoints documented
- 🔍 Search functionality
- 🏷️ Filter by category
- 💡 Request/response examples
- 🔧 cURL command samples

### 2. Real-time Analytics Dashboard
Monitor your API usage, performance, and system health in real-time.

**URL**: `http://localhost:8000/analytics`

**Metrics Displayed**:
- 📊 Total API calls with trends
- 📄 PDF conversions count
- 💰 Cost estimations performed
- ⚡ Average response times
- ✅ Success/error rates
- 🔥 Popular endpoints
- 🕐 Recent activity logs

### 3. Programmatic API Stats
Get statistics programmatically for integration with monitoring tools.

**URL**: `http://localhost:8000/api/stats`

**Returns**: JSON with comprehensive statistics

## 🏃 Quick Start

### Start the Server

```bash
# From project root
python -m src.estimatex.web
```

Or with the web interface script:

```bash
./quickstart.sh
```

### Access the Features

1. **Main Application**: http://localhost:8000
2. **API Documentation**: http://localhost:8000/api/docs
3. **Analytics Dashboard**: http://localhost:8000/analytics
4. **API Stats (JSON)**: http://localhost:8000/api/stats

## 📚 Example Usage

### View API Documentation

1. Open browser to `http://localhost:8000/api/docs`
2. Browse endpoints by category
3. Click any endpoint to see details
4. Use search to find specific endpoints

### Monitor Analytics

1. Open browser to `http://localhost:8000/analytics`
2. View real-time statistics
3. Check charts for usage trends
4. Review recent activity logs
5. Click "Refresh Data" for latest metrics

### Programmatic Access

```python
import requests

# Get current statistics
response = requests.get('http://localhost:8000/api/stats')
stats = response.json()

print(f"Total API Calls: {stats['total_api_calls']}")
print(f"Error Rate: {stats['error_rate']}%")
print(f"Avg Response Time: {stats['avg_response_time']}ms")
```

```bash
# Using cURL
curl http://localhost:8000/api/stats | jq '.'
```

## 🎨 Features Walkthrough

### API Documentation Page

**Categories**:
- 🔧 **System**: Health checks and system information
- 📄 **PDF Conversion**: Upload and convert PDFs
- 💰 **DSR Matching**: Cost estimation endpoints
- 📊 **Excel Operations**: Excel to PDF conversion
- 📈 **Analytics**: Usage statistics

**Search & Filter**:
- Type in search box to find endpoints
- Click category badges to filter
- Click "All" to show all endpoints

**Endpoint Details**:
- HTTP method (GET/POST/PUT/DELETE)
- Request parameters
- Response formats
- Status codes
- Example cURL commands

### Analytics Dashboard

**Summary Cards** (Top Row):
- Total API Calls
- PDF Conversions
- Cost Estimations
- Average Response Time
- Success Rate
- Error Rate

**Charts**:
- **API Calls Over Time**: Line chart showing last 24 hours
- **Endpoint Distribution**: Pie chart of usage by endpoint

**Tables**:
- **Popular Endpoints**: Most used APIs with performance metrics
- **Recent Activity**: Last 20 requests with timestamps

## 📖 Complete Documentation

For detailed information, see:

- **API & Analytics Guide**: `docs/API_ANALYTICS_GUIDE.md`
- **Implementation Summary**: `API_ANALYTICS_SUMMARY.md`
- **Main README**: `README.md`

## 🔧 Configuration

### Adjust History Limit

Default: 1000 requests

```python
# In src/estimatex/web.py
analytics_tracker.max_history = 500  # Keep last 500 requests
```

### Production Setup

For production deployments:

1. **Use Redis for Analytics**:
   ```python
   import redis
   redis_client = redis.Redis(host='localhost', port=6379)
   ```

2. **Add Authentication**:
   ```python
   @app.route('/analytics')
   @require_auth
   def analytics():
       # Protected endpoint
       pass
   ```

3. **Enable Rate Limiting**:
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app)
   ```

See `docs/API_ANALYTICS_GUIDE.md` for detailed production setup.

## 🐛 Troubleshooting

### Analytics Not Showing Data

**Solution**: Make some API requests first, then refresh the dashboard.

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/analytics
```

### Charts Not Displaying

**Check**:
1. Browser console for JavaScript errors
2. Chart.js CDN is accessible
3. Clear browser cache

### Slow Performance

**Solution**: Reduce history limit in `web.py`:

```python
analytics_tracker.max_history = 500
```

## 📊 Understanding Metrics

### Total API Calls
Total number of API requests received since server started.

### PDF Conversions
Count of successful PDF upload and conversion operations.

### Cost Estimations
Number of DSR cost estimation calculations performed.

### Average Response Time
Mean response time across all API requests (in milliseconds).

### Success Rate
Percentage of requests that returned 2xx or 3xx status codes.

### Error Rate
Percentage of requests that returned 4xx or 5xx status codes.

## 🎯 Next Steps

1. **Explore API Docs**: Browse all available endpoints
2. **Monitor Usage**: Check analytics dashboard regularly
3. **Integrate Monitoring**: Connect to external monitoring tools
4. **Customize Dashboard**: Add custom metrics for your needs
5. **Set Up Alerts**: Configure alerts for high error rates

## 💡 Tips

- Bookmark `/api/docs` and `/analytics` for quick access
- Use API docs as reference when building integrations
- Monitor analytics to identify performance bottlenecks
- Export statistics periodically for long-term analysis
- Use the health endpoint for uptime monitoring

## 🆘 Support

Need help?

1. Check `docs/API_ANALYTICS_GUIDE.md` for detailed documentation
2. Review `tests/test_analytics.py` for usage examples
3. Open an issue on GitHub
4. Check application logs in `data/logs/`

---

**Quick Links**:
- 📖 API Docs: http://localhost:8000/api/docs
- 📊 Analytics: http://localhost:8000/analytics
- 📈 Stats JSON: http://localhost:8000/api/stats
- 🏠 Main App: http://localhost:8000

**Happy Monitoring! 🎉**
