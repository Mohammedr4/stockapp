# core/tests.py
from django.test import TestCase
from django.urls import reverse

class LandingPageTest(TestCase):
    """
    Test to ensure the landing page functions correctly.
    """
    def test_landing_page_loads_successfully(self):
        """
        Verify that the landing page URL ('/') returns a 200 status code.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_landing_page_uses_correct_template(self):
        """
        Verify that the landing page renders its correct template.
        """
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'core/landing_page.html')b