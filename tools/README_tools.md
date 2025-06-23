# 🛠️ Herramientas incluidas en TraysiaROMFix

Esta carpeta contiene scripts Python utilizados durante el análisis y corrección del bug de guardado en la ROM distribuida por Shinyuden.

## 📄 Descripción de los scripts

### `fix_rom_traysia_shinyuden_nop.py`
Genera una versión corregida de `Traysia (W).bin` sustituyendo el bloque que añadía `_data` por instrucciones NOP (`0x4E71`). Equivale a aplicar el parche [`../patches/Traysia_Shinyuden_ROM_nop_patch.ips`](../patches/Traysia_Shinyuden_ROM_nop_patch.ips).

### `fix_rom_ips_generator.py`
Pequeña utilidad para crear un parche IPS a partir de la ROM original y su versión modificada. Se usó para generar `../patches/Traysia_Shinyuden_ROM_nop_patch.ips`.

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
Genera el parche `.ips` para corregir archivos `.srm` afectados (puedes usar Lunar IPS en su lugar).
- Aplica reemplazo de 13 bytes extra por `0xFF` en cada slot.
- El parche resultante se incluye como [`../patches/FixSave_TraysiaShinyuden_RemoveExtraSaveBytes.ips`](../patches/FixSave_TraysiaShinyuden_RemoveExtraSaveBytes.ips).
