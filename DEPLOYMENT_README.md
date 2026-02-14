# Django Deployment Guide - AWS Lightsail

Complete deployment guide for **sitari_api** Django project on AWS Lightsail.

## 📁 Deployment Files

This repository includes comprehensive deployment documentation:

| File | Description |
|------|-------------|
| **[AWS_LIGHTSAIL_DEPLOYMENT.md](AWS_LIGHTSAIL_DEPLOYMENT.md)** | Complete step-by-step deployment guide (READ THIS FIRST) |
| **[deployment_commands.sh](deployment_commands.sh)** | Shell script with all deployment commands |
| **[ssl_setup.sh](ssl_setup.sh)** | SSL certificate setup script |
| **[maintenance.sh](maintenance.sh)** | Interactive maintenance menu + commands |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and solutions |

## 🚀 Quick Start

### For New Deployment:

1. **Read the main guide**: [AWS_LIGHTSAIL_DEPLOYMENT.md](AWS_LIGHTSAIL_DEPLOYMENT.md)
2. Follow steps 1-7 to get your site running on HTTP
3. Configure your domain (step 8)
4. Add SSL certificate (step 9)

### For Existing Deployment:

Use the maintenance script for common tasks:

```bash
# Make executable (first time only)
chmod +x maintenance.sh

# Run interactive menu
./maintenance.sh

# Or run specific commands
./maintenance.sh update_from_github
./maintenance.sh restart_all
./maintenance.sh view_gunicorn_logs
```

## 📊 Project Information

- **Project Name**: sitari_api
- **Django Project Folder**: myproject
- **WSGI Module**: myproject.wsgi:application
- **Apps**: whatsapp, dashboard
- **Database**: SQLite (db.sqlite3)

## 🔗 Important Paths (on server)

```
/home/ubuntu/sitari_api/                    # Project root
/home/ubuntu/sitari_api/venv/               # Virtual environment
/home/ubuntu/sitari_api/myproject/          # Django project folder
/home/ubuntu/sitari_api/myproject/settings.py  # Settings file
/home/ubuntu/sitari_api/gunicorn.sock       # Gunicorn socket
/etc/systemd/system/gunicorn.service        # Gunicorn service
/etc/nginx/sites-available/sitari_api       # Nginx config
```

## ⚙️ Key Configuration Files

### Gunicorn Service
**Location**: `/etc/systemd/system/gunicorn.service`

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

### Nginx Configuration
**Location**: `/etc/nginx/sites-available/sitari_api`

```nginx
server {
    listen 80;
    server_name 13.201.34.38 your-domain.com;

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

## 🔧 Common Commands

### Update Code from GitHub
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

### Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### View Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -n 50

# Nginx error logs
sudo tail -n 50 /var/log/nginx/error.log

# Follow logs in real-time
sudo journalctl -u gunicorn -f
```

### Check Status
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

## 🌐 AWS Lightsail Firewall Rules

Ensure these ports are open in your instance's networking settings:

| Application | Protocol | Port | Source |
|-------------|----------|------|--------|
| SSH | TCP | 22 | Anywhere |
| HTTP | TCP | 80 | Anywhere |
| HTTPS | TCP | 443 | Anywhere |
| Custom (testing) | TCP | 8000 | Anywhere |

## 🔐 Required Settings.py Updates

Before deployment, update `myproject/settings.py`:

```python
# Set to False in production
DEBUG = False

# Add your IP and domain
ALLOWED_HOSTS = ['13.201.34.38', 'your-domain.com', 'www.your-domain.com']

# Add CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'http://13.201.34.38',
    'http://your-domain.com',
    'https://your-domain.com',
]

# Static files (already configured)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Media files (already configured)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
```

## 📝 Deployment Checklist

- [ ] AWS Lightsail instance created ($5/month plan)
- [ ] Firewall rules configured (ports 22, 80, 443, 8000)
- [ ] System updated and dependencies installed
- [ ] Repository cloned to `/home/ubuntu/sitari_api`
- [ ] Virtual environment created
- [ ] Python packages installed
- [ ] settings.py updated (DEBUG=False, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS)
- [ ] Static files collected
- [ ] Database migrated
- [ ] Superuser created
- [ ] Gunicorn service configured and running
- [ ] Nginx configured and running
- [ ] Permissions fixed
- [ ] Site accessible via HTTP at http://13.201.34.38
- [ ] Domain DNS configured (optional)
- [ ] Domain added to settings.py and Nginx (optional)
- [ ] SSL certificate installed (optional)
- [ ] HTTPS working (optional)

## 🆘 Troubleshooting

Having issues? Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for solutions to common problems:

- ERR_CONNECTION_TIMED_OUT
- 502 Bad Gateway
- Static files not loading
- 403 Forbidden
- CSRF verification failed
- Domain not working
- SSL certificate issues
- And more...

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Certbot](https://certbot.eff.org/)
- [AWS Lightsail Documentation](https://lightsail.aws.amazon.com/ls/docs/)

## 💡 Tips

1. **Always backup your database** before making changes
2. **Test locally first** before deploying
3. **Use Git** for version control
4. **Check logs** when something goes wrong
5. **Set up monitoring** for production
6. **Enable auto-renewactual for SSL** (Certbot does this by default)
7. **Update system packages regularly**

## 🎯 Post-Deployment

After successful deployment:

1. **Test all functionality**
   - Homepage loads
   - Admin panel works
   - Static files load
   - Media uploads work
   - Forms submit correctly

2. **Monitor logs** for the first few days
   ```bash
   sudo journalctl -u gunicorn -f
   ```

3. **Set up regular backups**
   ```bash
   # Add to crontab
   0 2 * * * cp /home/ubuntu/sitari_api/db.sqlite3 /home/ubuntu/backups/db_$(date +\%Y\%m\%d).sqlite3
   ```

4. **Monitor disk usage**
   ```bash
   df -h
   du -sh /home/ubuntu/sitari_api
   ```

## 📞 Support

If you encounter issues not covered in the troubleshooting guide:

1. Check service logs
2. Verify configuration files
3. Review recent changes
4. Check file permissions
5. Consult Django/Nginx/Gunicorn documentation

---

**Project**: sitari_api  
**Framework**: Django 5.2.8  
**Server**: AWS Lightsail  
**Last Updated**: February 14, 2026

---

## Quick Command Reference

```bash
# SSH to server
ssh ubuntu@13.201.34.38

# Activate virtual environment
cd /home/ubuntu/sitari_api && source venv/bin/activate

# Update application
./maintenance.sh update_from_github

# View logs
sudo journalctl -u gunicorn -n 50

# Restart services
sudo systemctl restart gunicorn nginx

# Fix permissions
./maintenance.sh fix_permissions

# Run Django commands
python manage.py [command]
```

**Happy Deploying! 🚀**
