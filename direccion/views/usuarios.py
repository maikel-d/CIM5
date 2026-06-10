# ============================================================
# Gestión de Usuarios
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from ..forms import UserCreateForm, UserEditForm
from .mixins import PermissionRequiredMixin
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms


@permiso_required(perms.USUARIOS_TOGGLE)
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
        return redirect("usuario_list")
    user.is_active = not user.is_active
    user.save()
    estado = "activada" if user.is_active else "desactivada"
    messages.success(request, f"Cuenta de {user.username} {estado} exitosamente.")
    auditar(request, "TOGGLE", "Usuario", user.pk, user.username, f"Cuenta {estado}")
    return redirect("usuario_list")


# ============================================================
# USER MANAGEMENT (Admin only)
# ============================================================

class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = "direccion/usuario_list.html"
    context_object_name = "usuarios"
    login_url = reverse_lazy("login")
    paginate_by = 25
    permisos_requeridos = [perms.USUARIOS_VER]

    def get_queryset(self):
        queryset = User.objects.all().order_by("username")
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset.prefetch_related("profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        for u in context["usuarios"]:
            try:
                u.rol = u.profile.rol
            except Exception:
                u.rol = "SIN PERFIL"
        return context


class UserCreateView(PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "direccion/usuario_form.html"
    login_url = reverse_lazy("login")
    success_url = reverse_lazy("usuario_list")
    permisos_requeridos = [perms.USUARIOS_CREAR]

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "CREAR", "Usuario", self.object.pk, self.object.username, f"Rol: {form.cleaned_data.get('rol', 'N/A')}")
        return resp


class UserUpdateView(PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "direccion/usuario_form.html"
    login_url = reverse_lazy("login")
    success_url = reverse_lazy("usuario_list")
    permisos_requeridos = [perms.USUARIOS_EDITAR]

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "ACTUALIZAR", "Usuario", self.object.pk, self.object.username, f"Rol: {form.cleaned_data.get('rol', 'N/A')}")
        return resp


@permiso_required(perms.USUARIOS_ELIMINAR)
def user_delete(request, pk):
    """Elimina permanentemente un usuario del sistema."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect("usuario_list")
    if user.is_superuser:
        messages.error(request, "No se puede eliminar el superusuario.")
        return redirect("usuario_list")
    if request.method == "POST":
        username = user.username
        pk_val = user.pk
        user.delete()
        messages.success(request, f"Usuario '{username}' eliminado permanentemente.")
        auditar(request, "ELIMINAR", "Usuario", pk_val, username, "Eliminado permanentemente")
        return redirect("usuario_list")
    return render(request, "direccion/usuario_confirm_delete.html", {"usuario": user})


