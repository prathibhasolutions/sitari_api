import threading
import time
from django.core.management import call_command
from django.apps import AppConfig

class WhatsAppAutoSyncConfig(AppConfig):
    name = 'whatsapp'

    def ready(self):
        from django.conf import settings
        if getattr(settings, 'RUN_MAIN', True):  # Only run in main process
            def sync_loop():
                while True:
                    try:
                        call_command('sync_wa_templates')
                    except Exception as e:
                        print(f"[WA Template Sync Error] {e}")
                    time.sleep(60)  # 1 minute (for testing)
            t = threading.Thread(target=sync_loop, daemon=True)
            t.start()
