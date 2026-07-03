import json
from pathlib import Path

# Rutas de los archivos
legacy_path = Path("translations/german.json")         # Archivo con las traducciones previas
new_path = Path("translations/spanish.json")          # Archivo nuevo con text_source y offset_hex
output_path = Path("translations/german_updated.json") # Archivo de salida combinado

# Cargar datos
old_data = json.loads(legacy_path.read_text(encoding="utf-8"))
new_data = json.loads(new_path.read_text(encoding="utf-8"))

# Crear mapas por offset
old_by_offset = {entry["offset"]: entry for entry in old_data}
new_by_offset = {entry["offset"]: entry for entry in new_data}

# Mezclar los datos por coincidencia de offset
merged = []
for offset, new_entry in new_by_offset.items():
    merged_entry = new_entry.copy()
    if offset in old_by_offset:
        old_entry = old_by_offset[offset]
        for key in ("text_translator", "text", "review"):
            if key in old_entry:
                merged_entry[key] = old_entry[key]
    merged.append(merged_entry)

# Guardar el resultado
output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✔ Archivo combinado guardado como {output_path.name}")
