# ============================================================
# Autenticación
# ============================================================

import secrets

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.cache import cache
from django.views import View

from ..forms import LoginForm


MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_SECONDS = 60


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

            # Verificar bloqueo por intentos fallidos
            cache_key = f"login_failures_{username}"
            intentos = cache.get(cache_key, 0)

            if intentos >= MAX_LOGIN_ATTEMPTS:
                messages.error(
                    request,
                    f"Demasiados intentos fallidos. Espere {LOCKOUT_SECONDS} segundos antes de intentar de nuevo.",
                )
                contexto["bloqueado"] = True
                return render(request, self.template_name, contexto)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    # Limpiar intentos fallidos al iniciar sesión correctamente
                    cache.delete(cache_key)
                    login(request, user)
                    # Generar token de sesión única (invalida otras sesiones)
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
                        request, "Esta cuenta está desactivada. Contacte al administrador."
                    )
            else:
                # Incrementar contador de intentos fallidos
                intentos += 1
                cache.set(cache_key, intentos, LOCKOUT_SECONDS)
                restantes = MAX_LOGIN_ATTEMPTS - intentos
                if restantes > 0:
                    messages.error(
                        request,
                        f"Usuario o contraseña incorrectos. Le queda{'n' if restantes > 1 else ''} {restantes} intento{'s' if restantes > 1 else ''}.",
                    )
                else:
                    messages.error(
                        request,
                        f"Demasiados intentos fallidos. Espere {LOCKOUT_SECONDS} segundos antes de intentar de nuevo.",
                    )
                    contexto["bloqueado"] = True
        return render(request, self.template_name, contexto)


