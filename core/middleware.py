import sys


class AutoMigrateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.migrated = False

    def __call__(self, request):
        if not self.migrated and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            from django.core.management import call_command
            call_command('migrate', '--noinput', verbosity=0)
            self.migrated = True
        return self.get_response(request)
