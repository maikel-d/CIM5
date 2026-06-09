import sys
import qrcode

# Forzar UTF-8 en la salida (Windows)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def generar_qr(url, label="Escanea para abrir"):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    print()
    print(f"  {label}")
    print(f"  {url}")
    print()

    qr_ascii = qr.make_image().convert("1")
    pixels = qr_ascii.load()
    width, height = qr_ascii.size

    # Usar caracteres ASCII (# y espacio) para compatibilidad
    for y in range(height):
        line = ""
        for x in range(width):
            if pixels[x, y]:
                line += "  "
            else:
                line += "##"
        print(line)

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_qr.py <url>")
        sys.exit(1)
    generar_qr(sys.argv[1])
