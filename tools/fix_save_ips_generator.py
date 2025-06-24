
# El parche sustituye los 13 bytes extra que la ROM Shinyuden inserta al final
# de cada slot de guardado. Los datos incorrectos comienzan en el byte 51 de
# cada bloque de 64 bytes, por lo que las posiciones a modificar son 51, 115,
# 179 y 243. Todas se rellenan con `0xFF` para restaurar el formato original.

def create_ips_patch_for_srm_fix(output_path="patches/Traysia_Shinyuden_SRM_nop_patch.ips"):
    output = bytearray()
    output += b'PATCH'

    for slot_index in range(4):
        slot_offset = slot_index * 64
        start_patch = slot_offset + 51  # Donde comienzan los 13 bytes adicionales
        patch_length = 13

        # Insertar offset y datos a reemplazar (0xFF)
        output += start_patch.to_bytes(3, 'big')
        output += patch_length.to_bytes(2, 'big')
        output += bytes([0xFF] * patch_length)

    output += b'EOF'

    with open(output_path, "wb") as f:
        f.write(output)

    print(f"✅ Parche IPS generado: {output_path}")

if __name__ == "__main__":
    create_ips_patch_for_srm_fix()
