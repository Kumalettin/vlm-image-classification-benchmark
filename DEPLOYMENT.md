# Deployment Guide

Bu dokümantasyon, Multimodal Image Classifier uygulamasının production ortamına deploy edilmesi için detaylı adımları içerir.

## İçindekiler

- [Gereksinimler](#gereksinimler)
- [Hazırlık](#hazırlık)
- [Linux/Ubuntu Deployment](#linuxubuntu-deployment)
- [Windows Server Deployment](#windows-server-deployment)
- [Docker Deployment](#docker-deployment)
- [Nginx Konfigürasyonu](#nginx-konfigürasyonu)
- [SSL/HTTPS Kurulumu](#sslhttps-kurulumu)
- [Monitoring ve Logging](#monitoring-ve-logging)
- [Güvenlik](#güvenlik)
- [Bakım ve Güncellemeler](#bakım-ve-güncellemeler)

## Gereksinimler

### Minimum Sistem Gereksinimleri

- **CPU**: 4 core
- **RAM**: 16GB (büyük modeller için 32GB önerilir)
- **Disk**: 50GB SSD
- **İşletim Sistemi**: Ubuntu 20.04+, Windows Server 2019+, CentOS 8+
- **Network**: Statik IP veya domain adı

### Yazılım Gereksinimleri

- Python 3.8+
- pip
- virtualenv veya venv
- Git
- Nginx (web server için)
- Supervisor veya systemd (process management için)

## Hazırlık

### 1. Sunucu Hazırlığı

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor
```

**CentOS/RHEL:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx supervisor
```

### 2. Kullanıcı Oluşturma

Güvenlik için ayrı bir kullanıcı oluşturun:

```bash
sudo adduser --system --group --home /opt/multimodal-classifier multimodal
sudo usermod -aG www-data multimodal
```

### 3. Projeyi Klonlama

```bash
sudo -u multimodal git clone <repository-url> /opt/multimodal-classifier
cd /opt/multimodal-classifier
```

### 4. Environment Variables

```bash
sudo -u multimodal cp .env.example .env
sudo -u multimodal nano .env
```

`.env` dosyasını düzenleyin:
```bash
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
```

## Linux/Ubuntu Deployment

### 1. Virtual Environment Kurulumu

```bash
cd /opt/multimodal-classifier
sudo -u multimodal python3 -m venv venv
sudo -u multimodal venv/bin/pip install --upgrade pip
sudo -u multimodal venv/bin/pip install -r requirements.txt
sudo -u multimodal venv/bin/pip install gunicorn
```

### 2. Dizin İzinlerini Ayarlama

```bash
sudo chown -R multimodal:www-data /opt/multimodal-classifier
sudo chmod -R 755 /opt/multimodal-classifier
sudo chmod -R 775 /opt/multimodal-classifier/data
```

### 3. Systemd Service Oluşturma

`/etc/systemd/system/multimodal-classifier.service` dosyası oluşturun:

```ini
[Unit]
Description=Multimodal Image Classifier
After=network.target

[Service]
Type=notify
User=multimodal
Group=www-data
WorkingDirectory=/opt/multimodal-classifier
Environment="PATH=/opt/multimodal-classifier/venv/bin"
EnvironmentFile=/opt/multimodal-classifier/.env
ExecStart=/opt/multimodal-classifier/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 300 \
    --access-logfile /opt/multimodal-classifier/logs/access.log \
    --error-logfile /opt/multimodal-classifier/logs/error.log \
    --log-level info \
    backend.app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Service'i Başlatma

```bash
sudo systemctl daemon-reload
sudo systemctl enable multimodal-classifier
sudo systemctl start multimodal-classifier
sudo systemctl status multimodal-classifier
```

### 5. Logları Kontrol Etme

```bash
sudo journalctl -u multimodal-classifier -f
```

## Windows Server Deployment

### 1. Python ve Bağımlılıkları Kurma

1. Python 3.8+ indirin ve kurun: https://www.python.org/downloads/
2. Git indirin ve kurun: https://git-scm.com/download/win

### 2. Projeyi Klonlama

```powershell
cd C:\
git clone <repository-url> C:\multimodal-classifier
cd C:\multimodal-classifier
```

### 3. Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install waitress
```

### 4. Environment Variables

`.env` dosyası oluşturun ve düzenleyin.

### 5. Windows Service Oluşturma

NSSM (Non-Sucking Service Manager) kullanın:

1. NSSM indirin: https://nssm.cc/download
2. Service oluşturun:

```powershell
nssm install MultimodalClassifier "C:\multimodal-classifier\venv\Scripts\python.exe"
nssm set MultimodalClassifier AppParameters "C:\multimodal-classifier\venv\Scripts\waitress-serve.exe --host=0.0.0.0 --port=5000 backend.app:app"
nssm set MultimodalClassifier AppDirectory "C:\multimodal-classifier"
nssm set MultimodalClassifier DisplayName "Multimodal Image Classifier"
nssm set MultimodalClassifier Description "Multimodal Image Classification Service"
nssm set MultimodalClassifier Start SERVICE_AUTO_START
nssm start MultimodalClassifier
```

### 6. Service'i Kontrol Etme

```powershell
nssm status MultimodalClassifier
```

## Docker Deployment

### 1. Dockerfile

Proje kök dizininde `Dockerfile` oluşturun:

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/models data/predictions data/results data/temp logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/models')"

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "300", "backend.app:app"]
```

### 2. docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: multimodal-classifier
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - HOST=0.0.0.0
      - PORT=5000
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LOG_LEVEL=INFO
    env_file:
      - .env
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: multimodal-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend:/usr/share/nginx/html:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### 3. Docker Build ve Run

```bash
# Build image
docker build -t multimodal-classifier .

# Run container
docker run -d \
  --name multimodal-classifier \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  multimodal-classifier

# Or use docker-compose
docker-compose up -d
```

### 4. Docker Komutları

```bash
# Logları görüntüleme
docker logs -f multimodal-classifier

# Container'a bağlanma
docker exec -it multimodal-classifier bash

# Container'ı yeniden başlatma
docker restart multimodal-classifier

# Container'ı durdurma
docker stop multimodal-classifier

# Container'ı silme
docker rm multimodal-classifier
```

## Nginx Konfigürasyonu

### 1. Nginx Config Dosyası

`/etc/nginx/sites-available/multimodal-classifier` dosyası oluşturun:

```nginx
upstream backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        root /opt/multimodal-classifier/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        root /opt/multimodal-classifier/frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Logs
    access_log /var/log/nginx/multimodal-classifier-access.log;
    error_log /var/log/nginx/multimodal-classifier-error.log;

    # Max upload size
    client_max_body_size 100M;
}
```

### 2. Nginx'i Aktifleştirme

```bash
sudo ln -s /etc/nginx/sites-available/multimodal-classifier /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/HTTPS Kurulumu

### Let's Encrypt ile Ücretsiz SSL

```bash
# Certbot kurulumu
sudo apt install -y certbot python3-certbot-nginx

# SSL sertifikası alma
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

Certbot otomatik olarak nginx konfigürasyonunu güncelleyecektir.

## Monitoring ve Logging

### 1. Log Dosyaları

```bash
# Application logs
tail -f /opt/multimodal-classifier/logs/app.log
tail -f /opt/multimodal-classifier/logs/error.log

# Nginx logs
tail -f /var/log/nginx/multimodal-classifier-access.log
tail -f /var/log/nginx/multimodal-classifier-error.log

# System logs
sudo journalctl -u multimodal-classifier -f
```

### 2. Log Rotation

`/etc/logrotate.d/multimodal-classifier` dosyası oluşturun:

```
/opt/multimodal-classifier/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 multimodal www-data
    sharedscripts
    postrotate
        systemctl reload multimodal-classifier > /dev/null 2>&1 || true
    endscript
}
```

### 3. Monitoring Tools (Opsiyonel)

**Prometheus + Grafana:**
```bash
# Prometheus exporter ekleyin
pip install prometheus-flask-exporter
```

**Sentry (Error Tracking):**
```bash
pip install sentry-sdk[flask]
```

`.env` dosyasına ekleyin:
```
SENTRY_DSN=https://your-sentry-dsn
```

## Güvenlik

### 1. Firewall Konfigürasyonu

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 2. Fail2Ban Kurulumu

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

`/etc/fail2ban/jail.local` dosyası oluşturun:

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/multimodal-classifier-error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/multimodal-classifier-error.log
```

### 3. Güvenlik Kontrol Listesi

- ✅ HTTPS kullanın
- ✅ Güçlü SECRET_KEY kullanın
- ✅ Firewall aktif olsun
- ✅ Düzenli güvenlik güncellemeleri yapın
- ✅ SSH key-based authentication kullanın
- ✅ Root login'i devre dışı bırakın
- ✅ Rate limiting aktif olsun
- ✅ CORS ayarlarını doğru yapılandırın
- ✅ Log monitoring sistemi kurun
- ✅ Backup stratejisi oluşturun

## Bakım ve Güncellemeler

### 1. Uygulama Güncelleme

```bash
cd /opt/multimodal-classifier
sudo -u multimodal git pull
sudo -u multimodal venv/bin/pip install -r requirements.txt
sudo systemctl restart multimodal-classifier
```

### 2. Backup

```bash
# Veri yedekleme
tar -czf backup-$(date +%Y%m%d).tar.gz /opt/multimodal-classifier/data

# Database backup (gelecekte)
# pg_dump dbname > backup-$(date +%Y%m%d).sql
```

### 3. Sistem Güncellemeleri

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### 4. Health Check Script

`/opt/multimodal-classifier/healthcheck.sh`:

```bash
#!/bin/bash

# Check if service is running
if ! systemctl is-active --quiet multimodal-classifier; then
    echo "Service is not running!"
    systemctl restart multimodal-classifier
    exit 1
fi

# Check if API responds
if ! curl -f http://localhost:5000/api/models > /dev/null 2>&1; then
    echo "API is not responding!"
    systemctl restart multimodal-classifier
    exit 1
fi

echo "Health check passed"
exit 0
```

Cron job ekleyin:
```bash
*/5 * * * * /opt/multimodal-classifier/healthcheck.sh >> /var/log/healthcheck.log 2>&1
```

## Performans Optimizasyonu

### 1. Gunicorn Workers

Worker sayısını CPU core sayısına göre ayarlayın:
```
workers = (2 * CPU_CORES) + 1
```

### 2. Nginx Caching

Nginx konfigürasyonuna ekleyin:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/models {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_pass http://backend;
}
```

### 3. Database Connection Pooling (gelecekte)

SQLAlchemy pool ayarları:
```python
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
```

## Sorun Giderme

### Service Başlamıyor

```bash
# Logları kontrol edin
sudo journalctl -u multimodal-classifier -n 50

# Konfigürasyonu test edin
sudo -u multimodal /opt/multimodal-classifier/venv/bin/python backend/app.py
```

### Nginx Hatası

```bash
# Konfigürasyonu test edin
sudo nginx -t

# Logları kontrol edin
sudo tail -f /var/log/nginx/error.log
```

### Bellek Problemi

```bash
# Bellek kullanımını kontrol edin
free -h
htop

# Worker sayısını azaltın
# /etc/systemd/system/multimodal-classifier.service dosyasında --workers değerini düşürün
```

## Destek

Deployment ile ilgili sorularınız için:
- GitHub Issues
- Dokümantasyon: README.md

---

**Son Güncelleme**: 2025-11-13
