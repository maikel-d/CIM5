from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.middleware.csrf import get_token
from functools import wraps

from .permissions import verificar_permiso_acceso


def _pagina_403(usuario, mensaje, csrf_token):
    """Genera el HTML de la página 403 con estilo glassmorphism."""
    return HttpResponseForbidden(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family:'Inter',system-ui,sans-serif; }}
            .bg {{ min-height:100vh; display:flex; align-items:center; justify-content:center;
                   background:linear-gradient(135deg,#0f1629 0%,#1a2540 50%,#0f1629 100%);
                   padding:1.5rem; }}
            .card {{ background:rgba(255,255,255,0.06); backdrop-filter:blur(20px);
                    -webkit-backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.08);
                    border-radius:24px; padding:3rem 2.5rem; max-width:440px; width:100%;
                    text-align:center; box-shadow:0 25px 60px rgba(0,0,0,0.5); }}
            .icon {{ width:72px; height:72px; margin:0 auto 1.5rem;
                    background:linear-gradient(135deg,rgba(255,107,107,0.2),rgba(255,107,107,0.05));
                    border-radius:20px; display:flex; align-items:center; justify-content:center; }}
            .icon svg {{ width:36px; height:36px; color:#ff6b6b; }}
            h1 {{ font-size:4.5rem; font-weight:800; line-height:1; margin-bottom:0.25rem;
                 background:linear-gradient(135deg,#ff6b6b,#ee5a24);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                 background-clip:text; }}
            h2 {{ font-size:1.3rem; font-weight:600; color:#e8edf5; margin-bottom:0.75rem; }}
            .msg {{ color:#8899b4; font-size:0.95rem; line-height:1.5; margin-bottom:1rem; }}
            .user {{ color:#5a7a9a; font-size:0.8rem; margin-bottom:2rem;
                    display:inline-block; background:rgba(255,255,255,0.04);
                    padding:0.4rem 1rem; border-radius:20px; }}
            .actions {{ display:flex; gap:0.75rem; flex-direction:column; }}
            .btn {{ display:block; padding:0.8rem 1.5rem; border-radius:12px;
                    font-size:0.9rem; font-weight:500; text-decoration:none;
                    transition:all 0.25s ease; cursor:pointer; border:none; }}
            .btn-primary {{ background:linear-gradient(135deg,#003363,#004a80); color:white; }}
            .btn-primary:hover {{ transform:translateY(-1px); box-shadow:0 8px 25px rgba(0,51,99,0.4); }}
            .btn-danger {{ background:linear-gradient(135deg,#991b1b,#b91c1c); color:white; }}
            .btn-danger:hover {{ transform:translateY(-1px); box-shadow:0 8px 25px rgba(185,28,28,0.4); }}
            .divider {{ color:#334466; font-size:0.75rem; margin:0.25rem 0; }}
            .footer {{ margin-top:2rem; font-size:0.7rem; color:#334466; }}
            .footer a {{ color:#4a7aaa; text-decoration:none; }}
            .footer a:hover {{ text-decoration:underline; }}
        </style>
        <div class="bg">
            <div class="card">
                <div class="icon">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                </div>
                <h1>403</h1>
                <h2>Accesso Denegado</h2>
                <p class="msg">{mensaje}</p>
                <span class="user"><svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:4px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>{usuario}</span>
                <div class="actions">
                    <a href="/" class="btn btn-primary">\u2190 Ir al inicio</a>
                    <span class="divider">\u00f3</span>
                    <form method="post" action="/logout/" style="margin:0;">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                        <button type="submit" class="btn btn-danger">Cerrar sesion</button>
                    </form>
                </div>
                <p class="footer">\n    Direcc\u00f3n General - Sistema de Gesti\u00f3n</p>
            </div>
        </div>
    """)



def permiso_required(*permisos):
    """Decorador para restringir acceso basado en permisos granulares.
    Uso: @permiso_required('personal_ver', 'personal_crear')
    Los superusuarios (is_superuser=True) siempre tienen acceso.
    Requiere que el UserProfile tenga el metodo tiene_permiso().
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if verificar_permiso_acceso(request.user, permisos):
                return view_func(request, *args, **kwargs)
            return _pagina_403(
                request.user,
                "No tienes permisos para acceder a esta sección.",
                get_token(request),
            )
        return _wrapped_view
    return decorator
