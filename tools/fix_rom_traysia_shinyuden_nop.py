from pathlib import Path

def generate_traysia_save_fix_rom(input_rom_path: str, output_rom_path: str):
    """
    Parchea la ROM de Traysia (versión Shinyuden) para anular el bloque sospechoso
    que introduce datos corruptos en el guardado.

    Sustituye el bloque detectado por instrucciones NOP (0x4E71).

    Parámetros:
        input_rom_path: Ruta de la ROM original de Traysia (W).bin
        output_rom_path: Ruta donde se escribirá la ROM parcheada
    """
    rom = bytearray(Path(input_rom_path).read_bytes())

    # Bloque identificado en offset 0x1FD00 + (0x15 * 16), tamaño 32 bytes
    offset = 0x1FD00 + (0x15 * 16)
    block_size = 32

    # Instrucción NOP (68K): 0x4E71 (2 bytes)
    nop = b'\x4E\x71'
    nop_block = nop * (block_size // 2)

    rom[offset:offset + block_size] = nop_block
    Path(output_rom_path).write_bytes(rom)

if __name__ == "__main__":
    generate_traysia_save_fix_rom("roms/Traysia (W).bin", "roms/Traysia (W)_nop_patch.bin")
