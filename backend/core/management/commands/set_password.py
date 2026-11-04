from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Password changes require a separately approved database administrator workflow.'

    def handle(self, *args, **options):
        raise CommandError('Bulk password resets are disabled. Ask the database administrator to change only the intended account.')
