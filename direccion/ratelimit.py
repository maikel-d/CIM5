"""Rate limiting para el login del Sistema de Gestion.

Proporciona:
- Rate limiting por username (3 intentos, lockout progresivo)
- Rate limiting por IP (10 intentos/hora)
- Logging de eventos de seguridad
- Cache-based (usa DatabaseCache de Django)
"""

import logging
import time

from django.core.cache import cache

# Configuracion de rate limiting
MAX_USERNAME_ATTEMPTS = 3  # Intentos antes de bloquear username
BASE_LOCKOUT_SECONDS = 60  # Bloqueo inicial (se multiplica progresivamente)
MAX_IP_ATTEMPTS = 10  # Intentos por IP antes de bloqueo
IP_LOCKOUT_SECONDS = 3600  # 1 hora de bloqueo por IP
MAX_PROGRESSIVE_LOCKOUT = 3600  # Limite maximo de bloqueo progresivo (1h)

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Obtiene la IP real del cliente, manejando proxys."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _get_lockout_time(strike_count):
    """Calcula el tiempo de bloqueo progresivo.
    
    1er bloqueo: 60s
    2do bloqueo: 300s (5 min)
    3er bloqueo: 900s (15 min)
    4to+ bloqueo: 3600s (1 hora, maximo)
    """
    # Formula: base * 5^(strikes-1), capped at MAX_PROGRESSIVE_LOCKOUT
    seconds = BASE_LOCKOUT_SECONDS * (5 ** (strike_count - 1))
    return min(seconds, MAX_PROGRESSIVE_LOCKOUT)


def check_ip_rate_limit(request):
    """Verifica si la IP del cliente esta bloqueada.
    
    Returns:
        dict con bloqueado, tiempo_restante, y razon, o None si no hay bloqueo.
    """
    ip = get_client_ip(request)
    cache_key = f"rate_limit_ip_{ip}"
    lockout_until = cache.get(cache_key)
    
    if lockout_until and time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        return {
            "bloqueado": True,
            "tiempo_restante": remaining,
            "razon": "ip",
            "mensaje": f"Demasiados intentos desde esta IP. Espere {remaining} segundos.",
        }
    return None


def check_username_rate_limit(username):
    """Verifica si un usuario especifico esta bloqueado.
    
    Returns:
        dict si esta bloqueado, o None si no.
    """
    cache_key = f"login_failures_{username}"
    data = cache.get(cache_key)
    
    if data and isinstance(data, dict):
        intentos = data.get("intentos", 0)
        lockout_until = data.get("lockout_until", 0)
        strike = data.get("strike", 1)
        
        if intentos >= MAX_USERNAME_ATTEMPTS and time.time() < lockout_until:
            remaining = int(lockout_until - time.time())
            return {
                "bloqueado": True,
                "tiempo_restante": remaining,
                "razon": "username",
                "strike": strike,
                "mensaje": f"Demasiados intentos fallidos. Espere {remaining} segundos.",
            }
    return None


def record_failed_attempt(request, username):
    """Registra un intento fallido de login.
    
    Incrementa contadores tanto por username como por IP.
    Si se alcanza el limite, activa el bloqueo con tiempo progresivo.
    """
    ip = get_client_ip(request)
    
    # 1. Registrar intento por IP
    ip_key = f"rate_limit_ip_attempts_{ip}"
    ip_attempts = cache.get(ip_key, 0)
    ip_attempts += 1
    
    if ip_attempts >= MAX_IP_ATTEMPTS:
        # Bloquear IP por IP_LOCKOUT_SECONDS
        lock_key = f"rate_limit_ip_{ip}"
        cache.set(lock_key, time.time() + IP_LOCKOUT_SECONDS, IP_LOCKOUT_SECONDS)
        cache.delete(ip_key)  # Resetear contador
        logger.warning(
            "[RATE_LIMIT] IP bloqueada: %s - %d intentos en %d segundos",
            ip, ip_attempts, IP_LOCKOUT_SECONDS,
        )
    else:
        # TTL de la IP: ventana de 1 hora
        cache.set(ip_key, ip_attempts, IP_LOCKOUT_SECONDS)
    
    # 2. Registrar intento por username (con bloqueo progresivo)
    username_key = f"login_failures_{username}"
    data = cache.get(username_key)
    
    if data and isinstance(data, dict):
        intentos = data.get("intentos", 0) + 1
        strike = data.get("strike", 1)
    else:
        intentos = 1
        strike = 1
    
    if intentos >= MAX_USERNAME_ATTEMPTS:
        # Calcular lockout progresivo
        lockout_time = _get_lockout_time(strike)
        lockout_until = time.time() + lockout_time
        strike += 1
        
        cache.set(username_key, {
            "intentos": intentos,
            "lockout_until": lockout_until,
            "strike": strike,
        }, lockout_time + 60)  # 60s extra de margen
        
        logger.warning(
            "[RATE_LIMIT] Usuario bloqueado: %s desde IP %s - strike %d, lockout %ds",
            username, ip, strike - 1, lockout_time,
        )
    else:
        # Guardar en cache con TTL del lockout base (aunque aun no este bloqueado)
        cache.set(username_key, {
            "intentos": intentos,
            "lockout_until": 0,
            "strike": strike,
        }, BASE_LOCKOUT_SECONDS * 5)
    
    return intentos, MAX_USERNAME_ATTEMPTS - intentos


def clear_rate_limits(username):
    """Limpia los contadores de rate limiting tras un login exitoso."""
    cache.delete(f"login_failures_{username}")
