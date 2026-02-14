#!/bin/bash
# Maintenance Commands for Django on AWS Lightsail
# Quick reference for common maintenance tasks

# ============================================
# UPDATE CODE FROM GITHUB
# ============================================
update_from_github() {
    echo "=== Updating from GitHub ==="
    cd /home/ubuntu/sitari_api
    
    # Show current branch
    git branch
    
    # Pull latest changes
    git pull origin main
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install any new dependencies
    pip install -r requirements.txt
    
    # Run migrations
    python manage.py migrate
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    # Restart services
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
    
    echo "Update complete!"
}

# ============================================
# VIEW LOGS
# ============================================
view_gunicorn_logs() {
    echo "=== Gunicorn Logs (last 50 lines) ==="
    sudo journalctl -u gunicorn -n 50
}

view_nginx_error_logs() {
    echo "=== Nginx Error Logs (last 50 lines) ==="
    sudo tail -n 50 /var/log/nginx/error.log
}

view_nginx_access_logs() {
    echo "=== Nginx Access Logs (last 50 lines) ==="
    sudo tail -n 50 /var/log/nginx/access.log
}

follow_gunicorn_logs() {
    echo "=== Following Gunicorn Logs (Ctrl+C to exit) ==="
    sudo journalctl -u gunicorn -f
}

follow_nginx_logs() {
    echo "=== Following Nginx Error Logs (Ctrl+C to exit) ==="
    sudo tail -f /var/log/nginx/error.log
}

# ============================================
# RESTART SERVICES
# ============================================
restart_all() {
    echo "=== Restarting all services ==="
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
    echo "Done!"
}

restart_gunicorn() {
    echo "=== Restarting Gunicorn ==="
    sudo systemctl restart gunicorn
    sudo systemctl status gunicorn
}

restart_nginx() {
    echo "=== Restarting Nginx ==="
    sudo systemctl restart nginx
    sudo systemctl status nginx
}

# ============================================
# CHECK STATUS
# ============================================
check_status() {
    echo "=== Service Status ==="
    echo ""
    echo "--- Gunicorn ---"
    sudo systemctl status gunicorn --no-pager
    echo ""
    echo "--- Nginx ---"
    sudo systemctl status nginx --no-pager
}

# ============================================
# DATABASE OPERATIONS
# ============================================
make_migrations() {
    echo "=== Making migrations ==="
    cd /home/ubuntu/sitari_api
    source venv/bin/activate
    python manage.py makemigrations
    python manage.py migrate
    sudo systemctl restart gunicorn
}

backup_database() {
    echo "=== Backing up database ==="
    cd /home/ubuntu/sitari_api
    BACKUP_FILE="db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp db.sqlite3 "$BACKUP_FILE"
    echo "Database backed up to: $BACKUP_FILE"
}

create_superuser() {
    echo "=== Creating superuser ==="
    cd /home/ubuntu/sitari_api
    source venv/bin/activate
    python manage.py createsuperuser
}

# ============================================
# STATIC FILES
# ============================================
collect_static() {
    echo "=== Collecting static files ==="
    cd /home/ubuntu/sitari_api
    source venv/bin/activate
    python manage.py collectstatic --noinput
    sudo systemctl restart nginx
    echo "Static files collected!"
}

# ============================================
# FIX PERMISSIONS
# ============================================
fix_permissions() {
    echo "=== Fixing permissions ==="
    sudo chmod o+x /home
    sudo chmod o+x /home/ubuntu
    sudo chmod o+x /home/ubuntu/sitari_api
    
    sudo chown -R ubuntu:www-data /home/ubuntu/sitari_api
    
    sudo chmod -R 755 /home/ubuntu/sitari_api/staticfiles
    sudo chmod -R 755 /home/ubuntu/sitari_api/media
    sudo chmod -R 755 /home/ubuntu/sitari_api/static
    
    if [ -e /home/ubuntu/sitari_api/gunicorn.sock ]; then
        sudo chown ubuntu:www-data /home/ubuntu/sitari_api/gunicorn.sock
        sudo chmod 660 /home/ubuntu/sitari_api/gunicorn.sock
    fi
    
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
    
    echo "Permissions fixed!"
}

# ============================================
# SSL CERTIFICATE RENEWAL
# ============================================
renew_ssl() {
    echo "=== Renewing SSL certificate ==="
    sudo certbot renew
    sudo systemctl restart nginx
    echo "SSL certificate renewed!"
}

test_ssl_renewal() {
    echo "=== Testing SSL auto-renewal ==="
    sudo certbot renew --dry-run
}

# ============================================
# SYSTEM UPDATES
# ============================================
update_system() {
    echo "=== Updating system packages ==="
    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y
    echo "System updated!"
}

# ============================================
# DJANGO MANAGEMENT COMMANDS
# ============================================
django_shell() {
    echo "=== Opening Django shell ==="
    cd /home/ubuntu/sitari_api
    source venv/bin/activate
    python manage.py shell
}

django_check() {
    echo "=== Running Django checks ==="
    cd /home/ubuntu/sitari_api
    source venv/bin/activate
    python manage.py check
    python manage.py check --deploy
}

# ============================================
# CLEANUP
# ============================================
cleanup() {
    echo "=== Cleaning up ==="
    
    # Remove old log files
    sudo find /var/log/nginx/ -name "*.gz" -type f -mtime +30 -delete
    
    # Clean apt cache
    sudo apt clean
    sudo apt autoremove -y
    
    # Clean pip cache
    cd /home/ubuntu/sitari_api
    source venv/bin/activate
    pip cache purge
    
    echo "Cleanup complete!"
}

# ============================================
# DISK USAGE
# ============================================
check_disk_usage() {
    echo "=== Disk Usage ==="
    df -h
    echo ""
    echo "=== Project Directory Size ==="
    du -sh /home/ubuntu/sitari_api
    echo ""
    echo "=== Database Size ==="
    du -sh /home/ubuntu/sitari_api/db.sqlite3
    echo ""
    echo "=== Media Files Size ==="
    du -sh /home/ubuntu/sitari_api/media
    echo ""
    echo "=== Static Files Size ==="
    du -sh /home/ubuntu/sitari_api/staticfiles
}

# ============================================
# MENU INTERFACE
# ============================================
show_menu() {
    echo ""
    echo "============================================"
    echo "Django Maintenance Menu - sitari_api"
    echo "============================================"
    echo ""
    echo "Code Updates:"
    echo "  1) Update from GitHub"
    echo "  2) Collect static files"
    echo "  3) Run migrations"
    echo ""
    echo "Service Management:"
    echo "  4) Restart all services"
    echo "  5) Restart Gunicorn"
    echo "  6) Restart Nginx"
    echo "  7) Check service status"
    echo ""
    echo "Logs:"
    echo "  8) View Gunicorn logs"
    echo "  9) View Nginx error logs"
    echo "  10) View Nginx access logs"
    echo "  11) Follow Gunicorn logs (live)"
    echo "  12) Follow Nginx logs (live)"
    echo ""
    echo "Database:"
    echo "  13) Backup database"
    echo "  14) Create superuser"
    echo "  15) Django shell"
    echo ""
    echo "Maintenance:"
    echo "  16) Fix permissions"
    echo "  17) Django checks"
    echo "  18) Renew SSL certificate"
    echo "  19) Test SSL renewal"
    echo "  20) Update system"
    echo "  21) Cleanup"
    echo "  22) Check disk usage"
    echo ""
    echo "  0) Exit"
    echo ""
    echo -n "Enter choice: "
}

# ============================================
# MAIN MENU LOOP
# ============================================
if [ "$1" = "" ]; then
    while true; do
        show_menu
        read choice
        
        case $choice in
            1) update_from_github ;;
            2) collect_static ;;
            3) make_migrations ;;
            4) restart_all ;;
            5) restart_gunicorn ;;
            6) restart_nginx ;;
            7) check_status ;;
            8) view_gunicorn_logs ;;
            9) view_nginx_error_logs ;;
            10) view_nginx_access_logs ;;
            11) follow_gunicorn_logs ;;
            12) follow_nginx_logs ;;
            13) backup_database ;;
            14) create_superuser ;;
            15) django_shell ;;
            16) fix_permissions ;;
            17) django_check ;;
            18) renew_ssl ;;
            19) test_ssl_renewal ;;
            20) update_system ;;
            21) cleanup ;;
            22) check_disk_usage ;;
            0) echo "Goodbye!"; exit 0 ;;
            *) echo "Invalid choice!" ;;
        esac
        
        echo ""
        echo "Press Enter to continue..."
        read
    done
else
    # Allow direct function calls
    # Example: ./maintenance.sh update_from_github
    "$@"
fi

# ============================================
# USAGE EXAMPLES
# ============================================
# Interactive menu:
#   ./maintenance.sh
#
# Direct command:
#   ./maintenance.sh update_from_github
#   ./maintenance.sh restart_all
#   ./maintenance.sh view_gunicorn_logs
#   ./maintenance.sh fix_permissions
#
# Make executable:
#   chmod +x maintenance.sh
# ============================================
