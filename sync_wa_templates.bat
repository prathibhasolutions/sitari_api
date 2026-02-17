# Windows Task Scheduler batch file to run Django template sync every 15 minutes
# Save this as sync_wa_templates.bat in your project root

cd /d %~dp0
venv\Scripts\activate
python manage.py sync_wa_templates
