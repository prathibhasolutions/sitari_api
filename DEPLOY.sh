#!/bin/bash
# Deploy script for AWS Lightsail server

echo "=== Deploying WhatsApp API with Safety Features ==="

# Navigate to project
cd /home/ubuntu/sitari_api

echo "=== Pulling latest code from GitHub ==="
git pull origin main

echo "=== Activating virtual environment ==="
source venv/bin/activate

echo "=== Creating migrations ==="
python manage.py makemigrations

echo "=== Running migrations ==="
python manage.py migrate

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Restarting Gunicorn ==="
sudo systemctl restart gunicorn

echo "=== Checking Gunicorn status ==="
sudo systemctl status gunicorn --no-pager -l

echo "=== Checking recent logs ==="
sudo journalctl -u gunicorn -n 30 --no-pager

echo "=== Deployment complete! ==="
