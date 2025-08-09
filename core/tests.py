# stock_savvy_project/core/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

# A test suite to check the core application's views and templates.
class CoreViewsTest(TestCase):
    """
    Test suite for the core application's views and URL configurations.
    """

    def setUp(self):
        """
        Set up a test client and a test user for authenticated tests.
        We'll use a test user to ensure the navbar's authenticated links work.
        """
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword123')

    def test_landing_page_url_exists_at_correct_location(self):
        """
        Test to ensure the landing page URL ('/') returns a 200 status code.
        This verifies the main URL is correctly mapped to a view.
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_landing_page_uses_correct_template(self):
        """
        Test to ensure the landing page renders the 'core/landing_page.html' template.
        It also checks if the template correctly extends 'base.html'.
        """
        response = self.client.get(reverse('home')) # Use 'home' as the URL name
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/landing_page.html')
        self.assertTemplateUsed(response, 'base.html') # This is crucial to check our fix!

    def test_signup_prompt_url_exists_at_correct_location(self):
        """
        Test to ensure the signup prompt URL returns a 200 status code.
        This confirms the path and view for this page are working.
        """
        response = self.client.get('/core/signup-prompt/')
        self.assertEqual(response.status_code, 200)

    def test_signup_prompt_uses_correct_template(self):
        """
        Test to ensure the signup prompt renders its specific template.
        It also checks if this template correctly extends 'base.html'.
        """
        # Use the namespaced URL 'core:signup_prompt'
        response = self.client.get(reverse('core:signup_prompt'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/signup_prompt.html')
        self.assertTemplateUsed(response, 'base.html') # Check that it also uses the base template.

    def test_authenticated_navbar_links_dont_cause_errors(self):
        """
        Test that the navbar links, especially the ones for authenticated users,
        resolve correctly without causing a NoReverseMatch error.
        We'll log in a test user to simulate an authenticated session.
        """
        # Log in the test user
        self.client.login(username='testuser', password='testpassword123')
        
        # Test the 'Calculators' link
        response = self.client.get(reverse('calculators:calculators_index'))
        self.assertEqual(response.status_code, 200)
        
        # Test the 'My Portfolio' link
        response = self.client.get(reverse('portfolio:portfolio_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test the 'Logout' link
        response = self.client.get(reverse('accounts:logout'))
        # A logout view typically redirects, so we check for a 302 status code
        self.assertEqual(response.status_code, 302)
        
    def test_unauthenticated_navbar_links_dont_cause_errors(self):
        """
        Test that the navbar links for unauthenticated users resolve correctly.
        """
        # Test the 'Login' link
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        
        # Test the 'Sign Up Free' link
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

