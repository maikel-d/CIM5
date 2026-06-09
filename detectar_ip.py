import socket

def get_local_ip():
    """Detecta la IP local de red (no loopback)."""
    try:
        # Conectar a un IP externa (no se establece conexion real)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass

    # Fallback: listar interfaces
    try:
        import subprocess
        import re
        output = subprocess.check_output(
            "netsh interface ip show addresses",
            shell=True, text=True, stderr=subprocess.DEVNULL
        )
        for line in output.split("\n"):
            m = re.search(r"IP Address[^:]*:\s*([\d.]+)", line, re.IGNORECASE)
            if m:
                ip = m.group(1)
                if ip != "127.0.0.1":
                    return ip
        # Buscar en espanol
        for line in output.split("\n"):
            m = re.search(r"Direcci.n IP[^:]*:\s*([\d.]+)", line)
            if m:
                ip = m.group(1)
                if ip != "127.0.0.1":
                    return ip
    except Exception:
        pass

    return ""


if __name__ == "__main__":
    ip = get_local_ip()
    print(ip)
