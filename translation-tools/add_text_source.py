import json
import sys
from pathlib import Path

# Evita errores de codificacion en consolas que no son UTF-8 (p.ej. cp1252)
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

spanish_path = Path("translations/spanish.json")
german_path = Path("translations/german.json")

for p in (spanish_path, german_path):
    if not p.exists():
        raise SystemExit(f"❌ No se encuentra {p}. Ejecuta el script desde la raíz del repositorio.")

es_data = json.loads(spanish_path.read_text(encoding="utf-8"))
de_data = json.loads(german_path.read_text(encoding="utf-8"))

if len(es_data) != len(de_data):
    raise SystemExit("❌ Los archivos no tienen la misma cantidad de entradas.")

for es, de in zip(es_data, de_data):
    de["text_source"] = es["text"]

german_path.write_text(json.dumps(de_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✔ Añadido 'text_source' a {len(de_data)} entradas en german.json")
