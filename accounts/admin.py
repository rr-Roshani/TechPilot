from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


# =====================================
# LOGIN
# =====================================

def login_view(request):

    # Already logged-in user ko dashboard par bhejo
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        # Normal email/password login
        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        if not email or not password:

            messages.error(
                request,
                "Please enter your email and password."
            )

            return redirect("login")

        # Django username field mein email store ho raha hai
        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid email or password."
        )

        return redirect("login")

    # Google Client ID template ko bhejna
    return render(
        request,
        "accounts/login.html",
        {
            "google_client_id": settings.GOOGLE_CLIENT_ID
        }
    )


# =====================================
# GOOGLE LOGIN / SIGNUP
# =====================================

def google_login(request):

    if request.method != "POST":

        return redirect("login")

    credential = request.POST.get(
        "credential",
        ""
    )

    if not credential:

        messages.error(
            request,
            "Google sign-in failed. Please try again."
        )

        return redirect("login")

    try:

        # =====================================
        # VERIFY GOOGLE ID TOKEN
        # =====================================

        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        # Google unique user ID
        google_user_id = idinfo.get(
            "sub"
        )

        # Google email
        email = idinfo.get(
            "email",
            ""
        ).strip().lower()

        # Google name
        name = idinfo.get(
            "name",
            ""
        ).strip()

        if not google_user_id or not email:

            messages.error(
                request,
                "Google account information could not be verified."
            )

            return redirect("login")

        # =====================================
        # FIND EXISTING USER
        # =====================================

        user = User.objects.filter(
            username=email
        ).first()

        # =====================================
        # CREATE NEW GOOGLE USER
        # =====================================

        if user is None:

            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=name
            )

            # Google account does not need
            # Django password login
            user.set_unusable_password()

            user.save()

            messages.success(
                request,
                "Welcome to TechPilot! Your account has been created."
            )

        else:

            # =====================================
            # UPDATE USER INFORMATION
            # =====================================

            changed = False

            if not user.email:

                user.email = email

                changed = True

            if not user.first_name and name:

                user.first_name = name

                changed = True

            if changed:

                user.save()

        # =====================================
        # CREATE DJANGO SESSION
        # =====================================

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend"
        )

        # =====================================
        # AFTER GOOGLE LOGIN
        # =====================================

        return redirect("dashboard")

    except ValueError:

        messages.error(
            request,
            "Invalid or expired Google sign-in."
        )

        return redirect("login")

    except Exception:

        messages.error(
            request,
            "Something went wrong with Google sign-in."
        )

        return redirect("login")


# =====================================
# REGISTER
# =====================================

def register_view(request):

    # Already logged-in user
    if request.user.is_authenticated:

        return redirect("dashboard")

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # =====================================
        # NAME VALIDATION
        # =====================================

        if not name:

            messages.error(
                request,
                "Please enter your name."
            )

            return redirect("register")

        # =====================================
        # EMAIL VALIDATION
        # =====================================

        if not email:

            messages.error(
                request,
                "Please enter your email."
            )

            return redirect("register")

        # =====================================
        # PASSWORD VALIDATION
        # =====================================

        if not password:

            messages.error(
                request,
                "Please create a password."
            )

            return redirect("register")

        if len(password) < 8:

            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

            return redirect("register")

        # =====================================
        # CONFIRM PASSWORD
        # =====================================

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("register")

        # =====================================
        # CHECK EXISTING ACCOUNT
        # =====================================

        if User.objects.filter(
            username=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

            return redirect("register")

        # =====================================
        # CREATE DJANGO USER
        # =====================================

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        user.save()

        messages.success(
            request,
            "Account created successfully! Please sign in."
        )

        return redirect("login")

    return render(
        request,
        "accounts/register.html"
    )


# =====================================
# LOGOUT
# =====================================

def logout_view(request):

    logout(request)

    return redirect("login")


# =====================================
# DASHBOARD
# =====================================

@login_required(login_url="login")
def dashboard_view(request):

    return render(
        request,
        "dashboard.html"
    )
    