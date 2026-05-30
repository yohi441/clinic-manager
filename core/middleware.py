import sys
import traceback


class AutoMigrateMiddleware:
    def __init__(self, get_response):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            try:
                from django.core.management import call_command
                print('[migrate] Running migrations...', flush=True)
                call_command('migrate', '--noinput', verbosity=1)
                print('[migrate] Done.', flush=True)
            except Exception:
                print('[migrate] FAILED:')
                traceback.print_exc()
                print(flush=True)
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
