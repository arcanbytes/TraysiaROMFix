"""Switch the Spanish-language Traysia ROM to English by repointing text."""

from pathlib import Path
import argparse

DEFAULT_SPANISH_OFFSET = 0x100000  # address of Spanish script in Shinyuden ROM
DEFAULT_ENGLISH_OFFSET = 0x07B706  # start of English script in Shinyuden ROM
DEFAULT_ENGLISH_END = 0x0937C4     # end of English text block in Shinyuden ROM

SPANISH_TEXT_OFFSET = DEFAULT_SPANISH_OFFSET
ENGLISH_TEXT_OFFSET = DEFAULT_ENGLISH_OFFSET

# Opcodes "LEA addr, An" para A0-A7
LEA_OPCODES = [bytes([0x41 + n * 2, 0xF9]) for n in range(8)]

def detect_offsets(data: bytes) -> tuple[int, int]:
    """Attempt to locate the Spanish and English text blocks automatically."""
    english_mark = b"THE KINGDOM"
    spanish_mark = b"EL REINO"
    english_offset = data.find(english_mark)
    spanish_offset = data.find(spanish_mark)
    return english_offset, spanish_offset

def switch_to_english(rom_path: str, output_path: str,
                      english_offset: int | None = None,
                      spanish_offset: int | None = None,
                      overwrite_spanish: bool = False,
                      skip_pointers: bool = False,
                      length: int | None = None,
                      search_start: int | None = None,
                      search_end: int | None = None):
    path = Path(rom_path)
    data = bytearray(path.read_bytes())

    if search_start is None:
        search_start = 0
    if search_end is None or search_end > len(data):
        search_end = len(data)

    auto_eng, auto_span = detect_offsets(data)
    if english_offset is None:
        english_offset = DEFAULT_ENGLISH_OFFSET
        if auto_eng != -1 and auto_eng != english_offset:
            print(f"Detected English text at 0x{auto_eng:X}; using default 0x{english_offset:X}")
    if spanish_offset is None:
        spanish_offset = DEFAULT_SPANISH_OFFSET
        if auto_span != -1 and auto_span != spanish_offset:
            print(f"Detected Spanish text at 0x{auto_span:X}; using default 0x{spanish_offset:X}")

    global SPANISH_TEXT_OFFSET, ENGLISH_TEXT_OFFSET
    SPANISH_TEXT_OFFSET = spanish_offset
    ENGLISH_TEXT_OFFSET = english_offset

    PATTERNS = {
        'be3': (
            SPANISH_TEXT_OFFSET.to_bytes(3, 'big'),
            ENGLISH_TEXT_OFFSET.to_bytes(3, 'big'),
        ),
        'le3': (
            SPANISH_TEXT_OFFSET.to_bytes(3, 'little'),
            ENGLISH_TEXT_OFFSET.to_bytes(3, 'little'),
        ),
        'be4': (
            SPANISH_TEXT_OFFSET.to_bytes(4, 'big'),
            ENGLISH_TEXT_OFFSET.to_bytes(4, 'big'),
        ),
        'le4': (
            SPANISH_TEXT_OFFSET.to_bytes(4, 'little'),
            ENGLISH_TEXT_OFFSET.to_bytes(4, 'little'),
        ),
        'be4shift': (
            (SPANISH_TEXT_OFFSET << 8).to_bytes(4, 'big'),
            (ENGLISH_TEXT_OFFSET << 8).to_bytes(4, 'big'),
        ),
        'le4shift': (
            (SPANISH_TEXT_OFFSET << 8).to_bytes(4, 'little'),
            (ENGLISH_TEXT_OFFSET << 8).to_bytes(4, 'little'),
        ),
        'hilo': (
            (SPANISH_TEXT_OFFSET >> 16).to_bytes(2, 'big') +
            (SPANISH_TEXT_OFFSET & 0xFFFF).to_bytes(2, 'big'),
            (ENGLISH_TEXT_OFFSET >> 16).to_bytes(2, 'big') +
            (ENGLISH_TEXT_OFFSET & 0xFFFF).to_bytes(2, 'big'),
        ),
    }

    counts = {}

    def replace_within(buf: bytearray, old: bytes, new: bytes) -> int:
        count = 0
        idx = buf.find(old, search_start)
        while idx != -1 and idx < search_end:
            buf[idx:idx + len(old)] = new
            idx = buf.find(old, idx + len(new))
            count += 1
        return count

    if not skip_pointers:
        for name, (old, new) in PATTERNS.items():
            occurrences = replace_within(data, old, new)
            counts[name] = occurrences

        # Buscar instrucciones LEA que cargan la direccion del texto en castellano
        lea_old = SPANISH_TEXT_OFFSET.to_bytes(4, 'big')
        lea_new = ENGLISH_TEXT_OFFSET.to_bytes(4, 'big')
        for idx, op in enumerate(LEA_OPCODES):
            search = op + lea_old
            replace = op + lea_new
            key = f'lea{idx}'
            occ = replace_within(data, search, replace)
            counts[key] = occ
    else:
        counts['pointers_skipped'] = 0

    if overwrite_spanish:
        if length is not None:
            text_length = length
        else:
            text_length = DEFAULT_ENGLISH_END - ENGLISH_TEXT_OFFSET
        end = ENGLISH_TEXT_OFFSET + text_length
        if end > len(data):
            end = len(data)
            text_length = end - ENGLISH_TEXT_OFFSET
        block = data[ENGLISH_TEXT_OFFSET:end]
        data[SPANISH_TEXT_OFFSET:SPANISH_TEXT_OFFSET + text_length] = block
        counts['overwrite'] = text_length
    elif sum(counts.values()) <= 1:
        print("Warning: se encontraron muy pocos punteros. Prueba a usar --overwrite-spanish o revisa los offsets.")

    Path(output_path).write_bytes(bytes(data))
    total = sum(counts.values())
    detail = ", ".join(f"{k}:{v}" for k, v in counts.items())
    print(f"Replaced {total} pointers ({detail})")

def main() -> None:
    """Parse CLI arguments and apply the language switch."""
    parser = argparse.ArgumentParser(
        description="Switch Traysia (W).bin language to English"
    )
    parser.add_argument(
        "input_rom",
        nargs="?",
        default="roms/Traysia (W).bin",
        help="Path to original Spanish ROM",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_rom",
        default="roms/Traysia (W)_english.bin",
        help="Output ROM path",
    )
    parser.add_argument(
        "--spanish-offset",
        type=lambda x: int(x, 0),
        help="Offset of Spanish text block (hex or decimal)",
    )
    parser.add_argument(
        "--english-offset",
        type=lambda x: int(x, 0),
        help="Offset of English text block (hex or decimal)",
    )
    parser.add_argument(
        "--overwrite-spanish",
        action="store_true",
        help="Copy the English text block over the Spanish one",
    )
    parser.add_argument(
        "--length",
        type=lambda x: int(x, 0),
        help="Bytes to copy when overwriting (default: length of English block)",
    )
    parser.add_argument(
        "--search-start",
        type=lambda x: int(x, 0),
        help="Start offset to search for pointers",
    )
    parser.add_argument(
        "--search-end",
        type=lambda x: int(x, 0),
        help="End offset (exclusive) for pointer search",
    )
    parser.add_argument(
        "--skip-pointers",
        action="store_true",
        help="Do not patch any pointer references; only copy text if requested",
    )
    args = parser.parse_args()
    switch_to_english(
        args.input_rom,
        args.output_rom,
        english_offset=args.english_offset,
        spanish_offset=args.spanish_offset,
        overwrite_spanish=args.overwrite_spanish,
        skip_pointers=args.skip_pointers,
        length=args.length,
        search_start=args.search_start,
        search_end=args.search_end,
    )


if __name__ == "__main__":
    main()
