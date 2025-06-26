"""Exporta e importa cadenas en castellano de la ROM para traducirlas.

Modo export: extrae las cadenas null-terminadas desde un rango y las guarda en
un JSON con su offset y longitud. Modo import: lee dicho JSON con las nuevas
traducciones y las escribe en la ROM respetando la longitud original.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict

DEFAULT_SPANISH_OFFSET = 0x100000
DEFAULT_SPANISH_END = 0x118000  # aproximado; ajustable mediante argumento


def extract_strings(data: bytes, start: int, end: int, encoding: str) -> List[Dict[str, int | str]]:
    strings = []
    pos = start
    while pos < end:
        term = data.find(b"\x00", pos, end)
        if term == -1:
            break
        if term > pos:
            chunk = data[pos:term]
            try:
                text = chunk.decode(encoding)
            except UnicodeDecodeError:
                text = chunk.decode(encoding, "replace")
            strings.append({"offset": pos, "length": term - pos + 1, "text": text})
        pos = term + 1
    return strings


def write_strings(data: bytearray, entries: List[Dict[str, int | str]], encoding: str) -> None:
    for entry in entries:
        off = entry["offset"]
        length = entry["length"]
        text = entry["text"]
        encoded = text.encode(encoding)
        if len(encoded) >= length:
            raise ValueError(f"Texto demasiado largo en offset 0x{off:X}")
        encoded += b"\x00"
        data[off:off + length] = encoded.ljust(length, b"\x00")


def export_mode(args: argparse.Namespace) -> None:
    data = Path(args.rom).read_bytes()
    end = args.end if args.end else len(data)
    strings = extract_strings(data, args.start, end, args.encoding)
    Path(args.output).write_text(json.dumps(strings, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extraidas {len(strings)} cadenas")


def import_mode(args: argparse.Namespace) -> None:
    data = bytearray(Path(args.rom).read_bytes())
    entries = json.loads(Path(args.json).read_text(encoding="utf-8"))
    write_strings(data, entries, args.encoding)
    Path(args.output).write_bytes(data)
    print(f"Insertadas {len(entries)} cadenas")


def main() -> None:
    parser = argparse.ArgumentParser(description="Exportar/Importar textos de Traysia")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_exp = sub.add_parser("export", help="Extrae cadenas a JSON")
    p_exp.add_argument("rom", help="Ruta a la ROM original")
    p_exp.add_argument("output", help="Archivo JSON de salida")
    p_exp.add_argument("--start", type=lambda x: int(x, 0), default=DEFAULT_SPANISH_OFFSET, help="Offset inicial")
    p_exp.add_argument("--end", type=lambda x: int(x, 0), default=DEFAULT_SPANISH_END, help="Offset final")
    p_exp.add_argument("--encoding", default="latin-1", help="Codificacion del texto")

    p_imp = sub.add_parser("import", help="Inserta traducciones desde JSON")
    p_imp.add_argument("rom", help="Ruta a la ROM original")
    p_imp.add_argument("json", help="Archivo JSON con traduccion")
    p_imp.add_argument("output", help="Ruta de la ROM modificada")
    p_imp.add_argument("--encoding", default="latin-1", help="Codificacion del texto")

    args = parser.parse_args()
    if args.cmd == "export":
        export_mode(args)
    else:
        import_mode(args)


if __name__ == "__main__":
    main()
