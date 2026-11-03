from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from core.auth import hash_password


class Command(BaseCommand):
    help = 'Give a user a new bcrypt password (by phone number), or give EVERY user the same one (--all). Development only.'

    def add_arguments(self, parser):
        parser.add_argument('password')
        parser.add_argument('phone', nargs='?')
        parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        if len(options['password']) < 8:
            raise CommandError('Use a password of at least 8 characters.')
        if not options['all'] and not options['phone']:
            raise CommandError('Give a phone number, or use --all.')
        hashed = hash_password(options['password'])
        with connection.cursor() as cur:
            if options['all']:
                cur.execute('UPDATE users SET password_hash = %s', [hashed])
            else:
                cur.execute('UPDATE users SET password_hash = %s WHERE phone = %s', [hashed, options['phone']])
            changed = cur.rowcount
        self.stdout.write(self.style.SUCCESS('Password updated for %d user(s).' % changed))
