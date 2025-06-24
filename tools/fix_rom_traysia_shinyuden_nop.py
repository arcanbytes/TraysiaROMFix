from pathlib import Path
import argparse
import hashlib

# MD5 checksum of the original "Traysia (W).bin" ROM distributed by Shinyuden
# Replace this value with the full hash if different
EXPECTED_MD5 = "db1529b9d6383bdb5b2d6c969cef6022"


def generate_traysia_save_fix_rom(input_rom_path: str, output_rom_path: str):
    """
    Parchea la ROM de Traysia (versión Shinyuden) para anular el bloque sospechoso
    que introduce datos corruptos en el guardado.

    Sustituye el bloque detectado por instrucciones NOP (0x4E71).

    Parámetros:
        input_rom_path: Ruta de la ROM original de Traysia (W).bin
        output_rom_path: Ruta donde se escribirá la ROM parcheada
    """

    data = Path(input_rom_path).read_bytes()

    md5_hash = hashlib.md5(data).hexdigest()
    if md5_hash != EXPECTED_MD5:
        print(f"⚠️  MD5 diferente al esperado.\n  Esperado: {EXPECTED_MD5}\n  Obtenido: {md5_hash}")
        cont = input("¿Continuar de todos modos? [y/N]: ")
        if cont.lower() != "y":
            print("Abortando.")
            return

    rom = bytearray(data)
    
    # Bloque identificado en offset 0x1B520 (rutina que escribe "_data" en SRAM)
    offset = 0x1B520
    block_size = 32

    # Instrucción NOP (68K): 0x4E71 (2 bytes)
    nop = b'\x4E\x71'
    nop_block = nop * (block_size // 2)

    rom[offset:offset + block_size] = nop_block
    Path(output_rom_path).write_bytes(rom)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parchea la ROM de Traysia Shinyuden remplazando el bloque '_data' por NOPs"
    )
    parser.add_argument(
        "input_rom",
        nargs="?",
        default="roms/Traysia (W).bin",
        help="Ruta a la ROM original"
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_rom",
        default="roms/Traysia (W)_nop_patch.bin",
        help="Ruta donde se escribirá la ROM parcheada"
    )
    args = parser.parse_args()

    generate_traysia_save_fix_rom(args.input_rom, args.output_rom)
