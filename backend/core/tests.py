from unittest.mock import patch
from django.conf import settings
from django.test import SimpleTestCase
from core.auth import check_login
from django.core.management import call_command, CommandError


class DatabaseBoundaryTests(SimpleTestCase):
    def test_sessions_use_sqlite(self):
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')

    def test_application_database_uses_restricted_login(self):
        self.assertEqual(settings.DATABASES['alsj']['USER'], 'alsj_app_login')

    def test_admin_and_builtin_auth_are_not_enabled(self):
        self.assertNotIn('django.contrib.admin', settings.INSTALLED_APPS)
        self.assertNotIn('django.contrib.auth', settings.INSTALLED_APPS)

    def test_migrations_are_blocked_on_postgres(self):
        from core.router import DatabaseRouter
        self.assertFalse(DatabaseRouter().allow_migrate('alsj', 'core'))
        self.assertFalse(DatabaseRouter().allow_migrate('default', 'core'))
        self.assertTrue(DatabaseRouter().allow_migrate('default', 'sessions'))

    def test_postgres_migration_command_refused_before_connecting(self):
        with self.assertRaisesMessage(CommandError, 'only on default SQLite'):
            call_command('migrate', database='alsj', verbosity=0)

    @patch('core.auth.fetch_all')
    def test_login_returns_safe_identity_from_routine(self, fetch):
        fetch.return_value = [{'user_id': 'id', 'full_name': 'Name', 'role_name': 'Client'}]
        self.assertIsNotNone(check_login('0772556213', 'example'))
        sql, params = fetch.call_args.args
        self.assertIn('app_authenticate', sql)
        self.assertNotIn('password_hash', sql)
        self.assertEqual(params, ['0772556213', 'example'])

    @patch('core.auth.fetch_all', return_value=[])
    def test_wrong_password_returns_no_identity(self, fetch):
        self.assertIsNone(check_login('0772556213', 'wrong'))
