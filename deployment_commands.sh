#!/bin/bash
# AWS Lightsail Django Deployment - Quick Command Reference
# For sitari_api project
# IMPORTANT: Replace YOUR_PUBLIC_IP and YOUR_DOMAIN with actual values before running

# ============================================
# SECTION 1: System Setup
# ============================================
echo "=== Updating system ==="
sudo apt update && sudo apt upgrade -y

echo "=== Installing dependencies ==="
sudo apt install python3-pip python3-dev python3-venv libpq-dev nginx curl git -y

# ============================================
# SECTION 2: Clone and Setup Project
# ============================================
echo "=== Cloning repository ==="
cd ~
git clone https://github.com/prathibhasolutions/sitariservices.git sitari_api
cd sitari_api

echo "=== Creating virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing Python packages ==="
pip install --upgrade pip
pip install -r requirements.txt

# ============================================
# SECTION 3: Django Configuration
# ============================================
echo "=== Now you need to edit settings.py manually ==="
echo "Run: nano myproject/settings.py"
echo ""
echo "Update these settings:"
echo "1. DEBUG = False"
echo "2. ALLOWED_HOSTS = ['13.201.34.38', 'localhost', '127.0.0.1']"
echo "3. Add: CSRF_TRUSTED_ORIGINS = ['http://13.201.34.38', 'http://localhost']"
echo ""
echo "Press Enter when done editing settings.py..."
read

# Open settings file
nano myproject/settings.py

# ============================================
# SECTION 4: Collect Static and Migrate
# ============================================
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Running migrations ==="
python manage.py migrate

echo "=== Creating superuser ==="
python manage.py createsuperuser

# ============================================
# SECTION 5: Test Gunicorn
# ============================================
echo "=== Testing Gunicorn (Press Ctrl+C after testing) ==="
gunicorn --workers 3 --bind 0.0.0.0:8000 myproject.wsgi:application
# After testing, press Ctrl+C

# ============================================
# SECTION 6: Setup Gunicorn Service
# ============================================
echo "=== Creating Gunicorn service ==="
sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=Gunicorn daemon for sitari_api
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/sitari_api
Environment="PATH=/home/ubuntu/sitari_api/venv/bin"
ExecStart=/home/ubuntu/sitari_api/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/home/ubuntu/sitari_api/gunicorn.sock \
    myproject.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

echo "=== Starting Gunicorn service ==="
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn

# ============================================
# SECTION 7: Configure Nginx
# ============================================
echo "=== Creating Nginx configuration ==="
echo "Your IP: 13.201.34.38"
echo "Press Enter to continue..."
read

sudo tee /etc/nginx/sites-available/sitari_api > /dev/null <<'EOF'
server {
    listen 80;
    server_name 13.201.34.38;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias /home/ubuntu/sitari_api/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/sitari_api/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/sitari_api/gunicorn.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
EOF

echo "=== Now edit the Nginx config if needed ==="
sudo nano /etc/nginx/sites-available/sitari_api

echo "=== Enabling site ==="
sudo ln -s /etc/nginx/sites-available/sitari_api /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

echo "=== Testing Nginx configuration ==="
sudo nginx -t

echo "=== Starting Nginx ==="
sudo systemctl restart nginx
sudo systemctl status nginx

# ============================================
# SECTION 8: Fix Permissions
# ============================================
echo "=== Fixing permissions ==="
sudo chmod o+x /home
sudo chmod o+x /home/ubuntu
sudo chmod o+x /home/ubuntu/sitari_api

sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api

sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles
sudo chmod -R 755 /home/ubuntu/sitari_api/media
sudo chmod -R 755 /home/ubuntu/sitari_api/static

sudo chown ubuntu:www-data /home/ubuntu/sitari_api/gunicorn.sock 2>/dev/null || true
sudo chmod 660 /home/ubuntu/sitari_api/gunicorn.sock 2>/dev/null || true

echo "=== Restarting services ==="
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "=== Checking status ==="
sudo systemctl status gunicorn
sudo systemctl status nginx

echo ""
echo "============================================"
echo "DEPLOYMENT COMPLETE!"
echo "============================================"
echo "Visit your site at: http://13.201.34.38"
echo "Admin panel: http://13.201.34.38/admin"
echo ""
echo "Troubleshooting commands:"
echo "  sudo journalctl -u gunicorn -n 50"
echo "  sudo tail -n 50 /var/log/nginx/error.log"
echo ""
