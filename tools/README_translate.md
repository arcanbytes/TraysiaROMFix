# translate_spanish_to_german.py

Herramienta CLI para traducir textos de juegos retro desde un archivo `spanish.json` a `german.json`, respetando restricciones de longitud y formato específico del juego Traysia. Estado: Work in Progress.

## Características

- Traducción automática usando `googletrans`, `deepl` o `argos`.
- Interrupción segura con `Ctrl+C`, guardado automático con `--save-every`.
- Formateo que respeta los saltos de línea `@` y mayúsculas.
- Validación automática de errores de formato (`@@`, palabras mal segmentadas, `@` sin espacio...).
- Modos independientes: `translate`, `format`, `check`.

## Requisitos

- Python 3.8+
- Paquetes:
  ```bash
  pip install -r requirements.txt
  ```

## Uso

### Traducción
```bash
python translate_spanish_to_german.py translations/spanish.json translations/german.json --mode translate --provider googletrans --save-every 25
```

### Formateo
```bash
python translate_spanish_to_german.py translations/spanish.json translations/german.json --mode format
```

### Validación de formato
```bash
python translate_spanish_to_german.py translations/spanish.json translations/german.json --mode check
```

## Notas

- `spanish.json` debe contener las claves `offset`, `length`, y `text`.
- La salida (`german.json`) tendrá `text_translator` con la traducción, y `text` con la versión ajustada que cabe en la ROM.
- Las líneas con problemas son marcadas con `"review": true`.

---

© 2025 — Proyecto Traysia ROM Fix
