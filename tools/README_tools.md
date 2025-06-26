# 🛠️ Herramientas incluidas en TraysiaROMFix

Esta carpeta contiene scripts Python utilizados durante el análisis y corrección del bug de guardado en la ROM distribuida por Shinyuden.

> 🔗 Este contenido forma parte del repositorio [TraysiaROMAnalyzer](https://github.com/arcanbytes/TraysiaROMAnalyzer)

## 📄 Descripción de los scripts

### `fix_rom_traysia_shinyuden_nop.py`
Genera una versión corregida de `Traysia (W).bin` sustituyendo el bloque que añadía `_data` por instrucciones NOP (`0x4E71`). Equivale a aplicar el parche [`../patches/Traysia_Shinyuden_ROM_nop_patch.ips`](../patches/Traysia_Shinyuden_ROM_nop_patch.ips).

#### Uso

positional arguments:
  input_rom             Ruta a la ROM original

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT_ROM
                        Ruta donde se escribirá la ROM parcheada

```bash
python tools/fix_rom_traysia_shinyuden_nop.py (usara las roms definidas por defecto de la carpeta roms)
or
python tools\fix_rom_traysia_shinyuden_nop.py -o "roms/Traysia (W)_nop_patch.bin" "roms/Traysia (W).bin" 
```


---

### `fix_traysia_srm.py`
Corrige directamente un archivo `.srm`. Equivale a aplicar el parche [../patches/Traysia_Shinyuden_SRM_nop_patch.ips](../patches/Traysia_Shinyuden_SRM_nop_patch.ips).

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

---

### `switch_to_english.py`

Script experimental para reemplazar los punteros del texto en castellano por los de la versión en inglés incluida dentro de `Traysia (W).bin`.
Detecta referencias en varios formatos: direcciones de 3 y 4 bytes (big/little endian), palabras separadas `hi/lo` y punteros de 4 bytes desplazados ocho bits (como `0x10000000`). También corrige instrucciones `LEA`.
La detección automática de offsets es muy imprecisa, por lo que se recomienda indicar de forma explícita `--spanish-offset 0x100000 --english-offset 0x7B706`.
Opcionalmente puede copiar el texto inglés sobre el castellano usando `--overwrite-spanish`.
Es posible limitar la búsqueda de punteros con `--search-start` y `--search-end` para evitar reemplazos masivos que dañen otros datos. También se puede saltar la fase de reemplazo y únicamente copiar el bloque inglés con `--skip-pointers`.

#### Uso

```bash
python tools/switch_to_english.py -o "roms/Traysia (W)_english.bin" "roms/Traysia (W).bin"
# offsets personalizados (hex)
python tools/switch_to_english.py --spanish-offset 0x100000 --english-offset 0x7B706 "roms/Traysia (W).bin"
# sobrescribir texto en lugar de cambiar punteros
python tools/switch_to_english.py --overwrite-spanish "roms/Traysia (W).bin"
# copiar texto sin modificar punteros
python tools/switch_to_english.py --skip-pointers --overwrite-spanish "roms/Traysia (W).bin"
```

Redirige todas las referencias al bloque de diálogos en castellano (por defecto `0x100000`) al comienzo del texto en inglés (`0x07B706`). Si se usa `--overwrite-spanish`, copia el texto inglés sobre el castellano usando el rango por defecto hasta `0x0937C4`. Con `--search-start` y `--search-end` puedes limitar el rango de búsqueda de punteros. El script contabiliza por separado cada formato sustituido para facilitar la verificación.

---

### `batch_switch_to_english.py`

Pequeño lanzador que aplica `switch_to_english.py` sobre varios bloques de texto.
Los offsets se calcularon con `dump_text_blocks.py` y permiten obtener una ROM en inglés en una sola pasada.

```bash
python tools/batch_switch_to_english.py
# o copiando el texto en lugar de solo redirigir punteros
python tools/batch_switch_to_english.py --overwrite-spanish
```

### `dump_text_blocks.py`

Explora una ROM y muestra todos los bloques de texto ASCII detectados con su offset.
Útil para localizar scripts ocultos o segmentados.

#### Uso
```bash
python tools/dump_text_blocks.py roms/Traysia\ \(W\).bin > text_blocks.txt
# mostrar bloques completos
python tools/dump_text_blocks.py --width 0 roms/Traysia\ \(W\).bin
# detectar caracteres acentuados (Latin-1)
python tools/dump_text_blocks.py --latin1 roms/Traysia\ \(W\).bin
# empezar en un offset concreto y mostrar la longitud de cada bloque
python tools/dump_text_blocks.py --start 0x100000 roms/Traysia\ \(W\).bin
```
Puedes ajustar la longitud mínima de texto con `--min-len 30`, limitar los caracteres por línea con `--width` (0 para no truncar) y desplazar el inicio de búsqueda con `--start`. Con `--latin1` se muestran también caracteres extendidos para localizar texto con tildes. El script indica la longitud de cada bloque detectado para ayudar a delimitar secciones.

