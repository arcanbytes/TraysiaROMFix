"""Parche "Anticrash SRAM" para Traysia (Shinyuden Edition).

La ROM de Shinyuden (2 MB) conserva 16 referencias al monitor de depuracion
que el juego original (1992) tenia en $100000, reubicadas mecanicamente a
$200000 al expandir la ROM. En el cartucho fisico $200000 es la ventana de
SRAM, por lo que cualquier excepcion de CPU o cualquier puntero de texto
fuera de rango acaba EJECUTANDO el contenido de la SRAM como codigo, con
riesgo de corromper las partidas guardadas.

Este script aplica la mitigacion:

  1. Los 14 stubs de excepcion (vectores 2-11, 14-15, 24 y TRAPs #2-#15,
     en 0x372..0x414) pasan de `jmp $200000` a `jmp $000200` -> reinicio
     limpio a traves del bootstrap oficial de Sega, con la SRAM intacta.

  2. El guard del streamer de texto (0x1504) pasa de `jmp $200000` a
     `moveq #0,d7 ; bra.s $150C` -> simula la lectura de un terminador de
     cadena y toma la ruta normal de fin de texto (el `beq` de 0x150C).

No se modifica ninguna otra logica del juego. Ver README.md para el
analisis tecnico completo.
"""

from pathlib import Path
import argparse
import hashlib
import sys

# Evita errores de codificacion en consolas que no son UTF-8 (p.ej. cp1252)
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

# MD5 de la ROM original "Traysia (W).bin" distribuida por Shinyuden
EXPECTED_MD5 = "db1529b9d6383bdb5b2d6c969cef6022"

# (offset, bytes originales, bytes nuevos)
PATCHES = [
    # 14 stubs de excepcion: operando de `jmp $200000.l` -> `jmp $000200.l`
    *[
        (0x37A + 12 * k, b"\x00\x20\x00\x00", b"\x00\x00\x02\x00")
        for k in range(14)
    ],
    # Guard del streamer de texto: `jmp $200000.l` ->
    # `moveq #0,d7 ; bra.s $150C ; nop` (simula terminador de cadena)
    (0x1504, b"\x4e\xf9\x00\x20\x00\x00", b"\x7e\x00\x60\x04\x4e\x71"),
]

IPS_DEFAULT = "patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips"


def build_ips(patches, output_path):
    ips = b"PATCH"
    for offset, _old, new in sorted(patches):
        ips += offset.to_bytes(3, "big") + len(new).to_bytes(2, "big") + new
    ips += b"EOF"
    Path(output_path).write_bytes(ips)
    print(f"✅ Parche IPS generado: {output_path}")


def generate_anticrash_rom(input_rom_path, output_rom_path, ips_path=None):
    data = Path(input_rom_path).read_bytes()

    md5_hash = hashlib.md5(data).hexdigest()
    if md5_hash != EXPECTED_MD5:
        print(f"⚠️  MD5 diferente al esperado.\n  Esperado: {EXPECTED_MD5}\n  Obtenido: {md5_hash}")
        cont = input("¿Continuar de todos modos? [y/N]: ")
        if cont.lower() != "y":
            print("Abortando.")
            return

    rom = bytearray(data)
    for offset, old, new in PATCHES:
        actual = bytes(rom[offset:offset + len(old)])
        if actual != old:
            print(f"❌ Bytes inesperados en 0x{offset:06X}: {actual.hex(' ')} (se esperaba {old.hex(' ')}). Abortando.")
            return
        rom[offset:offset + len(new)] = new

    Path(output_rom_path).write_bytes(rom)
    print(f"✅ ROM parcheada guardada como: {output_rom_path}")

    if ips_path:
        build_ips(PATCHES, ips_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aplica el parche Anticrash SRAM a la ROM de Traysia Shinyuden"
    )
    parser.add_argument(
        "input_rom",
        nargs="?",
        default="roms/Traysia (W).bin",
        help="Ruta a la ROM original",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_rom",
        default="roms/Traysia (W)_anticrash.bin",
        help="Ruta donde se escribirá la ROM parcheada",
    )
    parser.add_argument(
        "--ips",
        nargs="?",
        const=IPS_DEFAULT,
        default=None,
        help=f"Genera además el parche IPS (por defecto en {IPS_DEFAULT})",
    )
    args = parser.parse_args()

    generate_anticrash_rom(args.input_rom, args.output_rom, args.ips)
