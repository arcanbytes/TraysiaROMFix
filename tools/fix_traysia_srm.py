import sys

def fix_traysia_shinyuden_srm(input_path, output_path=None):
    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    if len(data) != 8192:
        print("⚠️ Archivo SRM no válido (tamaño esperado: 8192 bytes).")
        return

    for slot in range(4):
        offset = slot * 64 + 51
        data[offset:offset+13] = bytes([0xFF] * 13)

    if not output_path:
        output_path = input_path.replace(".srm", "_fixed.srm")

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"✅ Archivo corregido guardado como: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fix_traysia_srm.py archivo_original.srm [archivo_salida.srm]")
    else:
        fix_traysia_shinyuden_srm(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
