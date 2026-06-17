from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
from .models import (
    UserProfile, Personal, DocumentoPersonal,
    Caso, Investigado, DocumentoInvestigado, DocumentoDireccion,
    DocumentoCaso, Tarea, TicketSoporte, InformeDiario,
    Bien, DocumentoBien, CarpetaBien, DocumentoCarpetaBien,
    CarpetaDireccion
)


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _validar_tamano_archivo(archivo, max_size=MAX_FILE_SIZE):
    """Valida que un archivo no supere el tamaño máximo permitido."""
    if archivo and archivo.size > max_size:
        mb = max_size / (1024 * 1024)
        raise ValidationError(f"El archivo no puede superar los {mb:.0f}MB. Tamaño actual: {archivo.size / (1024 * 1024):.1f}MB")
    return archivo


class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre", max_length=30,
        widget=forms.TextInput(attrs={"class": "form-input"})
    )
    last_name = forms.CharField(
        label="Apellido", max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input"})
    )
    rol = forms.ChoiceField(
        choices=UserProfile.ROL_CHOICES, label="Rol",
        widget=forms.Select(attrs={"class": "form-input"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-input"})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = ""
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                rol=self.cleaned_data["rol"]
            )
        return user


class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre", max_length=30,
        widget=forms.TextInput(attrs={"class": "form-input"})
    )
    last_name = forms.CharField(
        label="Apellido", max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input"})
    )
    rol = forms.ChoiceField(
        choices=UserProfile.ROL_CHOICES, label="Rol",
        widget=forms.Select(attrs={"class": "form-input"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-input"})
        if self.instance and hasattr(self.instance, "profile"):
            self.fields["rol"].initial = self.instance.profile.rol

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, "profile"):
                user.profile.rol = self.cleaned_data["rol"]
                user.profile.save()
        return user


class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = [
            "foto", "apellidos", "nombres", "cedula", "grado",
            "fecha_nacimiento", "direccion", "telefonos",
            "fecha_ingreso", "correo", "contacto_emergencia"
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "fecha_ingreso": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "telefonos": forms.Textarea(attrs={"rows": 2, "class": "form-input", "placeholder": "Ej: 0412-1234567, 0212-7654321"}),
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-input", "placeholder": "Dirección de domicilio"}),
            "contacto_emergencia": forms.Textarea(attrs={"rows": 2, "class": "form-input", "placeholder": "Nombre, parentesco y teléfono"}),
            "correo": forms.EmailInput(attrs={"class": "form-input", "placeholder": "ejemplo@dominio.com"}),
            "grado": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej: Inspector, Sub-Comisario, T.S.U...."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not hasattr(field.widget.attrs, "get") or not field.widget.attrs.get("class"):
                field.widget.attrs.update({"class": "form-input"})

    def clean_foto(self):
        return _validar_tamano_archivo(self.cleaned_data.get("foto"))

    def clean_correo(self):
        correo = self.cleaned_data.get("correo")
        if correo:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
                raise forms.ValidationError("Ingrese un correo electronico valido (ejemplo@dominio.com)")
        return correo


class DocumentoPersonalForm(forms.ModelForm):
    class Meta:
        model = DocumentoPersonal
        fields = ["archivo", "descripcion"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Descripción opcional"}),
        }

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class CasoForm(forms.ModelForm):
    class Meta:
        model = Caso
        fields = ["nombre", "descripcion", "fecha_apertura"]
        widgets = {
            "fecha_apertura": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "descripcion": forms.Textarea(
                attrs={"rows": 3, "class": "form-input", "placeholder": "Descripción del caso..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not hasattr(field.widget.attrs, "get") or not field.widget.attrs.get("class"):
                field.widget.attrs.update({"class": "form-input"})


class InvestigadoForm(forms.ModelForm):
    class Meta:
        model = Investigado
        fields = [
            "caso", "foto", "apellidos", "nombres", "entrada_investigacion",
            "cedula", "rif", "partida_nacimiento"
        ]
        widgets = {
            "caso": forms.Select(attrs={"class": "form-input"}),
            "entrada_investigacion": forms.Textarea(
                attrs={"rows": 4, "class": "form-input", "placeholder": "Breve resumen del caso..."}
            ),
            "partida_nacimiento": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Tomo, folio o datos de acta"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not hasattr(field.widget.attrs, "get") or not field.widget.attrs.get("class"):
                field.widget.attrs.update({"class": "form-input"})

    def clean_foto(self):
        return _validar_tamano_archivo(self.cleaned_data.get("foto"))

    def clean_correo(self):
        correo = self.cleaned_data.get("correo")
        if correo:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
                raise forms.ValidationError("Ingrese un correo electronico valido (ejemplo@dominio.com)")
        return correo


class DocumentoInvestigadoForm(forms.ModelForm):
    class Meta:
        model = DocumentoInvestigado
        fields = ["archivo", "descripcion"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Descripción opcional"}),
        }

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class DocumentoDireccionForm(forms.ModelForm):
    class Meta:
        model = DocumentoDireccion
        fields = ["archivo", "descripcion", "categoria"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Descripción opcional"}),
            "categoria": forms.Select(attrs={"class": "form-input"}),
        }

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class DocumentoCasoForm(forms.ModelForm):
    class Meta:
        model = DocumentoCaso
        fields = ["archivo", "descripcion"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Descripción opcional"}),
        }

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ["descripcion", "prioridad"]
        widgets = {
            "descripcion": forms.Textarea(attrs={
                "rows": 2, "class": "form-input",
                "placeholder": "Escribe una tarea pendiente..."
            }),
            "prioridad": forms.Select(attrs={"class": "form-input"}),
        }


class TicketSoporteForm(forms.ModelForm):
    class Meta:
        model = TicketSoporte
        fields = ["asunto", "descripcion", "prioridad"]
        widgets = {
            "asunto": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Resumen del problema"
            }),
            "descripcion": forms.Textarea(attrs={
                "rows": 4, "class": "form-input",
                "placeholder": "Describe el problema en detalle..."
            }),
            "prioridad": forms.Select(attrs={"class": "form-input"}),
        }


class TicketAsignarForm(forms.ModelForm):
    """Formulario para administradores: asignar ticket, cambiar estado y prioridad."""
    class Meta:
        model = TicketSoporte
        fields = ["estado", "prioridad", "asignado_a"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-input"}),
            "prioridad": forms.Select(attrs={"class": "form-input"}),
            "asignado_a": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asignado_a"].queryset = User.objects.filter(is_active=True).order_by("username")
        self.fields["asignado_a"].required = False
        self.fields["asignado_a"].label = "Asignar a"
        self.fields["asignado_a"].empty_label = "--- Sin asignar ---"


class InformeDiarioForm(forms.ModelForm):
    class Meta:
        model = InformeDiario
        fields = ["titulo", "contenido", "archivo", "fecha"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-input", "placeholder": "Título del informe"}),
            "contenido": forms.Textarea(attrs={
                "rows": 8, "class": "form-input",
                "placeholder": "Breve descripción del informe (opcional)"
            }),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "archivo": forms.FileInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenido'].required = False
        self.fields['contenido'].label = 'Descripción'

    def clean_contenido(self):
        """Si no hay descripción, guarda un valor por defecto para evitar error de modelo blank=False."""
        return self.cleaned_data.get('contenido') or 'Sin descripción'

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class CarpetaForm(forms.ModelForm):
    class Meta:
        model = CarpetaBien
        fields = ["nombre"]
        widgets = {"nombre": forms.TextInput(attrs={"class": "form-input", "placeholder": "Nombre de la carpeta"})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].label = "Nombre"
        for field in self.fields.values():
            if not hasattr(field.widget.attrs, "get") or not field.widget.attrs.get("class"):
                field.widget.attrs.update({"class": "form-input"})


class BienForm(forms.ModelForm):
    class Meta:
        model = Bien
        fields = [
            "caso", "nombre", "descripcion", "foto", "categoria",
            "codigo_inventario", "serial", "marca", "modelo_bien",
            "ubicacion", "estado", "fecha_adquisicion", "valor"
        ]
        widgets = {
            "caso": forms.Select(attrs={"class": "form-input"}),
            "descripcion": forms.Textarea(attrs={
                "rows": 3, "class": "form-input",
                "placeholder": "Descripción del bien (opcional)"
            }),
            "fecha_adquisicion": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "categoria": forms.Select(attrs={"class": "form-input"}),
            "estado": forms.Select(attrs={"class": "form-input"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False
        self.fields['descripcion'].label = 'Descripción'
        for field in self.fields.values():
            if not hasattr(field.widget.attrs, "get") or not field.widget.attrs.get("class"):
                field.widget.attrs.update({"class": "form-input"})

    def clean_foto(self):
        return _validar_tamano_archivo(self.cleaned_data.get("foto"))

    def clean_correo(self):
        correo = self.cleaned_data.get("correo")
        if correo:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
                raise forms.ValidationError("Ingrese un correo electronico valido (ejemplo@dominio.com)")
        return correo


class CarpetaBienDocumentForm(forms.ModelForm):
    class Meta:
        model = DocumentoCarpetaBien
        fields = ["archivo", "descripcion"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Descripción opcional"}),
        }

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class CarpetaDireccionForm(forms.ModelForm):
    class Meta:
        model = CarpetaDireccion
        fields = ["nombre", "categoria"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Nombre de la carpeta"
            }),
            "categoria": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = False
        self.fields["categoria"].empty_label = "--- Sin categoría ---"
        self.fields["nombre"].label = "Nombre de la carpeta"


class DocumentoBienForm(forms.ModelForm):
    class Meta:
        model = DocumentoBien
        fields = ["archivo", "descripcion"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Descripción opcional"}),
        }

    def clean_archivo(self):
        return _validar_tamano_archivo(self.cleaned_data.get("archivo"))


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Nombre de usuario",
            "autocomplete": "username"
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Contraseña",
            "autocomplete": "current-password"
        })
    )
