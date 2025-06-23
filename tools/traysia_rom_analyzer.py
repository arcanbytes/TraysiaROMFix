# traysia_rom_analyzer.py

import hashlib
import os

def parse_md_header(rom_path):
    with open(rom_path, "rb") as f:
        f.seek(0x100)
        header = f.read(0x50)

    return {
        "ROM Name (domestic)": header[0x00:0x10].decode("ascii", errors="replace").strip(),
        "ROM Name (overseas)": header[0x10:0x20].decode("ascii", errors="replace").strip(),
        "Product Type": header[0x20:0x22].hex().upper(),
        "Checksum": f"0x{int.from_bytes(header[0x18:0x1A], 'big'):04X}",
        "Region": header[0x4F:0x50].decode("ascii", errors="replace")
    }

def calculate_hashes(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()
    return md5, sha1, len(data)

def compare_roms(path_a, path_b):
    with open(path_a, "rb") as f:
        data_a = f.read()
    with open(path_b, "rb") as f:
        data_b = f.read()

    size_a, size_b = len(data_a), len(data_b)
    min_size = min(size_a, size_b)
    max_size = max(size_a, size_b)

    diffs = 0
    diff_offsets = []
    for i in range(min_size):
        if data_a[i] != data_b[i]:
            diffs += 1
            if len(diff_offsets) < 5:
                diff_offsets.append((i, data_a[i], data_b[i]))

    if size_a != size_b:
        diffs += max_size - min_size

    return {
        "Size A": size_a,
        "Size B": size_b,
        "Bytes Different": diffs,
        "Sample Offsets": diff_offsets
    }

def summarize_rom(rom_path):
    header = parse_md_header(rom_path)
    md5, sha1, size = calculate_hashes(rom_path)
    summary = header.copy()
    summary["MD5"] = md5
    summary["SHA1"] = sha1
    summary["Size"] = size
    return summary

# Example usage:
if __name__ == "__main__":
    roms = {
        "Japón": "roms/Minato no Traysia (Japan).md",
        "USA": "roms/Traysia (USA).md",
        "Evercade": "roms/Traysia (World) (Evercade).md",
        "Español": "roms/Traysia (W).bin"
    }

    print("--- ROM Summaries ---")
    for name, path in roms.items():
        info = summarize_rom(path)
        print(f"\n{name}:")
        for k, v in info.items():
            print(f"  {k}: {v}")

    print("\n--- Binary Comparisons ---")
    comparisons = [
        ("Japón", "USA"),
        ("USA", "Evercade"),
        ("Japón", "Español")
    ]

    for a, b in comparisons:
        result = compare_roms(roms[a], roms[b])
        print(f"\nComparando {a} vs {b}:")
        for k, v in result.items():
            print(f"  {k}: {v}")
