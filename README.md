# 🧩 Traysia (Shinyuden Edition) – Fix Guardado y Análisis de Versiones

Este repositorio documenta y soluciona un bug crítico en la ROM de *Traysia* para Mega Drive distribuida por **Shinyuden**, y reúne herramientas de análisis utilizadas durante la investigación.

## 🐛 Bug de Guardado en Versión Shinyuden

Se ha detectado que la ROM distribuida por Shinyuden en reedición física del juego Traysia introduce **13 bytes adicionales** en cada slot de guardado de SRAM. Estos bytes contienen el texto `"_data "` con valores intercalados `0xFF`, lo que produce una estructura de guardado probablemente mayor a la esperada por el juego original (51 bytes).

### ❗ Reporte por TodoRPG
El usuario [TodoRPG](https://youtu.be/5akNdXm_BiM) experimentó un bug al salvar partida avanzada: la partida quedó corrupta y aparecieron textos en japonés y gráficos corruptos. Creemos que:

- El bug está relacionado con la escritura de datos inconsistentes al final del archivo .srm cuando se ejecuta en hardware real.

- El juego podría estar escribiendo metadatos no validados o datos mal inicializados en la zona extra de memoria, y luego accediendo a ellos sin control de integridad.

### 🔎 Análisis técnico
- Comparando la versión USA original con la versión Shinyuden (ya que ambos compoarten el sistema de guardado), los slots de guardado de la versión de Shinyuden tienen **13 bytes extra** al final.
- La ROM modifica las rutinas de guardado con respecto a la version USA e introduce el texto `"_data "` (intercalado con `0xFF`) justo después del bloque útil de datos. 
- Esto desborda la estructura esperada por el motor del juego, que no fue diseñado para manejar datos extra.

Ejemplo de los bytes extra:
```
FF 5F FF 64 FF 61 FF 74 FF 61 FF 20
```
→ Interpretado como: `_data `

### 🔬 Observaciones adicionales sobre SRAM

El archivo `.srm` generado desde un cartucho físico (Mega Sg FPGA) incluye múltiples bloques con la cadena `"SRAM_save_data"` a partir del byte 0x4000. Esta firma no aparece en los saves generados por emuladores (ej. Kega Fusion), donde el `.srm` ocupa 16 KB. Esto ocurre por que la PCB con 64 KB de SRAM simplemente rellena todo el espacio disponible, lo cual en realidad no deberia suponer un problema.

Lo interesante es que al comparar los `.srm` de las distintas versiones comprobamos que no son iguales. Esta observación revela que cada slot de guardado de la version Shinyuden ocupa **64 bytes**, frente a los **51 bytes** de las versiones USA y japonesa. Por lo tanto esto podria ser una posible causa del problema; probablemente el motor termina leyendo y escribiendo mas datos de los previstos en los slots, corrompiendo las partidas.

| Versión  | Tamaño por slot | Nº de slots | Tamaño habitual del `.srm` |
|---------|-----------------|------------|----------------------------|
| Japón   | 51 bytes        | 4          | 32 KB                       |
| USA     | 51 bytes        | 4          | 16 KB                       |
| Shinyuden | 64 bytes      | 4          | 16 KB en emulador / 64 KB en hardware |

Como se ve, el **tamaño total de 64 KB** en hardware se debe únicamente a que la placa detecta toda la SRAM disponible y la rellena por completo, algo normal en este tipo de memorias. El bug surge porque el juego usa estructuras de 64 bytes por slot, incompatibles con las rutinas heredadas que esperan 51 bytes. En emuladores como Kega Fusion, el archivo .srm generado es de solo 16 KB (como en la version USA).

### 🔍 Cómo se detectó el bug del guardado

Durante la investigación, utilizamos la herramienta srm_compare_util.py para comparar el archivo de guardado .srm dumpeado de la ROM de Shinyuden contra uno generado a partir de la ROM USA.

Ejemplo de uso:
```bash
python tools/srm_compare_util.py "Traysia (W).srm" "Traysia_USA_RealisticSave.srm"
```

Resultado detectado:
```bash
⚠️  Diferencias encontradas en el slot 1:
  Traysia (W).srm                → ... FF 5F FF 64 FF 61 FF 74 FF 61 FF 20 ...
  Traysia (USA).srm → ... FF FF FF FF FF FF FF FF FF FF FF FF ...
```

Los bytes adicionales "_data " intercalados con 0xFF en la versión Shinyuden no existen en la versión original. Esta anomalía provocaba que el guardado de partidas sobrescribiera datos fuera de su bloque asignado, corrompiendo partidas (especialmente en los slots más avanzados o múltiples).

Este análisis fue clave para identificar la rutina modificada en la ROM y desarrollar el parche de corrección.

---

## ✅ Solución aplicada: Parche IPS

Se ha creado un parche que elimina estos 13 bytes extra y restaura el comportamiento original.

📦 [`patches/Traysia_Shinyuden_ROM_nop_patch.ips`](patches/Traysia_Shinyuden_ROM_nop_patch.ips)

### 🔧 Cómo lo hace
- Localiza el bloque de código donde se escriben los datos `_data` en SRAM.
- Sustituye esas instrucciones por `NOPs` (`0x4E71`), que no afectan el resto del sistema de guardado.
- Esto restaura la estructura original de 51 bytes por slot.

Se comprobó que esta rutina se encuentra en el offset `0x1B520` de la ROM.
El offset `0x1FE50` corresponde a datos de la tabla de enemigos y no ejecuta instrucciones de guardado.

### 🧾 Cómo aplicar el parche
1. Abre **Lunar IPS** o cualquier herramienta compatible.
2. Selecciona `patches/Traysia_Shinyuden_ROM_nop_patch.ips` como parche.
3. Aplica sobre la ROM: `Traysia (W).bin`
4. Ejecuta la ROM parcheada en emulador, FPGA o flashcart (EverDrive, etc).

#### ⚙️ Generar la ROM parcheada directamente (Python)

Puedes usar el script `tools/fix_rom_traysia_shinyuden_nop.py` para crear una versión corregida de la ROM directamente a partir de `Traysia (W).bin`, sin necesidad de usar Lunar IPS:

```bash
python tools/fix_rom_traysia_shinyuden_nop.py
```

Este script corrige la rutina de guardado que añadía datos corruptos a cada slot de partida.


🔬 Estado: probado con partidas nuevas en el emulador KEGA Fusion y en un Flashcart de las mismas caracteristicas que el juego original en una Analogue Mega Sg (FPGA). Pendiente de validación con saves avanzados.

## 🩹 Arreglar archivos de guardado existentes

Si tienes saves creados con la ROM de Shinyuden, puedes repararlos con el parche [`patches/Traysia_Shinyuden_SRM_nop_patch.ips`](patches/Traysia_Shinyuden_SRM_nop_patch.ips), que elimina los bytes extra de cada slot.
Este parche se generó automáticamente con `tools/fix_save_ips_generator.py`, que guarda el archivo directamente en la carpeta `patches/` y reproduce exactamente la misma lógica que el script de reparación. Para recrearlo basta con ejecutar:
```bash
python tools/fix_save_ips_generator.py
```

También puedes usar el script `tools/fix_traysia_srm.py`:

```bash
python tools/fix_traysia_srm.py archivo.srm -o salida.srm
```

Si no indicas `-o`, se creará automáticamente `archivo_nop_patch.srm` con la estructura corregida.

### ℹ️ Tamaños habituales del archivo `.srm`
Dependiendo del dispositivo, los saves pueden medir **8 KB** (algunos emuladores antiguos) o **16 KB**/ **64 KB** en hardware real. El bug solo sucede, en principio, cuando se usa hardware real o FPGA (es decir, cuando la partida se salva en el cartucho)

Tanto el parche [`patches/Traysia_Shinyuden_SRM_nop_patch.ips`](patches/Traysia_Shinyuden_SRM_nop_patch.ips) como el script `fix_traysia_srm.py` funcionan con archivos de cualquier tamaño y solo modifican los primeros cuatro slots, pero solo es realmente efectivo cuando el srm es de 64 KB.

> Si el script muestra `archivo SRM no válido`, comprueba que el fichero tenga
> exactamente 8, 16 o 64 KB y no esté dañado ni comprimido.

🔬 Estado: Pendiente de validación con corruptos reales.

---

## 🔬 Análisis Comparativo de las Distintas Versiones de Traysia para Mega Drive

Análisis técnico detallado de las distintas versiones existentes del juego Traysia para Mega Drive/Genesis, incluyendo la versión japonesa original, su localización oficial, la adaptación para Evercade y la reciente traducción al castellano publicada por Shinyuden.

### 🔍 Comparación Técnica
 #### Cabecera de ROM
Las cabeceras son casi idénticas en todas las versiones, salvo por la fecha del copyright:
- Japón: (C)T-49 1991.DEC
- USA y posteriores: (C)T-49 1992.Jan

Ninguna ROM especifica región (J, U, E), lo que sugiere que se compiló sin ese metadato.

#### Hashes y Checksums
| Versión | MD5 (recorte) | Tamaño | Diferencias |
|---|---|---|---|
| Japón | `75d9...21b2b` | 1MB | - |
| USA | `98d9...a1af4` | 1MB | 870.000+ bytes distintos con respecto a Japón |
| Evercade | `9d83...ddaee` | 1MB | Solo 1.361 bytes diferentes respecto a USA |
| Español | `db15...60222` | 2MB | ROM expandida, texto y scripts reubicados |

#### Diferencias binaria directa
- Japón vs USA: 83% de la ROM es diferente. No es solo traducción, sino reestructuración profunda.
- USA vs Evercade: cambios mínimos (cabecera, firmas, compatibilidad).
- Japón vs Español: casi 2MB de diferencia total. Se expande la ROM, se reorganiza texto y se introducen scripts nuevos.

#### Tabla de Equivalencias
| Versión | Nombre de Archivo | Tamaño | Idioma | Deriva de | Cambios Principales |
|---|---|---|---|---|---|
| Minato no Traysia (Japón) | Minato no Traysia (Japan).md | 1MB | Japonés | Original | Versión base. Fecha interna: 1991.DEC |
| Traysia (USA) | Traysia (USA).md | 1MB | Inglés | Japonesa | Traducción oficial. Añade textos en inglés y ajustes en código |
| Traysia (Evercade) | Traysia (World) (Evercade).md | 1MB | Inglés | USA | Solo modifica metadatos. Compatibilidad Evercade |
| Traysia (Español – Shinyuden) | Traysia (W).bin | 2MB | Español | Japónesa | Traducción completa. ROM expandida, texto reorganizado |

#### Conclusiones de la Comparación
- La versión USA de Traysia no es solo una traducción: incluye ajustes profundos en el código.
- La versión Evercade parte de la USA y realiza cambios menores, probablemente solo en la cabecera.
- La versión en español de Shynyuden parte de la japonesa y expande la ROM a 2MB reales, reorganizando texto y posiblemente scripts. Es más, **la versión de Shinyuden incluye los textos originales en inglés de la versión USA**, con lo cual podría ser posible habilitar el cambio de idioma si encontramos la manera.
 - A partir de esta observación se ha añadido un script experimental (`switch_to_english.py`) que redirige los punteros del texto en castellano al bloque de diálogos en inglés. El script detecta referencias en varios formatos, incluidos punteros de 4 bytes desplazados (`0x10000000`). Por fiabilidad es recomendable indicar los offsets manualmente (`--spanish-offset 0x100000 --english-offset 0x7B706`). También permite copiar el bloque inglés sobre el castellano con la opción `--overwrite-spanish`, saltar la modificación de punteros con `--skip-pointers` y limitar el rango de búsqueda con `--search-start` y `--search-end`.
- También se incluye `dump_text_blocks.py` para listar los segmentos de texto en la ROM y localizar scripts ocultos. Permite ajustar la longitud mínima (`--min-len`), la anchura de las líneas (`--width 0` para no truncar), especificar un offset inicial (`--start`) y detectar caracteres extendidos con `--latin1`. El resultado indica además la longitud de cada bloque hallado.
- Para automatizar el proceso con todos los bloques, el script `batch_switch_to_english.py` lanza varias pasadas de `switch_to_english.py` usando los offsets descubiertos.
- Para traducir el juego a otro idioma se añade `translate_spanish.py`, que exporta todas las cadenas en castellano a un JSON editable y permite reinsertarlo tras la traducción. El script convierte los códigos de tildes (pares `0x81` seguidos de una letra, a veces en minúscula) en caracteres Unicode legibles, de modo que el traductor pueda editar el texto con normalidad.
- El análisis de diferencias mediante parches .IPS y comparación binaria es una herramienta fundamental para la preservación y documentación de estas versiones.

---

## 🛠️ Herramientas incluidas

Este repositorio incluye una descripción detallada de los scripts desarrollados para el análisis y validación. Puedes encontrar una descripción de cada una de las herramientas y scripts en este [README_tools.md](tools/README_tools.md)
### 📂 Organización de las ROMs
Guarda todas las ROMs en una carpeta llamada `roms/` ubicada en la raíz del repositorio. Tanto `tools/fix_rom_traysia_shinyuden_nop.py` como `tools/traysia_rom_analyzer.py` y otros scripts buscan los archivos directamente en esa ruta.
* **Traysia (W).bin**: Versión oficial editada y traducida al castellano por Shinyuden en 2025. 2MB. 
* **Traysia (World) (Evercade).md**: Reedición lanzada en 2022 por Blaze para Evercade y sistemas compatibles, incluido en el cartucho "Renovation Collection 1". 1MB. 
* **Traysia (USA).md**:  Traducción de la versión japonesa lanzada en Estados Unidos en abril de 1992. 
* **Minato no Traysia (Japan).md**:  versión original, lanzada en Japón en febrero de 1992.

---

## 📌 Cómo contribuir

Puedes ayudar:
- Verificando el parche en partidas reales avanzadas.
- Confirmando la estabilidad del fix en hardware real.
- Reportando cualquier regresión o incompatibilidad.
- Proponiendo mejoras o integraciones en los scripts.

---

## 🧠 Créditos y Licencia

- Investigación, análisis y parche por **@Arcanbytes**.
- Documentación generada con apoyo de herramientas propias.

Licencia: MIT – puedes usar, modificar y compartir este contenido libremente.

Si has detectado errores o quieres contribuir, puedes abrir un issue o forkear este repositorio.
