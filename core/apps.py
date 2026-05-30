import logging
import sys

from django.apps import AppConfig
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals  # noqa

        # Auto-migrate on startup so the app always has the correct schema
        _frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        if _frozen:
            try:
                from django.core.management import call_command
                call_command('migrate', '--noinput', verbosity=0)
            except OperationalError:
                logger.warning('Migration skipped — database may be locked')
