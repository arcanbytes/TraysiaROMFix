import json
from pathlib import Path

spanish_path = Path("translations/spanish.json")
german_path = Path("translations/german.json")

es_data = json.loads(spanish_path.read_text(encoding="utf-8"))
de_data = json.loads(german_path.read_text(encoding="utf-8"))

if len(es_data) != len(de_data):
    raise SystemExit("❌ Los archivos no tienen la misma cantidad de entradas.")

for es, de in zip(es_data, de_data):
    de["text_source"] = es["text"]

german_path.write_text(json.dumps(de_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✔ Añadido 'text_source' a {len(de_data)} entradas en german.json")
