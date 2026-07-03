"""Switch the Spanish-language Traysia ROM to English by repointing text."""

from pathlib import Path
import argparse

DEFAULT_SPANISH_OFFSET = 0x100000  # address of Spanish script in Shinyuden ROM
DEFAULT_ENGLISH_OFFSET = 0x07B706  # start of English script in Shinyuden ROM
DEFAULT_ENGLISH_END = 0x0937C4     # end of English text block in Shinyuden ROM

# Opcodes "LEA addr, An" para A0-A7
LEA_OPCODES = [bytes([0x41 + n * 2, 0xF9]) for n in range(8)]

# Numero de reemplazos a partir del cual un patron poco distintivo
# (casi todo ceros) se considera sospechoso de falsos positivos.
LOW_ENTROPY_WARN_THRESHOLD = 100


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

    PATTERNS = {
        'be3': (
            spanish_offset.to_bytes(3, 'big'),
            english_offset.to_bytes(3, 'big'),
        ),
        'le3': (
            spanish_offset.to_bytes(3, 'little'),
            english_offset.to_bytes(3, 'little'),
        ),
        'be4': (
            spanish_offset.to_bytes(4, 'big'),
            english_offset.to_bytes(4, 'big'),
        ),
        'le4': (
            spanish_offset.to_bytes(4, 'little'),
            english_offset.to_bytes(4, 'little'),
        ),
        'be4shift': (
            (spanish_offset << 8).to_bytes(4, 'big'),
            (english_offset << 8).to_bytes(4, 'big'),
        ),
        'le4shift': (
            (spanish_offset << 8).to_bytes(4, 'little'),
            (english_offset << 8).to_bytes(4, 'little'),
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
        # Instrucciones LEA primero: producen el mismo reemplazo en bytes que
        # el patron generico 'be4', pero al ejecutarlas antes el recuento se
        # atribuye correctamente a 'leaN' en lugar de mezclarse con 'be4'.
        lea_old = spanish_offset.to_bytes(4, 'big')
        lea_new = english_offset.to_bytes(4, 'big')
        for idx, op in enumerate(LEA_OPCODES):
            counts[f'lea{idx}'] = replace_within(data, op + lea_old, op + lea_new)

        for name, (old, new) in PATTERNS.items():
            occurrences = replace_within(data, old, new)
            counts[name] = occurrences
            distinctive = sum(1 for b in old if b != 0)
            if occurrences > LOW_ENTROPY_WARN_THRESHOLD and distinctive <= 1:
                print(
                    f"Warning: el patron '{name}' ({old.hex(' ')}) es poco distintivo y ha "
                    f"reemplazado {occurrences} coincidencias; es probable que muchas sean "
                    "falsos positivos. Limita el rango con --search-start/--search-end."
                )
    else:
        counts['pointers_skipped'] = 0

    if overwrite_spanish:
        if length is not None:
            text_length = length
        else:
            text_length = DEFAULT_ENGLISH_END - english_offset
        # No leer mas alla del final de la ROM...
        end = min(english_offset + text_length, len(data))
        block = data[english_offset:end]
        # ...ni escribir mas alla (la asignacion de slice de un bytearray
        # agrandaria el archivo silenciosamente).
        block = block[:max(len(data) - spanish_offset, 0)]
        data[spanish_offset:spanish_offset + len(block)] = block
        counts['overwrite'] = len(block)
    elif sum(counts.values()) <= 1:
        print("Warning: se encontraron muy pocos punteros. Prueba a usar --overwrite-spanish o revisa los offsets.")

    Path(output_path).write_bytes(bytes(data))
    total = sum(counts.values())
    detail = ", ".join(f"{k}:{v}" for k, v in counts.items() if v)
    print(f"Replaced {total} pointers ({detail or 'sin coincidencias'})")


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
