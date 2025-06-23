from pathlib import Path

def create_ips_patch(original_path, patched_path, output_path, start_offset, length):
    original = Path(original_path).read_bytes()
    patched = Path(patched_path).read_bytes()

    patch = b"PATCH"
    i = 0
    while i < length:
        if original[start_offset + i] != patched[start_offset + i]:
            start = start_offset + i
            run = 1
            while i + run < length and run < 65535 and original[start_offset + i + run] != patched[start_offset + i + run]:
                run += 1
            patch += start.to_bytes(3, 'big') + run.to_bytes(2, 'big') + patched[start:start+run]
            i += run
        else:
            i += 1
    patch += b"EOF"
    Path(output_path).write_bytes(patch)

if __name__ == "__main__":
    create_ips_patch(
        original_path="roms/Traysia (W).bin",
        patched_path="roms/Traysia (W)_nop_patch.bin",
        output_path="patches/Traysia_Shinyuden_ROM_nop_patch.ips",
        start_offset=0x1B520,
        length=32
    )
