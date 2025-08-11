from django.test import TestCase
from django.urls import reverse

class LandingPageTest(TestCase):
    """
    Tests to ensure the landing page functions correctly.
    """
    def test_landing_page_uses_correct_template(self):
        """
        Verify that the landing page view renders using the 'core/landing_page.html'
        template, which should correctly extend 'base.html'.
        """
        # The 'home' URL name is now the correct one for the landing page.
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/landing_page.html')
        self.assertTemplateUsed(response, 'base.html')