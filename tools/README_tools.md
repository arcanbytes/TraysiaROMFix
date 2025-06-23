
# 🛠️ Herramientas incluidas en TraysiaROMFix

Esta carpeta contiene scripts Python utilizados durante el análisis y corrección del bug de guardado en la ROM distribuida por Shinyuden.

## 📄 Descripción de los scripts

### `fix_rom_traysia_shinyuden.py`

Corrige la ROM original de Shinyuden (`Traysia (W).bin`) eliminando el patrón corrupto `"_data "` intercalado con `0xFF` que se añade al final de cada slot de guardado.

💡 Útil si prefieres trabajar directamente con la ROM en vez de aplicar un parche `.ips`.

### `fix_traysia_srm.py`
Corrige directamente un archivo `.srm` sin necesidad de usar Lunar IPS.

💡 Útil para validar partidas antiguas o reparar archivos de cartuchos físicos directamente en vez de aplicar un parche `.ips`.


---

### `traysia_rom_analyzer.py`
Analiza y compara versiones de la ROM de Traysia.
- Extrae cabeceras, detecta diferencias binarias, y genera un resumen por versión.

### `srm_compare_util.py`
Compara dos archivos `.srm` mostrando diferencias byte a byte por slot.
- Identifica saves corruptos o estructuras alteradas.
- Útil para detectar rutinas defectuosas de guardado.

### `fix_save_ips_generator.py`
Genera el parche `.ips` para corregir archivos `.srm` afectados. (puedes usar Lunar IPS en su lugar)
- Aplica reemplazo de 13 bytes extra por `0xFF` en cada slot.


### `Traysia_Shinyuden_RemoveExtraSaveData.py`
Script que genera el parche `.ips` que corrige la ROM modificada por Shinyuden (puedes usar Lunar IPS en su lugar)


