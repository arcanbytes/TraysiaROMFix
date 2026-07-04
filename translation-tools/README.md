# 🌐 Herramientas de traducción y cambio de idioma (experimentales)

> ⚠️ **Estado: Work in Progress.** Los scripts de esta carpeta son tentativos y no están completamente desarrollados ni validados. Son independientes del parche **Anticrash SRAM** (que vive en [`../tools/`](../tools/README_tools.md) y [`../patches/`](../patches/)): puedes usar el parche sin tocar nada de esta carpeta.

La ROM de Shinyuden contiene, además del guion en castellano, los textos originales en inglés de la versión USA. Estas herramientas exploran dos vías:

1. **Cambio de idioma a inglés** (`switch_to_english.py`, `batch_switch_to_english.py`): re-apuntar o sobreescribir los bloques de texto castellanos con los ingleses ya presentes en la ROM.
2. **Traducción a otros idiomas** (`translate_spanish*.py`): exportar el guion a JSON, traducirlo (automática o manualmente) y reinsertarlo respetando las longitudes originales. Con este flujo se generaron las pruebas `Traysia (EN).bin` y `Traysia (DE).bin`.

Documentación complementaria:
- [README_translate.md](README_translate.md) — detalle del traductor automático `translate_spanish_to_german.py`
- [TUTORIAL_translate.md](TUTORIAL_translate.md) — flujo de trabajo completo paso a paso

Los scripts asumen que se ejecutan desde la **raíz del repositorio** (buscan `roms/` y `translations/` relativas a ella).

## 📄 Descripción de los scripts

### `switch_to_english.py`

Script experimental para reemplazar los punteros del texto en castellano por los de la versión en inglés incluida dentro de `Traysia (W).bin`.
Detecta referencias en varios formatos: direcciones de 3 y 4 bytes (big/little endian) y punteros de 4 bytes desplazados ocho bits (como `0x10000000`). También corrige instrucciones `LEA` (contabilizadas por separado como `leaN`).
Cuando un patrón es poco distintivo (casi todo ceros, como ocurre con el offset `0x100000`) y produce muchos reemplazos, el script avisa de posibles falsos positivos; en ese caso conviene limitar el rango con `--search-start`/`--search-end`.
La detección automática de offsets es muy imprecisa, por lo que se recomienda indicar de forma explícita `--spanish-offset 0x100000 --english-offset 0x7B706`.
Opcionalmente puede copiar el texto inglés sobre el castellano usando `--overwrite-spanish`.
Es posible limitar la búsqueda de punteros con `--search-start` y `--search-end` para evitar reemplazos masivos que dañen otros datos. También se puede saltar la fase de reemplazo y únicamente copiar el bloque inglés con `--skip-pointers`.

#### Uso

```bash
python translation-tools/switch_to_english.py -o "roms/Traysia (W)_english.bin" "roms/Traysia (W).bin"
# offsets personalizados (hex)
python translation-tools/switch_to_english.py --spanish-offset 0x100000 --english-offset 0x7B706 "roms/Traysia (W).bin"
# sobrescribir texto en lugar de cambiar punteros
python translation-tools/switch_to_english.py --overwrite-spanish "roms/Traysia (W).bin"
# copiar texto sin modificar punteros
python translation-tools/switch_to_english.py --skip-pointers --overwrite-spanish "roms/Traysia (W).bin"
```

Redirige todas las referencias al bloque de diálogos en castellano (por defecto `0x100000`) al comienzo del texto en inglés (`0x07B706`). Si se usa `--overwrite-spanish`, copia el texto inglés sobre el castellano usando el rango por defecto hasta `0x0937C4`. Con `--search-start` y `--search-end` puedes limitar el rango de búsqueda de punteros. El script contabiliza por separado cada formato sustituido para facilitar la verificación. Estado actual: Work in Progress.

---

### `batch_switch_to_english.py`

Pequeño lanzador que aplica `switch_to_english.py` sobre varios bloques de texto.
Los offsets se calculan/deducen con `dump_text_blocks.py` y permiten obtener una ROM en inglés en una sola pasada. Cada bloque define además su `length` (la capacidad del bloque en castellano): con `--overwrite-spanish` nunca se copian más bytes que eso, de modo que el texto inglés no pisa los datos adyacentes. Los archivos intermedios `.tmpN` se eliminan automáticamente al terminar. Estado actual: Work in Progress.

```bash
python translation-tools/batch_switch_to_english.py
# o copiando el texto en lugar de solo redirigir punteros
python translation-tools/batch_switch_to_english.py --overwrite-spanish
# rutas personalizadas
python translation-tools/batch_switch_to_english.py -o "roms/Traysia (W)_english.bin" "roms/Traysia (W).bin"
```

---

### `dump_text_blocks.py`

Explora una ROM y muestra todos los bloques de texto ASCII detectados con su offset. Permite ajustar la longitud mínima (`--min-len`), la anchura de las líneas (`--width 0` para no truncar), especificar un offset inicial (`--start`) y detectar caracteres extendidos con `--latin1`. El resultado indica además la longitud de cada bloque hallado. Útil para localizar scripts ocultos o segmentados.

#### Uso
```bash
python translation-tools/dump_text_blocks.py "roms/Traysia (W).bin" > .temp/text_blocks.txt
# mostrar bloques completos
python translation-tools/dump_text_blocks.py --width 0 "roms/Traysia (W).bin"
# detectar caracteres acentuados (Latin-1)
python translation-tools/dump_text_blocks.py --latin1 "roms/Traysia (W).bin"
# empezar en un offset concreto y mostrar la longitud de cada bloque
python translation-tools/dump_text_blocks.py --start 0x100000 "roms/Traysia (W).bin"
#
python translation-tools/dump_text_blocks.py --width 0 --latin1 --start 0x000000 "roms/Traysia (W).bin" > .temp/text_blocks.txt
```

---

### `translate_spanish.py`

Herramienta para extraer el texto en castellano a un fichero JSON y volver a insertarlo una vez traducido.

Permite preparar una plantilla para traducir a otro idioma (por ejemplo, alemán) y reescribir el bloque de texto de la ROM con la traducción.

El script interpreta los caracteres acentuados que la ROM almacena como
secuencias `0x81 + letra` y los muestra en el JSON con tildes normales
(á, é, í, ó, ú, ñ, etc.). Las mayúsculas acentuadas usan la segunda letra
en minúscula: `0x81i → Á`, `0x81j → É`, `0x81k → Í`, `0x81l → Ó`,
`0x81m → Ú`, `0x81n → Ñ` (asignación verificada contra los textos reales
de la ROM: "Él", "Ámbar", "Ígnea", "Ópalo"...).
Al importar, la codificación inversa se aplica automáticamente, por lo que el
traductor puede editar el texto sin preocuparse por estos códigos. La
exportación seguida de importación sin cambios reproduce la ROM byte a byte.
Por defecto la importación translitera los caracteres alemanes (`ä → ae`...)
porque la fuente de Traysia no incluye esos glifos; puede desactivarse con
`--no-translit`.

#### Uso

```bash
# extraer las cadenas (por defecto los bloques conocidos de la ROM)
python translation-tools/translate_spanish.py export "roms/Traysia (W).bin" spanish.json

# editar `spanish.json` para obtener german.json con la traducción y volver a insertarla
python translation-tools/translate_spanish.py import "roms/Traysia (W).bin" german.json "roms/Traysia (DE).bin"
```

Los offsets y el rango pueden ajustarse con `--start` y `--end` en el modo `export`. El script mantiene la longitud original de cada cadena (incluyendo el byte nulo final), por lo que la traducción no debe superar ese límite.

---

### `translate_spanish_checkfit.py`

Verifica que cada cadena traducida de un JSON cabe en el espacio reservado en la ROM, con el mismo criterio que usa `translate_spanish.py import`. Devuelve código de salida 1 si alguna cadena no cabe (útil en scripts).

```bash
python translation-tools/translate_spanish_checkfit.py translations/german.json
# si se importó con --no-translit, medir igual:
python translation-tools/translate_spanish_checkfit.py translations/german.json --no-translit
```

---

### `add_text_source.py` y `merge_translation_fields.py`

Pequeños ayudantes del flujo de traducción (rutas fijas en `translations/`):

- `add_text_source.py` copia el texto español original al campo `text_source` de `german.json`, para que el revisor vea el original junto a la traducción.
- `merge_translation_fields.py` combina un `german.json` antiguo con un `spanish.json` reexportado, conservando `text_translator`, `text` y `review` por offset, y genera `german_updated.json`.

---

### `requirements.txt`

Dependencias del flujo de traducción (`pip install -r translation-tools/requirements.txt`). Solo instala `tqdm`; el motor de traducción (`googletrans`, `deepl` o `argostranslate`) se instala aparte según el proveedor que se vaya a usar (ver comentarios del propio archivo). El resto de scripts solo usan la librería estándar de Python.
