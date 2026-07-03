#!/usr/bin/env python3
"""translate_spanish_to_german.py  – v0.8  (jun‑2025)

▪ Traduce un archivo spanish.json (formato ROM) a alemán con uno de
  tres motores: googletrans (por defecto), DeepL o Argos Translate.

▪ Mantiene la estructura: offset y length no cambian nunca.
  – Si la traducción excede length → se recorta con “[…]” y se marca
    "review": true para revisión humana.

▪ Guarda dos campos por entrada:
    - text_translator  →  salida cruda del motor
    - text             →  versión formateada (mayúsculas, paddings “@”)

▪ Autoguarda cada N frases (--save-every, 25 por defecto) y permite
  reanudar con --resume (salta frases que ya tengan text_translator).

▪ Ajusta automáticamente la pausa entre peticiones (0.25 – 8 s) según
  la latencia media de las últimas 20 respuestas.

Uso:
    # primera pasada
    python translate_spanish_to_german.py spanish.json german.json --save-every 10

    # reanudar o cambiar de proveedor
    python translate_spanish_to_german.py spanish.json german.json --provider argos --resume
"""

from __future__ import annotations
import argparse, json, random, re, time
from collections import deque
from pathlib import Path
from typing import Optional
from translate_spanish import encode_custom, transliterate_de

# ──────────────────────────  Motores de traducción  ──────────────────────────
class BaseTranslator:
    def translate(self, text: str) -> str: ...

# Google (web‑scraper)
class GoogleTransTranslator(BaseTranslator):
    def __init__(self):
        from googletrans import Translator
        self.t = Translator(service_urls=[
            "translate.googleapis.com",
            "translate.google.com",
            "translate.google.de",
            "translate.google.es",
        ])
        # Parche pequeño: la lib. usa un atributo mal nombrado
        if not hasattr(self.t, "raise_Exception"):
            self.t.raise_Exception = getattr(self.t, "raise_exception", True)
    def translate(self, text: str) -> str:
        #return self.t.translate(text, dest="de").text # ← Para traducir al aleman
        return self.t.translate(text, dest="en").text  # ← ← Para traducir al ingles

# DeepL (requiere API key)
class DeeplTranslator(BaseTranslator):
    def __init__(self, api_key: str):
        import deepl
        self.t = deepl.Translator(api_key)
    def translate(self, text: str) -> str:
        #return self.t.translate_text(text, target_lang="DE").text  # ← Para traducir al aleman
        return self.t.translate_text(text, target_lang="EN").text  # ← Para traducir al ingles

# Argos Translate (offline)
class ArgosTranslator(BaseTranslator):
    def __init__(self):
        import argostranslate.translate as at
        src = tgt = None
        for lang in at.get_installed_languages():
            if lang.code == "es": src = lang
            #if lang.code == "de": tgt = lang  # ← Para traducir al aleman
            if lang.code == "en": tgt = lang  # ← Para traducir al ingles
        if not (src and tgt):
            raise RuntimeError("❌ Falta el modelo ES→DE en Argos Translate.")
        self.t = src.get_translation(tgt)
    def translate(self, text: str) -> str:
        return self.t.translate(text)

def get_translator(provider: str, api_key: Optional[str]) -> BaseTranslator:
    provider = provider.lower()
    if provider == "googletrans":
        return GoogleTransTranslator()
    if provider == "deepl":
        if not api_key:
            raise SystemExit("--api-key es obligatorio para DeepL")
        return DeeplTranslator(api_key)
    if provider == "argos":
        return ArgosTranslator()
    raise SystemExit(f"Proveedor desconocido: {provider}")

# ────────────────────────────  Helpers de formato (Genéricos y Traysia MD) ───────────────────────────
_pad_re = re.compile(r"@ *")

def _uppercase_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0

def is_badly_formatted(text: str, expected_ats: int) -> bool:
    """Detecta si un texto tiene signos de formato incorrecto, aunque tenga el número correcto de '@'."""
    if text.count("@") != expected_ats:
        return True
    for segment in text.split("@"):
        if len(segment.strip()) > 16 and " " not in segment:
            return True
    return False


def apply_formatting(es: str, de: str) -> str:
    """Sincroniza mayúsculas y preserva la posición original de los '@'."""
    de = re.sub(r"@+", " ", de)
    if '@' not in es or len(de.split()) < 2:
        return de.strip()

    es_segs = es.split('@')
    pads = [m.group(0)[1:] for m in _pad_re.finditer(es)]

    de_words = de.split()
    seg_count = len(es_segs)
    if seg_count == 0:
        return de.strip()

    # distribuir palabras proporcionalmente
    chunks = []
    remaining = len(de_words)
    avg = remaining // seg_count
    i = 0
    for n in range(seg_count - 1):
        chunk_size = avg
        if remaining - chunk_size < (seg_count - 1 - n):
            chunk_size = 1  # asegurar al menos 1 palabra por segmento
        chunks.append(de_words[i:i+chunk_size])
        i += chunk_size
        remaining -= chunk_size
    chunks.append(de_words[i:])

    de_segs = [' '.join(chunk) for chunk in chunks]

    # detectar si hay palabras pegadas (sin espacios)
    if any(len(seg) > 20 and ' ' not in seg for seg in de_segs):
        return de.strip()

    for i, (es_seg, de_seg) in enumerate(zip(es_segs, de_segs)):
        ratio = _uppercase_ratio(es_seg)
        if ratio > 0.8:
            de_segs[i] = de_seg.upper()
        elif es_seg[:1].isupper():
            de_segs[i] = de_seg[:1].upper() + de_seg[1:]

    rebuilt = de_segs[0].strip()
    for i, pad in enumerate(pads):
        segment = de_segs[i + 1].strip()
        if not rebuilt.endswith(" "):
            rebuilt += " "
        rebuilt += "@" + pad
        if not segment.startswith(" "):
            rebuilt += " "
        rebuilt += segment
    return rebuilt

def truncate(text: str, limit: int, encoding="latin-1") -> str:
    encoded_len = lambda t: len(encode_custom(t, encoding)) + 1
    truncator = "/"
    if encoded_len(text) <= limit:
        return text
    allowed = text
    while encoded_len(allowed + truncator) > limit:
        allowed = re.sub(r"\s?\S+$", "", allowed)
        if not allowed:
            truncator = ""  # ni siquiera cabe el truncador
            allowed = text[:limit - 1]
            break
    return allowed.rstrip() + truncator

def build_block(formatted: str, limit: int) -> dict:
    translit = transliterate_de(formatted) #Traysia DE. Comentar si la rom soporta representación de caracteres especiales alemanes
    if len(encode_custom(translit, "latin-1")) + 1 <= limit:
        return {"text": translit}
    return {"text": truncate(translit, limit), "review": True}

# ───────────────────────  Cargar o iniciar german.json  ──────────────────────
def load_or_init_de(dst: Path, es_data: list[dict], resume: bool):
    if resume and dst.exists():
        existing = {item["offset"]: item for item in json.loads(dst.read_text("utf-8"))}
        updated = []
        for es in es_data:
            entry = existing.get(es["offset"], {
                "offset": es["offset"],
                "length": es["length"],
                "text": "",
                "text_translator": "",
                "text_source": es.get("text_source", es["text"]),
            })
            # Siempre actualizamos/insertamos offset_hex
            entry["offset_hex"] = f"0x{es['offset']:X}"
            entry.setdefault("text_translator", "")
            entry.setdefault("text_source", es.get("text_source", es["text"]))
            updated.append(entry)
        return updated

    # archivo nuevo: clonar offset, length y text_source, incluyendo offset_hex
    return [
        {
            "offset": es["offset"],
            "offset_hex": f"0x{es['offset']:X}",
            "length": es["length"],
            "text": "",
            "text_translator": "",
            "text_source": es.get("text_source", es["text"]),
        }
        for es in es_data
    ]

DEFAULT_SAVE_EVERY = 25

# ─────────────────────────  Traducción segura  ───────────────────────────────
def safe_translate(tr: BaseTranslator, text: str, retries: int, delay: float) -> str:

    """
    Ejecuta una traducción segura con reintentos.

    Argumentos:
        tr: Objeto traductor con método .translate(text)
        text: Texto fuente en español
        retries: Número de intentos antes de fallar
        delay: Tiempo inicial de espera entre reintentos (se ajusta dinámicamente)

    Retorna:
        Texto traducido como str

    Lanza:
        La última excepción si todos los reintentos fallan
    """    
    import httpx, httpcore, json as _json
    timeout_exc = []
    for n in ("ReadTimeout", "TimeoutException"):
        if hasattr(httpx, n):
            timeout_exc.append(getattr(httpx, n))
    if hasattr(httpcore, "ReadTimeout"):
        timeout_exc.append(httpcore.ReadTimeout)
    timeout_exc.append(_json.JSONDecodeError)   # HTML/CAPTCHA en vez de JSON

    for attempt in range(retries + 1):
        try:
            return tr.translate(text)
        except tuple(timeout_exc):
            if attempt == retries:
                raise RuntimeError(
                    "Google no respondió con JSON válido después "
                    f"de {retries} reintentos; cancelo la ejecución."
                )
            # ↓ sigue dentro del except
            backoff = delay * (2 ** attempt) + random.uniform(0, 0.2)
            time.sleep(backoff)

# ────────────────────────────  Bucle principal  ─────────────────────────────
from tqdm import tqdm

def translate_file(src: Path, dst: Path, tr: BaseTranslator,
                   retries: int, resume: bool, save_every: int):
    es_items = json.loads(src.read_text("utf-8"))
    de_items = load_or_init_de(dst, es_items, resume)

    delay = 0.5
    latencies: deque[float] = deque(maxlen=20)

    try:
        for idx, (es_it, de_it) in enumerate(tqdm(zip(es_items, de_items),
                                                  total=len(es_items),
                                                  desc="Traduciendo",
                                                  unit="frase")):
            # saltar si ya hay traducción cruda
            if de_it.get("text_translator"):
                continue

            es_text = es_it["text"]

            t0 = time.perf_counter()
            de_raw = safe_translate(tr, es_text, retries, delay)
            lat = time.perf_counter() - t0
            latencies.append(lat)

            de_fmt = apply_formatting(es_text, de_raw)
            limit  = es_it["length"]
            de_it.update(text_translator=de_raw, **build_block(de_fmt, limit))
            de_it["length"] = limit  # mantener valor original

            # ─ auto‑ajuste de la pausa ─
            avg = sum(latencies) / len(latencies)
            if avg < 0.7:
                delay = max(delay / 2, 0.25)
            elif avg > 2.0:
                delay = min(delay * 1.5, 8.0)

            # guardado parcial
            if save_every and (idx + 1) % save_every == 0:
                dst.write_text(json.dumps(de_items, ensure_ascii=False, indent=2), "utf-8")
    
    except KeyboardInterrupt:
        print("\n⏹ Traducción interrumpida por el usuario. Guardando y saliendo…")
        return

    except RuntimeError as e:
        print("⚠", e)
        raise SystemExit(1)          # ← NUEVO: termina limpio

    finally:
        # siempre guarda al salir (cancelación o fin)
        dst.write_text(json.dumps(de_items, ensure_ascii=False, indent=2), "utf-8")

    print(f"✔ Traducción completa → {dst}")

# ─────────────────────────────  Re‑formateo  ────────────────────────────────
def format_file(src: Path, de_in: Path, de_out: Path):
    es = json.loads(src.read_text("utf-8"))
    de = json.loads(de_in.read_text("utf-8"))
    if len(es) != len(de):
        raise SystemExit("❌ Los archivos no tienen el mismo número de frases.")

    for es_it, de_it in tqdm(zip(es, de), total=len(es), desc="Formateando", unit="frase"):
        # Si no hay text_translator, no hay nada que formatear
        if not de_it.get("text_translator"):
            continue

        # Si el campo 'review' es False, asumimos que fue revisado manualmente y no tocamos
        if de_it.get("review") is False:
            continue

        candidate = de_it["text_translator"]
        de_fmt = apply_formatting(es_it["text"], candidate)
        limit = es_it["length"]
        de_it.update(**build_block(de_fmt, limit))
        de_it["length"] = limit  # asegúrate de que se mantenga sincronizado

    de_out.write_text(json.dumps(de, ensure_ascii=False, indent=2), "utf-8")
    print(f"✔ Formateadas {len(de)} frases → {de_out}")

def check_format(dst: Path):
    import re
    data = json.loads(dst.read_text("utf-8"))
    issues = []
    for item in data:
        txt = item.get("text", "")
        found = False
        if "@@" in txt:
            found = True
        if re.search(r"@[^\s@]", txt):
            found = True
        if re.search(r"[^\s@]@[a-zA-Z]", txt):
            found = True
        if found:
            item["review"] = True
            issues.append((item.get("offset", -1), txt))
    if issues:
        print(f"⚠ Detectadas {len(issues)} posibles incidencias. Archivo actualizado.")
        for off, txt in issues:
            print(f"  Offset 0x{off:X}: \"{txt}\"")
    else:
        print("✓ Sin problemas de formato detectados.")
    dst.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")   

# ───────────────────────────────  CLI  ───────────────────────────────────────
def cli():
    parser = argparse.ArgumentParser(description="[ES]→[DE] JSON translator")
    parser.add_argument("src", help="spanish.json original")
    parser.add_argument("dst", help="german.json destino (lectura/escritura)")
    parser.add_argument("--mode", choices=["translate", "format", "check"], default="translate")
    parser.add_argument("--provider", choices=["googletrans", "deepl", "argos"],
                        default="googletrans")
    parser.add_argument("--api-key", help="Clave API DeepL", default=None)
    parser.add_argument("--max-retries", type=int, default=5, help="reintentos por frase")
    parser.add_argument("--resume", action="store_true", help="reanudar archivo existente")
    parser.add_argument("--save-every", type=int, default=DEFAULT_SAVE_EVERY,
                        help="guardar cada N frases (0 = solo al finalizar)")

    args = parser.parse_args()
    src, dst = Path(args.src), Path(args.dst)

    if args.mode == "format":
        format_file(src, dst, dst)
        return
    if args.mode == "check":
        check_format(dst)
        return

    translator = get_translator(args.provider, args.api_key)
    try:
        translate_file(src, dst, translator,
                      retries=args.max_retries,
                      resume=args.resume,
                      save_every=args.save_every)
    except KeyboardInterrupt:
        print("\n⏹ Ejecución cancelada por el usuario. ¡Hasta luego!")
        return

if __name__ == "__main__":
    cli()