# 🔧 Troubleshooting Guide - Django on AWS Lightsail

## Quick Diagnostics

### Check All Services Status
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### View Recent Logs
```bash
# Gunicorn logs (last 50 lines)
sudo journalctl -u gunicorn -n 50

# Nginx error logs
sudo tail -n 50 /var/log/nginx/error.log

# Nginx access logs
sudo tail -n 50 /var/log/nginx/access.log
```

### Live Log Monitoring
```bash
# Watch Gunicorn logs in real-time
sudo journalctl -u gunicorn -f

# Watch Nginx error logs in real-time
sudo tail -f /var/log/nginx/error.log

# Watch Nginx access logs in real-time
sudo tail -f /var/log/nginx/access.log
```

---

## Common Issues & Solutions

### ❌ Issue 1: ERR_CONNECTION_TIMED_OUT

**Symptoms:**
- Browser shows "This site can't be reached"
- Connection times out

**Causes:**
- Firewall blocking ports

**Solutions:**

1. **Check AWS Lightsail Firewall:**
   - Go to AWS Lightsail Console
   - Click your instance → Networking tab
   - Verify these ports are open:
     - Port 22 (SSH)
     - Port 80 (HTTP)
     - Port 443 (HTTPS)
     - Port 8000 (for testing)

2. **Check UFW (if enabled):**
```bash
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 'Nginx Full'
```

---

### ❌ Issue 2: 502 Bad Gateway

**Symptoms:**
- Nginx shows "502 Bad Gateway" error

**Causes:**
- Gunicorn not running
- Gunicorn socket doesn't exist
- Permission issues

**Solutions:**

1. **Check if Gunicorn is running:**
```bash
sudo systemctl status gunicorn
```

2. **If Gunicorn is inactive, check logs:**
```bash
sudo journalctl -u gunicorn -n 100
```

3. **Check if socket exists:**
```bash
ls -l /home/ubuntu/sitari_api/gunicorn.sock
```

4. **Restart Gunicorn:**
```bash
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

5. **Fix permissions:**
```bash
sudo chmod o+x /home
sudo chmod o+x /home/ubuntu
sudo chmod o+x /home/ubuntu/sitari_api
sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api
sudo chmod 660 /home/ubuntu/sitari_api/gunicorn.sock
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

6. **Test Gunicorn manually:**
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application
```
Press Ctrl+C to stop, then restart the service.

---

### ❌ Issue 3: Static Files Not Loading (CSS/JS missing)

**Symptoms:**
- Website loads but looks broken
- No styling, images missing
- 404 errors for `/static/` files

**Causes:**
- Static files not collected
- Wrong permissions
- Wrong Nginx configuration

**Solutions:**

1. **Collect static files:**
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
python manage.py collectstatic --noinput
```

2. **Check if staticfiles directory exists:**
```bash
ls -la /home/ubuntu/sitari_api/staticfiles/
```

3. **Fix permissions:**
```bash
sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles
sudo chmod -R 755 /home/ubuntu/sitari_api/static
sudo chmod o+x /home/ubuntu/sitari_api
```

4. **Verify Nginx configuration:**
```bash
sudo nano /etc/nginx/sites-available/sitari_api
```
Make sure you have:
```nginx
location /static/ {
    alias /home/ubuntu/sitari_api/staticfiles/;
}
```

5. **Restart Nginx:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

6. **Check Nginx error logs:**
```bash
sudo tail -n 50 /var/log/nginx/error.log
```

---

### ❌ Issue 4: 403 Forbidden Error

**Symptoms:**
- "403 Forbidden" error when accessing site

**Causes:**
- Permission issues on folders

**Solutions:**

1. **Fix directory permissions:**
```bash
sudo chmod o+x /home
sudo chmod o+x /home/ubuntu
sudo chmod o+x /home/ubuntu/sitari_api
```

2. **Check Nginx error logs:**
```bash
sudo tail -n 50 /var/log/nginx/error.log
```

3. **Verify folder ownership:**
```bash
ls -la /home/ubuntu/
ls -la /home/ubuntu/sitari_api/
```

4. **Reset ownership:**
```bash
sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api
```

---

### ❌ Issue 5: CSRF Verification Failed

**Symptoms:**
- Forms show "CSRF verification failed"
- POST requests fail

**Causes:**
- Missing CSRF_TRUSTED_ORIGINS in settings

**Solutions:**

1. **Update settings.py:**
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
nano myproject/settings.py
```

2. **Add CSRF_TRUSTED_ORIGINS:**
```python
CSRF_TRUSTED_ORIGINS = [
    'http://13.201.34.38',
    'https://YOUR_DOMAIN',
    'http://YOUR_DOMAIN',
]
```

3. **Restart Gunicorn:**
```bash
sudo systemctl restart gunicorn
```

---

### ❌ Issue 6: Site Works on IP but Not on Domain

**Symptoms:**
- `http://13.201.34.38` works
- `http://yourdomain.com` doesn't work

**Causes:**
- DNS not propagated
- Domain not in ALLOWED_HOSTS
- Domain not in Nginx server_name

**Solutions:**

1. **Check DNS propagation:**
```bash
ping yourdomain.com
nslookup yourdomain.com
```

2. **Update Django settings:**
```bash
nano myproject/settings.py
```
Add domain to ALLOWED_HOSTS:
```python
ALLOWED_HOSTS = ['13.201.34.38', 'yourdomain.com', 'www.yourdomain.com']
```

3. **Update Nginx configuration:**
```bash
sudo nano /etc/nginx/sites-available/sitari_api
```
Update server_name:
```nginx
server_name 13.201.34.38 yourdomain.com www.yourdomain.com;
```

4. **Restart services:**
```bash
sudo systemctl restart gunicorn
sudo nginx -t
sudo systemctl restart nginx
```

---

### ❌ Issue 7: SSL Certificate Installation Failed

**Symptoms:**
- Certbot fails to get certificate
- "Failed authorization" errors

**Causes:**
- DNS not pointing to server
- Port 443 not open
- Domain not accessible on HTTP

**Solutions:**

1. **Verify DNS is correct:**
```bash
ping yourdomain.com
```
Should show your server's IP.

2. **Check port 443 is open:**
   - AWS Lightsail → Networking → Firewall
   - Ensure port 443/TCP is allowed

3. **Test HTTP first:**
```bash
curl -I http://yourdomain.com
```
Should return 200 OK.

4. **Try Certbot again:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

### ❌ Issue 8: Updates from GitHub Not Reflecting

**Symptoms:**
- Pushed code to GitHub
- Server still shows old code

**Causes:**
- Forgot to pull changes
- Forgot to restart services
- Forgot to collect static files

**Solutions:**

1. **Complete update process:**
```bash
cd /home/ubuntu/sitari_api
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

2. **Clear browser cache** or use Incognito mode

---

### ❌ Issue 9: Server Restarted, Site No Longer Works

**Symptoms:**
- After server reboot, site is down

**Causes:**
- Services not enabled to auto-start

**Solutions:**

1. **Enable auto-start:**
```bash
sudo systemctl enable gunicorn
sudo systemctl enable nginx
```

2. **Start services manually:**
```bash
sudo systemctl start gunicorn
sudo systemctl start nginx
```

3. **Check status:**
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## Diagnostic Commands Cheat Sheet

```bash
# Service Status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Restart Services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View Logs
sudo journalctl -u gunicorn -n 50        # Gunicorn logs
sudo tail -n 50 /var/log/nginx/error.log # Nginx errors
sudo tail -n 50 /var/log/nginx/access.log # Nginx access

# Live Logs
sudo journalctl -u gunicorn -f           # Follow Gunicorn logs
sudo tail -f /var/log/nginx/error.log    # Follow Nginx errors

# Test Configurations
sudo nginx -t                            # Test Nginx config
python manage.py check                   # Check Django project

# Permission Fixes
sudo chmod o+x /home /home/ubuntu /home/ubuntu/sitari_api
sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api
sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles

# Check Socket
ls -l /home/ubuntu/sitari_api/gunicorn.sock

# DNS Check
ping yourdomain.com
nslookup yourdomain.com

# Test HTTP Response
curl -I http://yourdomain.com
curl -I https://yourdomain.com
```

---

## Need More Help?

### Get Detailed Error Information

1. **Check all logs:**
```bash
# Full Gunicorn log
sudo journalctl -u gunicorn --no-pager -n 200

# All Nginx errors
sudo cat /var/log/nginx/error.log
```

2. **Check Django errors:**
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
python manage.py check --deploy
```

3. **Test Gunicorn directly:**
```bash
cd /home/ubuntu/sitari_api
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application
```

### Emergency Reset

If nothing works, try a complete restart:

```bash
# Stop everything
sudo systemctl stop gunicorn
sudo systemctl stop nginx

# Fix all permissions
sudo chmod o+x /home /home/ubuntu /home/ubuntu/sitari_api
sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api
sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles
sudo chmod -R 755 /home/ubuntu/sitari_api/media

# Collect static files
cd /home/ubuntu/sitari_api
source venv/bin/activate
python manage.py collectstatic --noinput

# Start everything
sudo systemctl start gunicorn
sudo systemctl start nginx

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

**Last Updated: 2026-02-14**
