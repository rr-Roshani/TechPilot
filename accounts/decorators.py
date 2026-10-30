from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import StudentProfile


def onboarding_required(view_func):
    @wraps(view_func)
    @login_required(login_url="login")
    def wrapped_view(request, *args, **kwargs):
        profile, _ = StudentProfile.objects.get_or_create(
            user=request.user
        )

        if not profile.onboarding_completed:
            messages.warning(
                request,
                "Please complete your onboarding profile before accessing this page.",
            )
            return redirect("onboarding")

        return view_func(request, *args, **kwargs)

    return wrapped_view
