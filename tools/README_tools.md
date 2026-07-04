# 🛠️ Herramientas incluidas en TraysiaROMFix

Esta carpeta contiene los scripts estables del proyecto: el parche **Anticrash SRAM** y el analizador de versiones de la ROM.

> 🔗 Las herramientas experimentales de traducción y cambio de idioma están en [`../translation-tools/`](../translation-tools/README.md).

## 📄 Descripción de los scripts

### `fix_rom_traysia_shinyuden_anticrash.py`
Aplica el parche **Anticrash SRAM** a `Traysia (W).bin`. Redirige las 15 rutas de error heredadas del monitor de depuración (14 stubs de excepción de CPU + el guard del streamer de texto) que en la ROM de Shinyuden acaban ejecutando la ventana de SRAM (`$200000`), convirtiéndolas en un reinicio limpio o un fin de cadena seguro. Equivale a aplicar el parche [`../patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips`](../patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips). Ver el [README principal](../README.md) para el análisis técnico completo.

El script comprueba el MD5 de la ROM de entrada y verifica los bytes originales de cada punto antes de modificarlos: si la ROM no coincide con lo esperado, aborta sin escribir nada.

#### Uso

positional arguments:
  input_rom             Ruta a la ROM original

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT_ROM
                        Ruta donde se escribirá la ROM parcheada
  --ips [IPS]           Genera además el parche IPS en patches/

```bash
# usa las rutas por defecto de la carpeta roms/
python tools/fix_rom_traysia_shinyuden_anticrash.py

# regenerando también el parche IPS
python tools/fix_rom_traysia_shinyuden_anticrash.py --ips

# rutas personalizadas
python tools/fix_rom_traysia_shinyuden_anticrash.py -o "roms/Traysia (W)_anticrash.bin" "roms/Traysia (W).bin"
```

---

### `traysia_rom_analyzer.py`

Un script en Python para comparar y analizar distintas versiones del juego *Traysia* para Sega Mega Drive / Genesis.

#### ¿Qué hace?
- Extrae y muestra la cabecera estándar de la ROM (0x100-0x1FF): nombres doméstico/internacional, copyright, número de serie, checksum, región y el rango de SRAM declarado
- Calcula hashes MD5 y SHA1
- Compara binariamente dos ROMs e identifica diferencias

#### Uso
Coloca las ROMs en la carpeta `roms/` de la raíz del repositorio, con los siguientes nombres:
```
Minato no Traysia (Japan).md
Traysia (USA).md
Traysia (World) (Evercade).md
Traysia (W).bin
```
```bash
python tools/traysia_rom_analyzer.py
```

Ninguno de estos scripts necesita dependencias externas: solo usan la librería estándar de Python.
