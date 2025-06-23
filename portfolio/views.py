from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# This view will render the stock reprice calculator page.
# The @login_required decorator ensures that only authenticated users can access this page.
@login_required(login_url='/login/') # Redirects to /login/ if user is not authenticated
def calculator_view(request):
    """
    Renders the stock reprice calculator page.
    Requires user to be logged in.
    """
    return render(request, 'portfolio/stock_calculator.html', {'title': 'Calculator'})
