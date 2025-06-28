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

# Caracteres alemanes comunes (extensión específica para DE)
_DE_MAP: dict[bytes, str] = {
    b"\x81a": "ä",
    b"\x81b": "ö",
    b"\x81c": "ü",
    b"\x81d": "Ä",
    b"\x81e": "Ö",
    b"\x81f": "Ü",
    b"\x81g": "ß",
}

SPANISH_CHAR_MAP: dict[bytes, str] = {**_CANONICAL_MAP, **_ALT_MAP, **_DE_MAP}

REVERSE_CHAR_MAP: dict[str, bytes] = {}
for pair, ch in {**_CANONICAL_MAP, **_ALT_MAP, **_DE_MAP}.items():
    REVERSE_CHAR_MAP[ch] = pair

def transliterate_de(text: str) -> str: # específico para Traysia DE)
    return (text
        .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        .replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
        .replace("ß", "ss"))

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

ENABLE_TRANSLIT = True  # cambia a False si no quieres transliteración DE

def encode_custom(text: str, encoding: str) -> bytes:
    if ENABLE_TRANSLIT:
        text = transliterate_de(text)
    out = bytearray()
    for ch in text:
        if ch in REVERSE_CHAR_MAP:
            out.extend(REVERSE_CHAR_MAP[ch])
        else:
            out.extend(ch.encode(encoding, errors="replace"))
    return bytes(out)

#ALL (strings acabados en b"\x00") ← Solo para exploración!
#DEFAULT_SPANISH_OFFSET = 0x000000
#DEFAULT_SPANISH_END = 0x200000  # aproximado; ajustable mediante argumento

#BLOQUE 1 NARRATIVA y DIALOGOS (strings acabados en b"\x00")
#DEFAULT_SPANISH_OFFSET = 0x100000
#DEFAULT_SPANISH_END = 0x1181A5  # aproximado; ajustable mediante argumento

#BLOQUE 2 ENEMIGOS 
#DEFAULT_SPANISH_OFFSET = 0x1FDB00
#DEFAULT_SPANISH_END = 0x1FFF00

#BLOQUE 3 NARRATIVA EXTRA 
#DEFAULT_SPANISH_OFFSET = 0x00C2C4
#DEFAULT_SPANISH_END = 0xC55B

#BLOQUE 4 MENU PARTIDA
#DEFAULT_SPANISH_OFFSET = 0x1C119
#DEFAULT_SPANISH_END = 0x1C232

#BLOQUE 5 ITEMS
#DEFAULT_SPANISH_OFFSET = 0x12E0D
#DEFAULT_SPANISH_END = 0x133FD
#---------------------------------------
# Bloques de texto conocidos de Traysia
BLOCKS = [
    (0x100000, 0x1181A5),  # BLOQUE 1: Narrativa principal
    (0x1FDB00, 0x1FFF00),  # BLOQUE 2: Enemigos
    (0x00C2C4, 0x00C55B),  # BLOQUE 3: Narrativa extra
    (0x1C119,  0x1C232),   # BLOQUE 4: Menú de partida
    (0x12E0D,  0x133FD),   # BLOQUE 5: Items
    (0x1436C,  0x14787),   # BLOQUE 5: Tiendas
]

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
            strings.append({
                "offset": pos,
                "offset_hex": f"0x{pos:X}",  # ← mismo valor en hexadecimal
                "length": term - pos + 1,
                "text": text,
                "text_source": text  # ← para referencia
            })
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


def export_mode(rom_path: Path, json_path: Path, encoding: str):
    data = rom_path.read_bytes()
    strings = []
    for start, end in BLOCKS:
        strings.extend(extract_strings(data, start, end, encoding))
    strings.sort(key=lambda s: s["offset"])
    json_path.write_text(json.dumps(strings, ensure_ascii=False, indent=2), "utf-8")
    print(f"✔ Exportadas {len(strings)} cadenas → {json_path}")

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
    p_exp.add_argument("--encoding", default="latin-1", help="Codificacion del texto (por defecto: latin-1). Se usan bloques predefinidos.")
    p_imp = sub.add_parser("import", help="Inserta traducciones desde JSON")
    p_imp.add_argument("rom", help="Ruta a la ROM original")
    p_imp.add_argument("json", help="Archivo JSON con traduccion")
    p_imp.add_argument("output", help="Ruta de la ROM modificada")
    p_imp.add_argument("--encoding", default="latin-1", help="Codificacion del texto")

    args = parser.parse_args()
    if args.cmd == "export":
        export_mode(Path(args.rom), Path(args.output), args.encoding)
    else:
        import_mode(args)


if __name__ == "__main__":
    main()