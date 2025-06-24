# 🛠️ Herramientas incluidas en TraysiaROMFix

Esta carpeta contiene scripts Python utilizados durante el análisis y corrección del bug de guardado en la ROM distribuida por Shinyuden.

> 🔗 Este contenido forma parte del repositorio [TraysiaROMAnalyzer](https://github.com/arcanbytes/TraysiaROMAnalyzer)

## 📄 Descripción de los scripts

### `fix_rom_traysia_shinyuden_nop.py`
Genera una versión corregida de `Traysia (W).bin` sustituyendo el bloque que añadía `_data` por instrucciones NOP (`0x4E71`). Equivale a aplicar el parche [`../patches/Traysia_Shinyuden_ROM_nop_patch.ips`](../patches/Traysia_Shinyuden_ROM_nop_patch.ips).

---

### `fix_traysia_srm.py`
Corrige directamente un archivo `.srm`. Equivale a aplicar el parche [`../patches/Traysia_Shinyuden_SRM_nop_patch.ips`](../patches/Traysia_Shinyuden_SRM_nop_patc.ips).

---

### `traysia_rom_analyzer.py`

Un script en Python para comparar y analizar distintas versiones del juego *Traysia* para Sega Mega Drive / Genesis. 

#### ¿Qué hace?
- Extrae y muestra la cabecera de la ROM (título, región, checksum...)
- Calcula hashes MD5 y SHA1
- Compara binariamente dos ROMs e identifica diferencias

#### Uso
Coloca tus ROMs `.md` o `.bin` en el mismo directorio del script, con los siguientes nombres:
```
Minato no Traysia (Japan).md
Traysia (USA).md
Traysia (World) (Evercade).md
Traysia (W).bin
```
---

### `srm_compare_util.py`

Utilidad para comparar estructuras `.srm` mostrando diferencias byte a byte, permitiendo detectar diferencias por slot de guardado.

#### ¿Qué hace?
- Carga dos archivos `.srm`. 
- Divide cada archivo en bloques de 64 bytes (1 por slot)
- Compara los primeros 51 bytes reales de cada bloque y muestra diferencias

#### Uso
```bash
python srm_compare_util.py archivo1.srm archivo2.srm
```

Esta herramienta fue clave para identificar las diferencias en los datos guardados generados por la ROM de Shinyuden.

---

### `fix_rom_ips_generator.py`
Pequeña utilidad para crear un parche IPS a partir de la ROM original y su versión modificada. Se usó para generar `../patches/Traysia_Shinyuden_ROM_nop_patch.ips`.

---

### `fix_save_ips_generator.py`
Genera el parche `.ips` para corregir archivos `.srm` afectados. Se usó para generar `../patches/Traysia_Shinyuden_SRM_nop_patch.ips`. 