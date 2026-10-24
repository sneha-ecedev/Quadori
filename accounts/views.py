from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, RegistrationForm, UpdateProfileForm
from .models import Profile


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Your account has been created. You can now log in.',
            )
            return redirect('accounts:login')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    next_page = '/dashboard/'

    def form_valid(self, form):
        messages.success(self.request, 'You have logged in successfully.')
        return super().form_valid(form)


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('accounts:login')

    def post(self, request, *args, **kwargs):
        messages.info(request, 'You have logged out.')
        return super().post(request, *args, **kwargs)


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(
        request,
        'accounts/profile.html',
        {'profile': profile},
    )


@login_required
def edit_profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = UpdateProfileForm(instance=request.user)

    return render(
        request,
        'accounts/edit_profile.html',
        {'form': form, 'profile': profile},
    )
