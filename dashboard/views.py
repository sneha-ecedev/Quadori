from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    full_name = request.user.get_full_name().strip() or request.user.username
    return render(request, 'dashboard/home.html', {'full_name': full_name})
