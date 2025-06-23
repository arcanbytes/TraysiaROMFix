import argparse
from pathlib import Path

ALLOWED_SIZES = {8192, 16384, 65536}


def fix_traysia_shinyuden_srm(input_path: str, output_path: str):
    data = bytearray(Path(input_path).read_bytes())

    if len(data) not in ALLOWED_SIZES:
        print("⚠️ Archivo SRM no válido (tama\u00f1o permitido: 8 KB, 16 KB o 64 KB).")
        return

    for slot in range(4):
        offset = slot * 64 + 51
        data[offset:offset+13] = bytes([0xFF] * 13)

    Path(output_path).write_bytes(data)

    print(f"✅ Archivo corregido guardado como: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corrige un archivo .srm de Traysia Shinyuden")
    parser.add_argument("input_file", help="Archivo .srm a reparar")
    parser.add_argument("-o", "--output", dest="output", help="Nombre del archivo de salida")
    args = parser.parse_args()

    output_file = args.output or args.input_file.replace(".srm", "_fixed.srm")
    fix_traysia_shinyuden_srm(args.input_file, output_file)
