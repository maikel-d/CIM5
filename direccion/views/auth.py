# ============================================================
# Autenticación
# ============================================================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.views import View

from ..forms import LoginForm


class CustomLoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Bienvenido, {user.get_full_name() or user.username}")
                    return redirect("dashboard")
                else:
                    messages.error(request, "Esta cuenta está desactivada. Contacte al administrador.")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        return render(request, self.template_name, {"form": form})


