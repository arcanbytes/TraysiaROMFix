#!/usr/bin/env python3
"""Batch apply switch_to_english.py for multiple text blocks."""

from pathlib import Path
import argparse

from switch_to_english import switch_to_english

# Offsets determinados con dump_text_blocks.py.
#
# 'length' es la capacidad del bloque en castellano de destino: al usar
# --overwrite-spanish nunca se copian mas bytes que eso, para que el texto
# ingles no pise los datos adyacentes al bloque. (Sin este limite, los
# bloques 2 y 3 heredarian la longitud por defecto del bloque principal y
# sobreescribirian cientos de KB de codigo y datos.)
BLOCKS = [
    {   # Bloque 1: narrativa principal (segundo MB de la ROM)
        'spanish_offset': 0x100000,
        'english_offset': 0x07B706,
        'length': 0x0180BE,   # 0x0937C4 - 0x07B706 (tamano del bloque ingles)
        'search_start': 0x000000,
        'search_end': 0x200000,
    },
    {   # Bloque 2: cola de la narrativa (0x1180BE-0x1181A5)
        'spanish_offset': 0x1180BE,
        'english_offset': 0x007605,
        'length': 0x0000E7,   # 0x1181A5 - 0x1180BE
        'search_start': 0x000000,
        'search_end': 0x200000,
    },
    {   # Bloque 3: narrativa extra (0xC2C5-0xC55B, primer MB)
        'spanish_offset': 0x00C2C5,
        'english_offset': 0x008D72,
        'length': 0x000296,   # 0x00C55B - 0x00C2C5
        'search_start': 0x000000,
        'search_end': 0x200000,
    },
]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Batch run switch_to_english.py over several text blocks"
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
        "--overwrite-spanish",
        action="store_true",
        help="Copy English text over the Spanish block for each pass",
    )
    args = parser.parse_args(argv)

    final_path = Path(args.output_rom)
    working = args.input_rom
    temp_files: list[Path] = []
    for i, block in enumerate(BLOCKS):
        if i == len(BLOCKS) - 1:
            out = final_path
        else:
            out = final_path.with_suffix(f'.tmp{i}')
            temp_files.append(out)
        print(
            f"--- Bloque {i + 1}/{len(BLOCKS)}: "
            f"ES 0x{block['spanish_offset']:06X} -> EN 0x{block['english_offset']:06X} ---"
        )
        switch_to_english(
            working,
            str(out),
            spanish_offset=block['spanish_offset'],
            english_offset=block['english_offset'],
            search_start=block['search_start'],
            search_end=block['search_end'],
            length=block['length'],
            overwrite_spanish=args.overwrite_spanish,
        )
        working = str(out)

    for tmp in temp_files:
        tmp.unlink(missing_ok=True)
    print(f"ROM final: {final_path}")


if __name__ == '__main__':
    main()
