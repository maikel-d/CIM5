import os

# Extensiones de archivo permitidas
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".jpg", ".jpeg", ".png", ".gif", ".txt",
}

# Firmas MIME: (offset, bytes_firma, extensiones_permitidas)
MIME_SIGNATURES = {
    "pdf": (0, b"%PDF", {".pdf"}),
    "png": (0, b"\x89PNG", {".png"}),
    "jpg": (0, b"\xff\xd8\xff", {".jpg", ".jpeg"}),
    "gif": (0, b"GIF8", {".gif"}),
    "zip": (0, b"PK\x03\x04", {".zip", ".docx", ".xlsx"}),
}


def leer_bytes(archivo):
    try:
        archivo.seek(0)
        header = archivo.read(16)
        archivo.seek(0)
        return header
    except Exception:
        return b""


def validar_tipo_real(archivo):
    """Valida que el contenido real del archivo coincida con su extension.
    Retorna (es_valido, mensaje_error).
    """
    if not archivo:
        return False, "No se recibio ningun archivo."

    ext = os.path.splitext(archivo.name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Formato no soportado: {ext}"

    header = leer_bytes(archivo)
    if not header or len(header) < 4:
        return False, "El archivo esta vacio o es demasiado pequeno para validar su tipo."

    tipo_detectado = None
    for tipo, (offset, firma, _) in MIME_SIGNATURES.items():
        if len(header) > offset + len(firma):
            if header[offset:offset + len(firma)] == firma:
                tipo_detectado = tipo
                break

    if tipo_detectado is None:
        return False, "El contenido del archivo no coincide con formatos permitidos."

    ext_permitidas = MIME_SIGNATURES[tipo_detectado][2]
    if ext not in ext_permitidas:
        return False, f"El archivo parece ser {tipo_detectado.upper()} pero tiene extension {ext}."

    return True, ""
