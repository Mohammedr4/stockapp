from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def stock_calculator(request):
    return render(request, 'portfolio/stock_calculator.html')

def index(request):
    # If logged in, redirect to calculator
    if request.user.is_authenticated:
        return redirect('stock_calculator')
    # If not logged in, show login page (or landing page)
    return redirect('login')  # or render a landing page if you want

def register(request):
    # Just render your register template
    return render(request, 'user/register.html')

def login(request):
    # Just render your login template (ideally handled by auth views)
    return render(request, 'portfolio/login.html')

def logout_view(request):
    logout(request)
    return redirect('index')  # redirect to homepage or wherever you want