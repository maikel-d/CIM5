# ============================================================
# Autenticacion
# ============================================================

import secrets

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.views import View
from django.core.cache import cache

from ..forms import LoginForm
from ..ratelimit import (
    check_ip_rate_limit,
    check_username_rate_limit,
    record_failed_attempt,
    clear_rate_limits,
    MAX_USERNAME_ATTEMPTS,
)


class CustomLoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        contexto = {"form": form}

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # 1. Verificar rate limit por IP primero
            ip_block = check_ip_rate_limit(request)
            if ip_block:
                messages.error(request, ip_block["mensaje"])
                contexto["bloqueado"] = True
                return render(request, self.template_name, contexto)

            # 2. Verificar rate limit por username
            user_block = check_username_rate_limit(username)
            if user_block:
                messages.error(request, user_block["mensaje"])
                contexto["bloqueado"] = True
                return render(request, self.template_name, contexto)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    # Limpiar intentos fallidos al iniciar sesion correctamente
                    clear_rate_limits(username)
                    login(request, user)
                    # Generar token de sesion unica (invalida otras sesiones)
                    token = secrets.token_hex(16)
                    request.session['session_token'] = token
                    request.session.save()
                    cache.set(f'auth_token_{user.pk}', token, 86400)
                    messages.success(
                        request,
                        f"Bienvenido, {user.get_full_name() or user.username}",
                    )
                    return redirect("dashboard")
                else:
                    messages.error(
                        request, "Esta cuenta esta desactivada. Contacte al administrador."
                    )
            else:
                # Registrar intento fallido (IP + username)
                intentos, restantes = record_failed_attempt(request, username)
                if restantes > 0:
                    messages.error(
                        request,
                        f"Usuario o contrasena incorrectos. Le queda{"n" if restantes > 1 else ""} {restantes} intento{"s" if restantes > 1 else ""}.",
                    )
                else:
                    messages.error(
                        request, "Demasiados intentos fallidos. Espere unos minutos antes de intentar de nuevo."
                    )
                    contexto["bloqueado"] = True
        return render(request, self.template_name, contexto)
