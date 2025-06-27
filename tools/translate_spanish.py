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

# Mapeo de caracteres especiales usado por la ROM.
# Cada letra acentuada se codifica como el byte 0x81 seguido de
# una letra. El juego principal emplea mayúsculas, pero algunos
# bloques alternativos utilizan códigos con la segunda letra en
# minúsculas para representar ciertas mayúsculas acentuadas.
_CANONICAL_MAP: dict[bytes, str] = {
    b"\x81J": "¡",
    b"\x81K": "¿",
    b"\x81L": "á",
    b"\x81M": "é",
    b"\x81N": "í",
    b"\x81O": "ó",
    b"\x81P": "ú",
    b"\x81Q": "ñ",
    b"\x81R": "Á",
    b"\x81S": "É",
    b"\x81T": "Í",
    b"\x81U": "Ó",
    b"\x81V": "Ú",
    b"\x81W": "Ñ",
}

# Códigos alternativos detectados en textos menos comunes.
_ALT_MAP: dict[bytes, str] = {
    b"\x81i": "Á",
    b"\x81j": "Á",
    b"\x81k": "Í",
    b"\x81l": "Ó",
    b"\x81m": "Ú",
    b"\x81n": "Ñ",
}

SPANISH_CHAR_MAP: dict[bytes, str] = {**_CANONICAL_MAP, **_ALT_MAP}

REVERSE_CHAR_MAP: dict[str, bytes] = {}
for pair, ch in _CANONICAL_MAP.items():
    REVERSE_CHAR_MAP[ch] = pair


def decode_custom(chunk: bytes, encoding: str) -> str:
    """Decodifica usando el mapa de caracteres especial."""
    result = []
    i = 0
    while i < len(chunk):
        if chunk[i] == 0x81 and i + 1 < len(chunk):
            pair = chunk[i:i + 2]
            char = SPANISH_CHAR_MAP.get(pair)
            if char is not None:
                result.append(char)
                i += 2
                continue
        result.append(chunk[i:i + 1].decode(encoding, errors="replace"))
        i += 1
    return "".join(result)


def encode_custom(text: str, encoding: str) -> bytes:
    """Codifica el texto aplicando el mismo mapa en sentido inverso."""
    out = bytearray()
    for ch in text:
        if ch in REVERSE_CHAR_MAP:
            out.extend(REVERSE_CHAR_MAP[ch])
        else:
            out.extend(ch.encode(encoding, errors="replace"))
    return bytes(out)

DEFAULT_SPANISH_OFFSET = 0x100000
DEFAULT_SPANISH_END = 0x120000  # aproximado; ajustable mediante argumento


def extract_strings(data: bytes, start: int, end: int, encoding: str) -> List[Dict[str, int | str]]:
    strings = []
    pos = start
    while pos < end:
        term = data.find(b"\x00", pos, end)
        if term == -1:
            break
        if term > pos:
            chunk = data[pos:term]
            text = decode_custom(chunk, encoding)
            strings.append({"offset": pos, "length": term - pos + 1, "text": text})
        pos = term + 1
    return strings


def write_strings(data: bytearray, entries: List[Dict[str, int | str]], encoding: str) -> None:
    for entry in entries:
        off = entry["offset"]
        length = entry["length"]
        text = entry["text"]
        encoded = encode_custom(text, encoding)
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