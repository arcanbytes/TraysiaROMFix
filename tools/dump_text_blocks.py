import argparse
import re
from pathlib import Path
import sys

DEFAULT_MIN_LEN = 20
DEFAULT_WIDTH = 60

def build_regex(min_len: int, latin1: bool) -> re.Pattern:
    if latin1:
        charset = rb"[\x20-\x7E\x80-\xFF]"
    else:
        charset = rb"[\x20-\x7E]"
    return re.compile(charset + rb"{%d,}" % min_len)



def scan_blocks(data: bytes, min_len: int, latin1: bool, start: int = 0):
    ascii_re = build_regex(min_len, latin1)
    encoding = 'latin-1' if latin1 else 'ascii'
    for m in ascii_re.finditer(data, start):
        start_off = m.start()
        text = m.group().decode(encoding, errors='replace')
        yield start_off, len(m.group()), text


def main(path: str, min_len: int, width: int, latin1: bool, start: int):
    data = Path(path).read_bytes()
    encoding = "latin-1" if latin1 else "ascii"
    for off, length, text in scan_blocks(data, min_len, latin1, start):
        out = text.replace("\n", " ")
        if width > 0:
            out = out[:width]
        line = f"0x{off:06X}+{length:04X}: {out}\n"
        sys.stdout.buffer.write(line.encode(encoding, errors="replace"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dump ASCII text blocks from a ROM")
    parser.add_argument('rom', help='Path to ROM file')
    parser.add_argument('--min-len', type=int, default=DEFAULT_MIN_LEN, help='Minimum block length')
    parser.add_argument('--width', type=int, default=DEFAULT_WIDTH, help='Maximum characters to show per block; use 0 for all')
    parser.add_argument('--latin1', action='store_true', help='Detect extended Latin-1 characters')
    parser.add_argument('--start', type=lambda x: int(x, 0), default=0, help='Start offset for scanning')
    args = parser.parse_args()
    main(args.rom, args.min_len, args.width, args.latin1, args.start)
