# translate_spanish_to_german.py

Herramienta CLI para traducir textos de juegos retro desde un archivo `spanish.json` a otro idioma (`german.json`, `english.json`...), respetando restricciones de longitud y formato específico del juego Traysia. Estado: Work in Progress.

## Características

- Traducción automática usando `googletrans`, `deepl` o `argos`.
- Idioma de destino seleccionable con `--target de|en` (por defecto: `de`).
- Interrupción segura con `Ctrl+C`, guardado automático con `--save-every`.
- Formateo que respeta los saltos de línea `@` y mayúsculas.
- Transliteración alemana automática (`ä → ae`...) solo cuando `--target de`, ya que la fuente de Traysia no incluye esos glifos.
- Validación automática de errores de formato (`@@`, palabras mal segmentadas, `@` sin espacio...).
- Modos independientes: `translate`, `format`, `check`.

## Requisitos

- Python 3.10+
- Paquetes:
  ```bash
  pip install -r translation-tools/requirements.txt
  ```
  Esto instala `tqdm`; el motor de traducción se instala aparte según el proveedor elegido (ver comentarios del propio `requirements.txt`).

## Uso

### Traducción
```bash
# a alemán (por defecto)
python translation-tools/translate_spanish_to_german.py translations/spanish.json translations/german.json --provider googletrans --save-every 25
# a inglés
python translation-tools/translate_spanish_to_german.py translations/spanish.json translations/english.json --target en --provider googletrans
```

### Formateo
```bash
python translation-tools/translate_spanish_to_german.py translations/spanish.json translations/german.json --mode format
```

### Validación de formato
```bash
python translation-tools/translate_spanish_to_german.py translations/spanish.json translations/german.json --mode check
```

## Notas

- `spanish.json` debe contener las claves `offset`, `length`, y `text`.
- La salida (`german.json`) tendrá `text_translator` con la traducción, y `text` con la versión ajustada que cabe en la ROM.
- Las líneas con problemas son marcadas con `"review": true`.

---

© 2025 — Proyecto Traysia ROM Fix
