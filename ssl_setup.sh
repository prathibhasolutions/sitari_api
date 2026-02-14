#!/bin/bash
# SSL Configuration for Django on AWS Lightsail
# Run this AFTER basic deployment is complete and DNS is configured

# ============================================
# Prerequisites:
# 1. Your domain DNS is pointing to your server IP
# 2. Domain propagation is complete (test with: ping yourdomain.com)
# 3. Port 443 is open in AWS Lightsail Firewall
# 4. Basic deployment is working on HTTP
# ============================================

# Replace these with your actual values
YOUR_DOMAIN="whatsapp.sitarisolutions.in"
YOUR_WWW_DOMAIN="www.whatsapp.sitarisolutions.in"
YOUR_IP="13.201.34.38"

echo "============================================"
echo "SSL Setup for Django"
echo "Domain: $YOUR_DOMAIN"
echo "============================================"
echo ""

# ============================================
# STEP 1: Update Django Settings
# ============================================
echo "=== Step 1: Update Django Settings ==="
cd /home/ubuntu/sitari_api
source venv/bin/activate

echo "Opening settings.py for editing..."
echo "Update ALLOWED_HOSTS and add CSRF_TRUSTED_ORIGINS"
echo ""
echo "ALLOWED_HOSTS should include:"
echo "  '$YOUR_IP', '$YOUR_DOMAIN', '$YOUR_WWW_DOMAIN', 'localhost', '127.0.0.1'"
echo ""
echo "Add CSRF_TRUSTED_ORIGINS:"
echo "  CSRF_TRUSTED_ORIGINS = ["
echo "      'http://$YOUR_IP',"
echo "      'http://$YOUR_DOMAIN',"
echo "      'https://$YOUR_DOMAIN',"
echo "      'http://$YOUR_WWW_DOMAIN',"
echo "      'https://$YOUR_WWW_DOMAIN',"
echo "  ]"
echo ""
echo "Press Enter to edit settings.py..."
read

nano myproject/settings.py

# ============================================
# STEP 2: Update Nginx Configuration
# ============================================
echo ""
echo "=== Step 2: Update Nginx Configuration ==="
echo "Opening Nginx config for editing..."
echo ""
echo "Update server_name line to:"
echo "  server_name $YOUR_IP $YOUR_DOMAIN $YOUR_WWW_DOMAIN;"
echo ""
echo "Press Enter to edit Nginx config..."
read

sudo nano /etc/nginx/sites-available/sitari_api

# ============================================
# STEP 3: Restart Services
# ============================================
echo ""
echo "=== Step 3: Restart Services ==="
sudo systemctl restart gunicorn
sudo nginx -t
sudo systemctl restart nginx

echo "Services restarted!"
echo ""

# ============================================
# STEP 4: Test HTTP Access
# ============================================
echo "=== Step 4: Test HTTP Access ==="
echo "Before installing SSL, verify your site works on HTTP:"
echo "  http://$YOUR_DOMAIN"
echo ""
echo "Press Enter when HTTP access is working..."
read

# ============================================
# STEP 5: Install Certbot
# ============================================
echo ""
echo "=== Step 5: Install Certbot ==="
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# ============================================
# STEP 6: Get SSL Certificate
# ============================================
echo ""
echo "=== Step 6: Get SSL Certificate ==="
echo "Running Certbot..."
echo ""
echo "You will be asked:"
echo "  1. Email address (for renewal notifications)"
echo "  2. Agree to Terms of Service (Y)"
echo "  3. Share email with EFF (Y/N - your choice)"
echo "  4. Redirect HTTP to HTTPS? Choose: 2 (Redirect)"
echo ""
echo "Press Enter to continue..."
read

sudo certbot --nginx -d $YOUR_DOMAIN -d $YOUR_WWW_DOMAIN

# ============================================
# STEP 7: Test Auto-Renewal
# ============================================
echo ""
echo "=== Step 7: Test SSL Auto-Renewal ==="
sudo certbot renew --dry-run

echo ""
echo "============================================"
echo "SSL CONFIGURATION COMPLETE!"
echo "============================================"
echo ""
echo "Your site is now available at:"
echo "  https://$YOUR_DOMAIN"
echo "  https://$YOUR_WWW_DOMAIN"
echo ""
echo "HTTP URLs will automatically redirect to HTTPS"
echo ""
echo "SSL certificate will auto-renew before expiration"
echo ""

# ============================================
# STEP 8: Verify HTTPS
# ============================================
echo "=== Testing HTTPS ==="
echo "Opening test in terminal..."
curl -I https://$YOUR_DOMAIN

echo ""
echo "Check if you see 'HTTP/2 200' or 'HTTP/1.1 200' above"
echo ""
echo "============================================"
echo "DEPLOYMENT FULLY COMPLETE! 🎉"
echo "============================================"
