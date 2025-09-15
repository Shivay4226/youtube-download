# YouTube Video Downloader

A modern web application for downloading YouTube videos with multiple quality options, language support, and audio-only downloads.

## Features

- 🎥 Download videos in multiple qualities (360p, 720p, 1080p, etc.)
- 🎵 Audio-only download options
- 🌍 Multi-language subtitle support
- 📱 Responsive modern UI
- 📁 File management with download history
- ⚡ Fast and reliable downloads using pytube

## Installation

### Option 1: Docker (Recommended for Production)

1. **Build and run with Docker Compose:**
```bash
git clone <repository-url>
cd yt-download
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Copy environment file:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application:**
```bash
python app.py
```

### Production Deployment

#### Option 1: Simple Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build -d

# View logs
docker-compose logs -f
```

#### Option 2: Production with Nginx (Recommended)
```bash
# Set environment variables
export SECRET_KEY="your-secure-secret-key"
export CORS_ORIGINS="https://yourdomain.com"

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up --build -d
```

#### Option 3: Manual Gunicorn Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn --config gunicorn.conf.py app:app
```

## Usage

1. **Enter YouTube URL**: Paste any YouTube video URL in the input field
2. **Get Video Info**: Click the button to fetch video details and available formats
3. **Select Quality**: Choose your preferred video quality or audio format
4. **Add Subtitles**: Optionally include subtitles in your preferred language
5. **Download**: Click the download button to save the file
6. **Access Files**: Downloaded files appear in the downloads section

## API Endpoints

- `POST /api/video-info` - Get video information and available streams
- `POST /api/download` - Download video or audio
- `GET /api/downloads` - List downloaded files
- `GET /api/download-file/<filename>` - Serve downloaded files

## Supported Features

### Video Formats
- MP4 (various resolutions)
- Progressive download streams
- Adaptive streams support

### Audio Formats
- MP4 audio
- WebM audio
- Various bitrates (128kbps, 160kbps, etc.)

### Subtitle Languages
- Automatic detection of available languages
- SRT format download
- Support for channels like MrBeast with multiple language options

## Requirements

- Python 3.7+
- pytube==7.0.16
- Flask
- Flask-CORS

## File Structure

```
yt-download/
├── app.py              # Main Flask application
├── index.html          # Frontend HTML interface
├── requirements.txt    # Python dependencies
├── downloads/          # Downloaded files directory (auto-created)
└── README.md          # This file
```

## Docker Deployment Benefits

- ✅ **Consistent Environment** - Same runtime across all platforms
- ✅ **Easy Scaling** - Deploy to any cloud provider
- ✅ **Dependency Management** - All dependencies included
- ✅ **Production Ready** - Optimized for hosting
- ✅ **Auto Cleanup** - Temporary files handled automatically

## Environment Variables

- `PORT` - Server port (default: 5000)
- `FLASK_ENV` - Environment mode (development/production)

## Production Features

### Security
- ✅ **Rate Limiting** - Prevents API abuse (configurable per endpoint)
- ✅ **Security Headers** - HSTS, XSS protection, content type validation
- ✅ **Non-root Container** - Runs with restricted user permissions
- ✅ **Input Validation** - Sanitized URL and parameter handling
- ✅ **CORS Configuration** - Configurable cross-origin policies

### Performance
- ✅ **Gunicorn WSGI** - Production-grade server with worker processes
- ✅ **Multi-stage Docker** - Optimized image size and build caching
- ✅ **Nginx Reverse Proxy** - Load balancing and SSL termination
- ✅ **Resource Limits** - Memory and CPU constraints
- ✅ **Health Checks** - Automated container health monitoring

### Monitoring
- ✅ **Structured Logging** - JSON logs with request tracking
- ✅ **Error Handling** - Comprehensive exception management
- ✅ **Health Endpoint** - `/health` for monitoring systems
- ✅ **Request Metrics** - Access logs with response times

## Cloud Deployment

### Heroku
```bash
# Login and create app
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set CORS_ORIGINS="https://your-app-name.herokuapp.com"

# Deploy container
heroku container:push web
heroku container:release web
```

### Railway
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy automatically on git push

### DigitalOcean App Platform
1. Create new app from GitHub repository
2. Configure environment variables
3. Set build command: `docker build -t app .`
4. Set run command: `gunicorn --config gunicorn.conf.py app:app`

### AWS ECS/Fargate
```bash
# Build and push to ECR
aws ecr create-repository --repository-name youtube-downloader
docker build -t youtube-downloader .
docker tag youtube-downloader:latest <account-id>.dkr.ecr.<region>.amazonaws.com/youtube-downloader:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/youtube-downloader:latest
```

### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/youtube-downloader
gcloud run deploy --image gcr.io/PROJECT-ID/youtube-downloader --platform managed
```

## Notes

- Files are streamed directly to users (no server storage)
- Temporary files are automatically cleaned up
- The application runs on `http://localhost:5000` by default
- Supports both video and audio-only downloads
- Subtitle files are included when requested

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Environment mode (development/production) |
| `SECRET_KEY` | `dev-secret-key` | Flask secret key (change in production) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `RATE_LIMIT` | `10` | API requests per minute per IP |
| `DOWNLOAD_TIMEOUT` | `300` | Download timeout in seconds |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

## API Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/health` | GET | Health check | None |
| `/api/video-info` | POST | Get video metadata | 5/min |
| `/api/download` | POST | Download video/audio | 3/min |
| `/api/downloads` | GET | List downloaded files | 10/min |
| `/api/downloads/<filename>` | DELETE | Delete specific file | 10/min |
| `/api/downloads/clear` | DELETE | Clear all downloads | 5/min |

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 <PID>
```

**Docker Build Fails:**
```bash
# Clean Docker cache
docker system prune -a
# Rebuild without cache
docker-compose build --no-cache
```

**Rate Limit Errors:**
- Increase `RATE_LIMIT` environment variable
- Wait 1 minute for rate limit reset
- Check if multiple clients are using same IP

**Download Failures:**
- Verify YouTube URL is accessible
- Check if video has geographic restrictions
- Ensure sufficient disk space
- Check network connectivity

**SSL/HTTPS Issues:**
- Update SSL certificates in nginx.conf
- Verify domain DNS configuration
- Check firewall rules for ports 80/443

### Performance Optimization

**For High Traffic:**
```bash
# Increase worker processes in gunicorn.conf.py
workers = multiprocessing.cpu_count() * 4 + 1

# Scale with Docker Compose
docker-compose up --scale youtube-downloader=3
```

**Memory Usage:**
- Monitor with `docker stats`
- Increase memory limits in docker-compose.yml
- Restart workers periodically with `max_requests`

### Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Configure specific `CORS_ORIGINS`
- [ ] Set up SSL certificates
- [ ] Enable firewall rules
- [ ] Monitor access logs
- [ ] Set up log rotation
- [ ] Configure backup strategy
