from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as DjangoMigrateCommand


class Command(DjangoMigrateCommand):
    def handle(self, *args, **options):
        # Routers alone do not prevent Django's migration recorder from creating
        # django_migrations. Stop before any database connection or recorder use.
        if options.get('database', 'default') != 'default':
            raise CommandError('Migrations are permitted only on default SQLite, never on alsj.')
        return super().handle(*args, **options)
