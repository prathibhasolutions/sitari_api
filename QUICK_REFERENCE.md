# 🚀 Quick Reference Card - Django on AWS Lightsail

## Essential Info
- **Server**: AWS Lightsail Ubuntu
- **IP Address**: 13.201.34.38
- **Project**: sitari_api
- **Location**: /home/ubuntu/sitari_api
- **WSGI**: myproject.wsgi:application

---

## Daily Commands

### Update Code
```bash
cd /home/ubuntu/sitari_api && git pull && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && sudo systemctl restart gunicorn nginx
```

### Restart Everything
```bash
sudo systemctl restart gunicorn nginx
```

### View Logs
```bash
# Last 50 Gunicorn logs
sudo journalctl -u gunicorn -n 50

# Last 50 Nginx errors
sudo tail -n 50 /var/log/nginx/error.log

# Follow Gunicorn logs live
sudo journalctl -u gunicorn -f
```

### Check Status
```bash
sudo systemctl status gunicorn nginx
```

---

## Fix Common Issues

### 502 Bad Gateway
```bash
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

### Static Files Not Loading
```bash
cd /home/ubuntu/sitari_api && source venv/bin/activate && python manage.py collectstatic --noinput && sudo systemctl restart nginx
```

### Permission Errors
```bash
sudo chmod o+x /home /home/ubuntu /home/ubuntu/sitari_api && sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api && sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles && sudo systemctl restart gunicorn nginx
```

---

## File Locations

| File | Location |
|------|----------|
| Gunicorn Service | /etc/systemd/system/gunicorn.service |
| Nginx Config | /etc/nginx/sites-available/sitari_api |
| Django Settings | /home/ubuntu/sitari_api/myproject/settings.py |
| Gunicorn Socket | /home/ubuntu/sitari_api/gunicorn.sock |
| Database | /home/ubuntu/sitari_api/db.sqlite3 |

---

## Firewall Ports (AWS Lightsail)

| Port | Purpose |
|------|---------|
| 22   | SSH |
| 80   | HTTP |
| 443  | HTTPS |
| 8000 | Testing (optional) |

---

## Settings.py Essentials

```python
DEBUG = False

ALLOWED_HOSTS = ['13.201.34.38', 'your-domain.com']

CSRF_TRUSTED_ORIGINS = [
    'http://13.201.34.38',
    'https://your-domain.com',
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

---

## SSL Certificate

### Install
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Renew
```bash
sudo certbot renew
```

### Test Renewal
```bash
sudo certbot renew --dry-run
```

---

## Emergency Commands

### Complete Restart
```bash
sudo systemctl stop gunicorn nginx && sudo chmod o+x /home /home/ubuntu /home/ubuntu/sitari_api && sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api && sudo systemctl start gunicorn nginx
```

### Check Everything
```bash
sudo systemctl status gunicorn && sudo systemctl status nginx && ls -l /home/ubuntu/sitari_api/gunicorn.sock && sudo tail -n 20 /var/log/nginx/error.log
```

---

## Maintenance Script

```bash
# Make executable (first time)
chmod +x maintenance.sh

# Interactive menu
./maintenance.sh

# Direct commands
./maintenance.sh update_from_github
./maintenance.sh restart_all
./maintenance.sh fix_permissions
```

---

## Database

### Backup
```bash
cp /home/ubuntu/sitari_api/db.sqlite3 /home/ubuntu/sitari_api/db_backup_$(date +%Y%m%d).sqlite3
```

### Migrate
```bash
cd /home/ubuntu/sitari_api && source venv/bin/activate && python manage.py migrate
```

### Create Superuser
```bash
cd /home/ubuntu/sitari_api && source venv/bin/activate && python manage.py createsuperuser
```

---

## URLs to Check

- Site: http://13.201.34.38 or https://your-domain.com
- Admin: https://your-domain.com/admin
- API: Check your urls.py for endpoints

---

## Troubleshooting Checklist

- [ ] Firewall ports open? (22, 80, 443)
- [ ] Services running? `sudo systemctl status gunicorn nginx`
- [ ] Socket exists? `ls -l /home/ubuntu/sitari_api/gunicorn.sock`
- [ ] Permissions correct? Run fix_permissions
- [ ] Logs show errors? Check Gunicorn and Nginx logs
- [ ] DNS propagated? `ping your-domain.com`
- [ ] ALLOWED_HOSTS updated?
- [ ] Static files collected?

---

## Help

Full docs: See DEPLOYMENT_README.md, AWS_LIGHTSAIL_DEPLOYMENT.md, TROUBLESHOOTING.md
