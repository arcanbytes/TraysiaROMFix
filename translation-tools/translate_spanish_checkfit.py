#!/usr/bin/env python3
"""Comprueba si las cadenas traducidas de un JSON caben en el espacio
reservado en la ROM (mismo criterio que translate_spanish.py import)."""

import argparse
import json
import sys

# Evita errores de codificacion en consolas que no son UTF-8 (p.ej. cp1252)
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

import translate_spanish
from translate_spanish import encode_custom  # reutilizamos la misma rutina


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifica que cada cadena traducida cabe en su hueco de la ROM"
    )
    parser.add_argument("json_file", help="Archivo JSON con las traducciones")
    parser.add_argument("--encoding", default="latin-1", help="Codificacion del texto")
    parser.add_argument(
        "--no-translit",
        action="store_true",
        help="No transliterar caracteres alemanes antes de medir (debe coincidir con la opcion usada al importar)",
    )
    args = parser.parse_args()

    if args.no_translit:
        translate_spanish.ENABLE_TRANSLIT = False

    with open(args.json_file, encoding="utf-8") as fh:
        entries = json.load(fh)

    bad = []
    for e in entries:
        txt = e["text"]
        need = len(encode_custom(txt, args.encoding)) + 1   # +0x00
        if need > e["length"]:
            bad.append((e["offset"], e["length"], need, txt))

    if bad:
        print(f"{len(bad)} cadenas demasiado largas:\n")
        for off, lim, need, txt in bad:
            print(f"   offset 0x{off:X} ({off})   reservado={lim}   necesita={need}   →   «{txt}»")
        sys.exit(1)
    print("✓   Todas las cadenas caben.")


if __name__ == "__main__":
    main()
