# 🧭 Django on AWS Lightsail - Complete Deployment Guide
## For sitari_api Project

---

## ✅ Pre-Deployment Checklist
- [ ] GitHub repository is up to date
- [ ] requirements.txt is complete
- [ ] You have AWS account access
- [ ] You have your domain DNS access (if using custom domain)

---

## 📋 Part 1: AWS Lightsail Instance Setup

### 1.1 Create Instance
1. Go to https://lightsail.aws.amazon.com
2. Click **Create Instance**
3. Select:
   - **Platform**: Linux/Unix
   - **Blueprint**: Ubuntu 22.04 LTS (or latest)
   - **Instance Plan**: $5/month (1 GB RAM, 1 vCPU)
4. Name your instance: `sitari-api-server`
5. Click **Create Instance**
6. **Wait 2-3 minutes** for instance to start

### 1.2 Configure Networking (CRITICAL)
1. Click on your instance name
2. Go to **Networking** tab
3. Scroll to **Firewall** section
4. Add these rules (click "Add another" for each):

   | Application | Protocol | Port | Source |
   |-------------|----------|------|--------|
   | SSH         | TCP      | 22   | Anywhere |
   | HTTP        | TCP      | 80   | Anywhere |
   | HTTPS       | TCP      | 443  | Anywhere |
   | Custom      | TCP      | 8000 | Anywhere |

5. Click **Save** after adding each rule

**Note**: When you select "Anywhere" as the source, AWS Lightsail automatically applies the rule to both IPv4 and IPv6. You don't need to create separate rules for each protocol.

### 1.3 Note Your Public IP
- Your **Public IP address**: `13.201.34.38`
- You'll use this IP throughout the deployment

---

## 📋 Part 2: Server Configuration

### 2.1 Connect to Server
Click the **terminal icon** (orange) in your Lightsail instance dashboard to open SSH in browser.

### 2.2 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Install Dependencies
```bash
sudo apt install python3-pip python3-dev python3-venv libpq-dev nginx curl git -y
```

---

## 📋 Part 3: Deploy Your Django Application

### 3.1 Clone Repository
```bash
cd ~
git clone https://github.com/prathibhasolutions/sitariservices.git sitari_api
cd sitari_api
```

**Note**: We're cloning to `sitari_api` directory to match your project name.

### 3.2 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 Install Python Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Configure Django Settings
```bash
nano myproject/settings.py
```

**Find and update these settings:**

1. **Set DEBUG to False:**
```python
DEBUG = False
```

2. **Update ALLOWED_HOSTS** (use your IP):
```python
ALLOWED_HOSTS = ['13.201.34.38', 'localhost', '127.0.0.1']
```

3. **Verify STATIC settings** (should already be there):
```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
```

4. **Add CSRF_TRUSTED_ORIGINS** (use your IP):
```python
CSRF_TRUSTED_ORIGINS = [
    'http://13.201.34.38',
    'http://localhost',
]
```

**Save and exit**: Press `Ctrl+X`, then `Y`, then `Enter`

### 3.5 Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 3.6 Run Migrations
```bash
python manage.py migrate
```

### 3.7 Create Superuser
```bash
python manage.py createsuperuser
```
Enter username, email, and password when prompted.

### 3.8 Test Gunicorn
```bash
gunicorn --workers 3 --bind 0.0.0.0:8000 myproject.wsgi:application
```

**Test in browser**: Visit `http://13.201.34.38:8000`

If it works, press `Ctrl+C` to stop Gunicorn.

---

## 📋 Part 4: Configure Gunicorn as System Service

### 4.1 Create Gunicorn Service File
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**Paste this content:**
```ini
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
```

**Save and exit**: `Ctrl+X`, `Y`, `Enter`

### 4.2 Start and Enable Gunicorn
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

**Expected output**: Should show "active (running)" in green.

If there are errors:
```bash
sudo journalctl -u gunicorn -n 50
```

---

## 📋 Part 5: Configure Nginx

### 5.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/sitari_api
```

**Paste this content:**
```nginx
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
```

**Save and exit**: `Ctrl+X`, `Y`, `Enter`

### 5.2 Enable the Site
```bash
sudo ln -s /etc/nginx/sites-available/sitari_api /etc/nginx/sites-enabled/
```

### 5.3 Test Nginx Configuration
```bash
sudo nginx -t
```

**Expected output**: "syntax is ok" and "test is successful"

### 5.4 Remove Default Nginx Site (Optional but Recommended)
```bash
sudo rm /etc/nginx/sites-enabled/default
```

### 5.5 Restart Nginx
```bash
sudo systemctl restart nginx
sudo systemctl status nginx
```

---

## 📋 Part 6: Fix Permissions

### 6.1 Set Correct Permissions
```bash
# Allow execute access on parent folders
sudo chmod o+x /home
sudo chmod o+x /home/ubuntu
sudo chmod o+x /home/ubuntu/sitari_api

# Set ownership for the project
sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api

# Set permissions for static and media folders
sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles
sudo chmod -R 755 /home/ubuntu/sitari_api/media
sudo chmod -R 755 /home/ubuntu/sitari_api/static

# If gunicorn.sock exists, set its permissions
sudo chown ubuntu:www-data /home/ubuntu/sitari_api/gunicorn.sock 2>/dev/null || true
sudo chmod 660 /home/ubuntu/sitari_api/gunicorn.sock 2>/dev/null || true
```

### 6.2 Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 6.3 Check Status
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## 📋 Part 7: Verify Deployment

### 7.1 Check if Site is Accessible
Visit in your browser: `http://13.201.34.38`

### 7.2 Check Admin Panel
Visit: `http://13.201.34.38/admin`
Login with superuser credentials you created.

### 7.3 Troubleshooting Commands
If something doesn't work:

```bash
# Check Gunicorn logs
sudo journalctl -u gunicorn -n 50

# Check Nginx error logs
sudo tail -n 50 /var/log/nginx/error.log

# Check Nginx access logs
sudo tail -n 50 /var/log/nginx/access.log

# Check if Gunicorn socket exists
ls -l /home/ubuntu/sitari_api/gunicorn.sock

# Restart everything
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 📋 Part 8: Domain Configuration (Optional)

### 8.1 Add Domain to GoDaddy/Your DNS Provider

Add **A Record**:
- **Type**: A
- **Name**: whatsapp (or api, or @)
- **Value**: 13.201.34.38
- **TTL**: Default

Example domains:
- `whatsapp.sitarisolutions.in` → 13.201.34.38
- `api.sitarisolutions.in` → 13.201.34.38

**Wait 5-30 minutes for DNS propagation.**

### 8.2 Update Django Settings
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
nano myproject/settings.py
```

**Update ALLOWED_HOSTS:**
```python
ALLOWED_HOSTS = [
    '13.201.34.38',
    'whatsapp.sitarisolutions.in',
    'www.whatsapp.sitarisolutions.in',
    'localhost',
    '127.0.0.1'
]
```

**Update CSRF_TRUSTED_ORIGINS:**
```python
CSRF_TRUSTED_ORIGINS = [
    'http://13.201.34.38',
    'http://whatsapp.sitarisolutions.in',
    'https://whatsapp.sitarisolutions.in',
    'http://www.whatsapp.sitarisolutions.in',
    'https://www.whatsapp.sitarisolutions.in',
]
```

**Save and exit**: `Ctrl+X`, `Y`, `Enter`

### 8.3 Update Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/sitari_api
```

**Update server_name line:**
```nginx
server_name 13.201.34.38 whatsapp.sitarisolutions.in www.whatsapp.sitarisolutions.in;
```

**Save and exit**: `Ctrl+X`, `Y`, `Enter`

### 8.4 Restart Services
```bash
sudo systemctl restart gunicorn
sudo nginx -t
sudo systemctl restart nginx
```

### 8.5 Test Domain
Visit: `http://whatsapp.sitarisolutions.in`

---

## 📋 Part 9: SSL Certificate (HTTPS)

### 9.1 Make Sure Port 443 is Open
Verify in AWS Lightsail Firewall (already done in Part 1.2).

### 9.2 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 9.3 Get SSL Certificate
```bash
sudo certbot --nginx -d whatsapp.sitarisolutions.in -d www.whatsapp.sitarisolutions.in
```

**Follow prompts:**
1. Enter email address
2. Agree to Terms of Service (Y)
3. Share email with EFF (Y/N - your choice)
4. Choose redirect option: **2** (Redirect HTTP to HTTPS)

### 9.4 Test Auto-Renewal
```bash
sudo certbot renew --dry-run
```

**Expected output**: "Congratulations, all simulated renewals succeeded"

### 9.5 Verify HTTPS
Visit: `https://whatsapp.sitarisolutions.in`

Your site should now have a padlock icon! 🔒

---

## 📋 Part 10: Maintenance Commands

### Update Code from GitHub
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### View Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Check Service Status
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## 🎯 Quick Reference

**Your Django app should be accessible at:**
- IP: `http://13.201.34.38`
- Domain: `http://whatsapp.sitarisolutions.in` (after DNS setup)
- HTTPS: `https://whatsapp.sitarisolutions.in` (after SSL setup)
- Admin: `https://whatsapp.sitarisolutions.in/admin`

**Important File Paths:**
- Project root: `/home/ubuntu/sitari_api`
- Virtual environment: `/home/ubuntu/sitari_api/venv`
- Settings: `/home/ubuntu/sitari_api/myproject/settings.py`
- Gunicorn service: `/etc/systemd/system/gunicorn.service`
- Nginx config: `/etc/nginx/sites-available/sitari_api`
- Gunicorn socket: `/home/ubuntu/sitari_api/gunicorn.sock`

---

## ❓ Common Issues

### Issue: ERR_CONNECTION_TIMED_OUT
**Solution**: Check AWS Lightsail firewall - ports 80, 443, 8000 must be open.

### Issue: 502 Bad Gateway
**Solution**: 
```bash
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -n 50
```
Check if Gunicorn socket exists and has correct permissions.

### Issue: Static files not loading
**Solution**:
```bash
python manage.py collectstatic --noinput
sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles
sudo systemctl restart nginx
```

### Issue: Permission denied errors
**Solution**: Run Part 6 (Fix Permissions) again.

---

## ✅ Deployment Complete!

Your Django application is now running on AWS Lightsail with:
- ✅ Gunicorn as application server
- ✅ Nginx as reverse proxy
- ✅ Static files serving
- ✅ Media files serving
- ✅ Custom domain (optional)
- ✅ SSL certificate (optional)
- ✅ Auto-renewal for SSL

**Estimated total time: 30-45 minutes**

---

**Created for sitari_api project**  
**Last updated: {{ date }}**
