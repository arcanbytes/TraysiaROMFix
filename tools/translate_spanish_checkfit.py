#!/usr/bin/env python3
import json, sys
from translate_spanish import encode_custom  # reutilizamos la misma rutina

def main(path, encoding="latin-1"):
    bad = []
    for e in json.load(open(path, encoding="utf-8")):
        txt = e["text"]
        need = len(encode_custom(txt, encoding)) + 1   # +0x00
        if need > e["length"]:
            bad.append((e["offset"], e["length"], need, txt))

    if bad:
        print(f"{len(bad)} cadenas demasiado largas:\n")
        for off, lim, need, txt in bad:
            # Modified line to include both hexadecimal and decimal
            print(f"   offset 0x{off:X} ({off})   reservado={lim}   necesita={need}   →   «{txt}»")
    else:
        print("✓   Todas las cadenas caben.")

if __name__ == "__main__":
    main(sys.argv[1])