# 🧩 Traysia (Shinyuden Edition) – Fix Guardado y Análisis de Versiones

Este repositorio documenta y soluciona un bug crítico en la ROM de *Traysia* para Mega Drive distribuida por **Shinyuden**, y reúne herramientas de análisis utilizadas durante la investigación.

---

## 🐛 Bug de Guardado en Versión Shinyuden

Se ha detectado que la ROM distribuida por Shinyuden introduce **13 bytes adicionales** en cada slot de guardado de SRAM. Estos bytes contienen el texto `"_data "` con valores intercalados `0xFF`, lo que produce una estructura de guardado mayor a la esperada por el juego original (51 bytes).

### ❗ Reporte por TodoRPG
El usuario [TodoRPG](https://youtu.be/5akNdXm_BiM) experimentó un bug al salvar partida avanzada: la partida quedó corrupta y aparecieron textos en japonés y gráficos corruptos. Creemos que:

- El bug está relacionado con la escritura de datos inconsistentes al final del archivo .srm cuando se ejecuta en hardware real.

- Este error no se reproduce fácilmente en emuladores porque estos limitan el acceso a 16 KB de SRAM.

- El juego podría estar escribiendo metadatos no validados o datos mal inicializados en la zona extra de memoria, y luego accediendo a ellos sin control de integridad.

### 🔎 Análisis técnico
- Comparando la versión USA original con la versión Shinyuden, los slots de guardado tienen **13 bytes extra** al final.
- La ROM modifica las rutinas de guardado e introduce el texto `"_data "` (intercalado con `0xFF`) justo después del bloque útil de datos.
- Esto desborda la estructura esperada por el motor del juego, que no fue diseñado para manejar datos extra.

Ejemplo de los bytes extra:
```
FF 5F FF 64 FF 61 FF 74 FF 61 FF 20
```
→ Interpretado como: `_data `

### 🔬 Observaciones adicionales sobre SRAM

El archivo `.srm` generado desde un cartucho físico (Mega Sg FPGA) incluye múltiples bloques con la cadena `"SRAM_save_data"` a partir del byte 0x4000. Esta firma no aparece en los saves generados por emuladores (ej. Kega Fusion), donde el `.srm` ocupa 16 KB.

Esto sugiere que la ROM de Shinyuden está escribiendo fuera del rango habitual de los 4 slots válidos (cada uno de 64 bytes), introduciendo metadatos no esperados en zonas de la SRAM. Esta diferencia puede ser clave para explicar la corrupción de partidas en fases avanzadas del juego, como han reportado algunos jugadores.

### 🧠 Uso de SRAM Expandida en Hardware Real

Durante el análisis de la ROM Traysia (W).bin distribuida por Shinyuden, se detectó que el juego accede a regiones de SRAM superiores a 0x6000, lo cual excede el rango habitual de 16 KB (hasta 0x5FFF) utilizado por la mayoría de juegos de Mega Drive. Entre las direcciones detectadas están:
```
0x7FFF, 0x8000, 0xA000, 0xB000, 0xC000, 0xD000, 0xE000, 0xF000
```

Esto confirma el uso activo de 64 KB de SRAM cuando la ROM se ejecuta en hardware compatible (como ciertas PCBs clonadas disponibles en Aliexpress), entre ellas: 🔗 [Ejemplo de PCB utilizada por Shinyuden](https://es.aliexpress.com/item/1005007209715227.html)

### 🧪 Diferencias entre Hardware Real y Emulación
- En emuladores como Kega Fusion, el archivo .srm generado es de solo 16 KB, y el juego guarda correctamente.

- En hardware real con cartucho físico, el .srm puede ocupar 64 KB, con datos adicionales en los últimos 48 KB.

- Este comportamiento sugiere que el juego detecta si se ejecuta en hardware real, y expande la estructura de guardado automáticamente, quizás por una lógica heredada o modificada respecto a las versiones anteriores.


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

### 📂 Organización de las ROMs
Guarda todas las ROMs en una carpeta llamada `roms/` ubicada en la raíz del repositorio. Tanto `tools/fix_rom_traysia_shinyuden_nop.py` como `tools/traysia_rom_analyzer.py` y otros scripts buscan los archivos directamente en esa ruta.
* **Traysia (W).bin**: Versión oficial editada y traducida al castellano for Shynyuden en 2025. 2MB. 
* **Traysia (World) (Evercade).md**: Reedición lanzada en 2022 por Blaze para Evercade y sistemas compatibles, incluido en el cartucho "Renovation Collection 1". 1MB. 
* **Traysia (USA).md**:  Traduccion de la version japonesa lanzada en Estados Unidos en  Abril de 1992. 
* **Minato no Traysia (Japan).md**:  Version original, lanzada en Japon en Febrero de 1992.


---

## 🛠️ Herramientas incluidas

Este repositorio incluye una descripción detallada de los scripts desarrollados para el análisis y validación. Puedes encontrar una dfescripción de cada una de las herramientas y scripts en este [README_tools.md](tools/README_tools.md)

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