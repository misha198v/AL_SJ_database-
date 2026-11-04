from django.test import SimpleTestCase, RequestFactory, override_settings


class PremiumInterfaceTests(SimpleTestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_public_welcome_is_available_without_signing_in(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Every journey')
        self.assertContains(response, '/login/')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_login_has_shared_assets_and_accessible_password_control(self):
        response = self.client.get('/login/')
        self.assertContains(response, 'core/app.css')
        self.assertContains(response, 'Show password')
        self.assertContains(response, 'novalidate')
        self.assertContains(response, 'autocomplete="current-password"')

    def test_pagination_preserves_filter_state(self):
        from core.ui import paginate
        request = RequestFactory().get('/applications/?q=Amina&status=ACTIVE&page=2')
        result = paginate(request, list(range(25)))
        self.assertEqual(list(result['page']), list(range(10,20)))
        self.assertIn('q=Amina', result['next_url'])
        self.assertIn('status=ACTIVE', result['next_url'])
        self.assertIn('page=3', result['next_url'])

    def test_invalid_page_is_clamped(self):
        from core.ui import paginate
        request = RequestFactory().get('/applications/?page=999')
        result = paginate(request, [1,2])
        self.assertEqual(result['page'].number, 1)

    def test_format_duration_keeps_completed_zero_duration(self):
        from datetime import timedelta
        from core.templatetags.ui import duration
        self.assertEqual(duration(timedelta()), '0h 00m')
        self.assertEqual(duration(timedelta(hours=25,minutes=5)), '25h 05m')
        self.assertEqual(duration(None), 'In progress')
