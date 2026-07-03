#!/usr/bin/env python3
"""Batch apply switch_to_english.py for multiple text blocks."""

from pathlib import Path
import argparse

from switch_to_english import switch_to_english

# Offsets determined from dump_text_blocks.py
BLOCKS = [
    {
        'spanish_offset': 0x100000,
        'english_offset': 0x07B706,
        'search_start': 0x000000,
        'search_end': 0x200000,
    },
    {
        'spanish_offset': 0x1180BE,
        'english_offset': 0x007605,
        'search_start': 0x000000,
        'search_end': 0x200000,
    },
    {
        'spanish_offset': 0x00C2C5,
        'english_offset': 0x008D72,
        'search_start': 0x000000,
        'search_end': 0x200000,
    },
]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Batch run switch_to_english.py over several text blocks"
    )
    parser.add_argument(
        "--overwrite-spanish",
        action="store_true",
        help="Copy English text over the Spanish block for each pass",
    )
    args = parser.parse_args(argv)

    input_rom = 'roms/Traysia (W).bin'
    temp_path = Path('roms/Traysia (W)_english.bin')
    working = input_rom
    for i, block in enumerate(BLOCKS):
        out = temp_path if i == len(BLOCKS) - 1 else temp_path.with_suffix(f'.tmp{i}')
        switch_to_english(
            working,
            str(out),
            spanish_offset=block['spanish_offset'],
            english_offset=block['english_offset'],
            search_start=block['search_start'],
            search_end=block['search_end'],
            overwrite_spanish=args.overwrite_spanish,
        )
        working = str(out)


if __name__ == '__main__':
    main()
