# 🧩 Traysia (Shinyuden Edition) – Fix Guardado y Análisis de Versiones

Este repositorio documenta la investigación en profundidad —incluyendo desensamblado 68000— del sistema de guardado de la ROM de *Traysia* para Mega Drive distribuida por **Shinyuden**, propone un **parche de mitigación ("Anticrash SRAM")** frente a la posible corrupción de partidas reportada por la comunidad, y reúne las herramientas de análisis y traducción desarrolladas durante el proceso.

## 🐛 El problema reportado

El usuario [TodoRPG](https://youtu.be/5akNdXm_BiM) experimentó un bug al salvar una partida avanzada en hardware real con la reedición física de Shinyuden: la partida quedó corrupta y al cargarla aparecieron textos en japonés y gráficos corruptos.

Tras una primera fase de análisis comparativo de archivos `.srm`, hemos investigado más a fondo desensamblando por completo el sistema de guardado de la ROM y auditando **todas** las diferencias entre la versión de Shinyuden y las versiones originales. El resultado es el diagnóstico y el parche de mitigación que se describen a continuación.

---

## 🔬 Cómo guarda partida Traysia realmente (análisis por desensamblado)

El motor del juego (heredado sin cambios de la versión USA de 1992) implementa un sistema de guardado sorprendentemente robusto sobre los 8 KB de SRAM del cartucho (mapeados en los bytes impares de `$200001–$203FFF`, tal y como declara la cabecera de la ROM):

| Zona SRAM (dirección de bus) | Contenido |
|---|---|
| `$200011–$20006F` | Firma `" SRAM_save_data "` escrita **por triplicado** (`$200011`, `$200031`, `$200051`) |
| `$200081` + `0xF00`·n | Slot de partida *n* (n = 0…3): bases en `$200081`, `$200F81`, `$201E81`, `$202D81` |

Cada slot almacena **tres copias redundantes** de ~600 bytes de datos (separadas `+0x500`/`+0xA00` en el bus) más una suma de verificación. Las rutinas clave:

| Offset ROM | Rutina |
|---|---|
| `0x1B464` | Comprobación de la firma al arrancar; si falta, formatea la SRAM |
| `0x1B4A6` | Formateo: limpia los 8 KB y escribe la firma ×3 (cadena en `0x1B4E0`) |
| `0x1B96A` | Guardado de slot: escribe las 3 copias con checksum |
| `0x1BBF2` | Escritura de cada byte con verificación y hasta 15 reintentos por copia; si las 3 copias fallan, pantalla de error |
| `0x1BF5C` / `0x1BF70` | Lectura con doble muestreo y **voto por mayoría** entre las 3 copias |
| `0x1BE44` | Verificación del checksum al cargar |

Dos datos importantes que arroja el desensamblado:

- **El sistema de guardado de Shinyuden es idéntico byte a byte al de la versión USA** (toda la región `0x1B000–0x1C000` y sus rutinas auxiliares coinciden exactamente). La adaptación no modificó las rutinas de guardado.
- El motor de Shinyuden **deriva de la build USA**: solo ~10.400 bytes difieren en el primer MB (frente a ~871.000 respecto a la japonesa), y casi todos son texto traducido y punteros re-apuntados al segundo MB, donde vive el guion en castellano.

> ℹ️ Nota sobre los dumps `.srm`: en hardware/FPGA el archivo puede ocupar 64 KB porque se vuelca la ventana completa `$200000–$20FFFF`; solo los primeros 16 KB (bytes impares) son SRAM real de 8 KB, y a partir de `0x4000` se lee ruido de bus abierto. Es normal y no indica ningún problema.

---

## ⚠️ El hallazgo: los ganchos del monitor de depuración apuntan a la SRAM

El juego original de 1992 dejó en la ROM comercial dos ganchos hacia un *monitor de depuración* que en las placas de desarrollo vivía en `$100000` (justo después del ROM de 1 MB):

1. **14 stubs de excepción de la CPU** (vectores 2–11, 14–15, 24 y TRAPs #2–#15, en `0x372–0x414`): ante un *bus error*, *address error*, instrucción ilegal, división por cero, etc., cada stub hace `moveq #n,d0 ; jmp $100000`.
2. **El streamer de texto** (`0x14FA`): antes de leer *cada byte* de texto comprueba si el puntero se ha salido del ROM, y en ese caso salta también al monitor:

```
0x14FA: cmpa.l #$100000,a0    ; ¿puntero de texto más allá del final del ROM?
0x1500: bmi.s  $150A          ; no → continuar
0x1504: jmp    $100000.l      ; sí → saltar al monitor de depuración
0x150A: move.b (a0)+,d7       ; fetch del siguiente byte de texto
```

En el cartucho retail de 1 MB, `$100000` era "el vacío": si algo llegaba ahí, el juego ya estaba colgado y no había nada más que perder.

Al expandir la ROM a 2 MB, el proceso de adaptación reubicó mecánicamente esas direcciones de `$100000` a `$200000`. La auditoría completa de la ROM encuentra **exactamente 16 valores reubicados así** (los operandos de los 14 stubs, más el límite del `cmpa` y el `jmp` del streamer) y ningún otro puntero a esa zona. El problema es que en el cartucho físico **`$200000` ya no es "el vacío": es la ventana de la SRAM donde viven las partidas guardadas**.

### Mecanismo plausible de la corrupción

Con la ROM actual, cualquier excepción de CPU *o* cualquier puntero de texto fuera de rango hace que la CPU **ejecute como código el contenido de la SRAM** (bytes impares = datos de la partida del usuario; bytes pares = bus abierto). A partir de ahí:

- La ejecución es caótica y **depende del contenido de la partida guardada**, lo que explicaría un fallo esporádico y difícil de reproducir.
- La CPU corre *dentro* de la ventana de SRAM escribible, con posibilidad real de escrituras salvajes sobre las partidas antes de colgarse. Cada nueva excepción durante ese caos vuelve a saltar a `$200000`, realimentando el bucle.
- En emulador, el bus abierto devuelve valores fijos y el resultado suele ser una congelación inofensiva; en hardware real la "sopa" de instrucciones es más rica. Esto encajaría con que el fallo solo se haya visto en hardware.
- Los síntomas visuales encajan: la rutina de carga (`0x1BE54`) tolera un checksum inválido y carga los datos igualmente, y el motor de texto sigue siendo el japonés (la traducción usa códigos Shift-JIS de 2 bytes para `¡ ¿` y las tildes, y la fuente conserva glifos japoneses). Un estado corrupto alimenta al renderizador con bytes basura ≥ `0x80` → glifos japoneses aleatorios y gráficos rotos, exactamente lo reportado.

> ⚠️ **Estado de la hipótesis**: es el único defecto estructural que aparece al auditar todas las diferencias de la ROM de Shinyuden, y saltar a `$200000` es objetivamente incorrecto en un cartucho con SRAM. Aun así, **está pendiente de validación empírica** (ver más abajo) y no puede descartarse por completo un factor puramente físico (pila, PCB) con una sola muestra del fallo.

---

## ✅ Parche Anticrash SRAM (mitigación)

📦 [`patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips`](patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips)

### Estrategia de mitigación

El parche **no toca ninguna lógica del juego**: se limita a redirigir las 15 rutas de error que hoy acaban ejecutando la SRAM, convirtiéndolas en resultados seguros y deterministas. La SRAM deja de ser alcanzable como código en cualquier circunstancia:

1. **Excepciones de CPU → reinicio limpio.** Los 14 stubs pasan de `jmp $200000` a `jmp $000200`, el punto de entrada oficial del bootstrap de Sega, que reinicializa la máquina por completo sin depender del estado (corrupto) del momento del fallo. Un cuelgue se convierte en un reinicio con la **SRAM intacta**: se pierde el progreso no guardado, nunca la partida salvada.
2. **Puntero de texto fuera de rango → fin de cadena.** El `jmp $200000` del streamer se sustituye por `moveq #0,d7 ; bra.s $150C`, que simula exactamente la lectura de un byte terminador: el `beq` ya existente en `0x150C` toma la ruta normal de fin de texto. Un puntero defectuoso corta el diálogo en vez de ejecutar la SRAM. (El límite `cmpa.l #$200000` se conserva: es el valor correcto para un ROM de 2 MB.)

### Cambios exactos (34 bytes en 15 puntos)

| Offset ROM | Antes | Después | Efecto |
|---|---|---|---|
| `0x37A + 12·k` (k = 0…13) | `00 20 00 00` | `00 00 02 00` | `jmp $200000` → `jmp $000200` (soft reset por el bootstrap oficial) |
| `0x1504` | `4E F9 00 20 00 00` | `7E 00 60 04 4E 71` | `jmp $200000` → `moveq #0,d7 ; bra.s $150C ; nop` (simula terminador de cadena) |

Verificación:

| Archivo | MD5 |
|---|---|
| `Traysia (W).bin` original | `db1529b9d6383bdb5b2d6c969cef6022` |
| ROM parcheada | `476b5b7bf9aa02dc9c2490cd2150774b` |

### Qué NO hace este parche

Es una **mitigación**, no la corrección del disparador subyacente: si existe un puntero de texto o un dato defectuoso concreto que provoque la condición de error, seguirá existiendo — pero su consecuencia pasará de "ejecución caótica dentro de la SRAM con riesgo de corrupción" a "corte de diálogo o reinicio limpio con las partidas a salvo". Identificar el disparador exacto requiere depuración dinámica (ver plan de validación).

### 🧾 Cómo aplicar el parche

1. Con **Lunar IPS** (o cualquier herramienta compatible): aplica [`patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips`](patches/Traysia_Shinyuden_anticrash_SRAM_patch.ips) sobre `Traysia (W).bin`.
2. O directamente con Python, sin Lunar IPS:

```bash
python tools/fix_rom_traysia_shinyuden_anticrash.py
```

El script comprueba el MD5 de la ROM original, **verifica los bytes originales de cada punto antes de tocarlos**, genera `roms/Traysia (W)_anticrash.bin` y, con la opción `--ips`, regenera también el parche IPS.

🔬 **Estado: pendiente de validación empírica.** El parche está verificado a nivel de desensamblado (las instrucciones resultantes son correctas y equivalen a las rutas seguras descritas), pero aún no se ha reproducido el fallo original ni confirmado la mitigación en hardware real.

---

## 🧪 Plan de validación (cómo ayudar)

1. **Encontrar el disparador**: en un emulador con depurador (BlastEm nightly, Exodus, MAME), poner un *breakpoint* de ejecución en `PC=$200000` y jugar una partida avanzada con la ROM sin parchear (idealmente la ruta del vídeo de TodoRPG). Si salta, el backtrace y el registro `a0` señalan la cadena o puntero exacto responsable.
2. **Probar la mitigación**: forzar la condición con el depurador (poner `a0=$200000` en el streamer, o inyectar una instrucción ilegal) en la ROM original y en la parcheada, comparando el `.srm` antes y después: sin parche se ejecuta la SRAM; con parche debe verse el fin de cadena o el reinicio con SRAM intacta.
3. **La prueba de oro**: conseguir el `.srm` corrupto real de un cartucho afectado *sin pasarlo por ninguna herramienta*. Su contenido permitiría incluso reconstruir qué "código" ejecutó la CPU.
4. **Hardware real / FPGA**: partidas largas con la ROM parcheada en EverDrive, Mega Sg, etc., verificando estabilidad y guardado.

---

## 📜 Historial de la investigación

Una primera fase de este proyecto se basó en la comparación de archivos `.srm` de distintas versiones y dispositivos, y produjo un parche preliminar. Al investigar más a fondo —desensamblando el sistema de guardado completo y auditando todas las diferencias entre la ROM de Shinyuden y la versión USA— pudimos caracterizar con precisión la arquitectura real de guardado (firma triplicada, copias redundantes con voto por mayoría) y localizar el vector de riesgo descrito arriba. El parche **Anticrash SRAM** sustituye al preliminar como mitigación más segura y mejor fundamentada; los materiales de la fase anterior permanecen disponibles en el historial de git del repositorio.

---

## 🔬 Análisis Comparativo de las Distintas Versiones de Traysia para Mega Drive

Análisis técnico de las versiones existentes del juego: la japonesa original, su localización oficial americana, la adaptación para Evercade y la traducción al castellano publicada por Shinyuden.

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

#### Diferencias binarias directas
- Japón vs USA: 83% de la ROM es diferente. No es solo traducción, sino reestructuración profunda.
- USA vs Evercade: cambios mínimos (cabecera, firmas, compatibilidad).
- USA vs Español: ~10.400 bytes distintos en el primer MB (texto y punteros, esencialmente) más el segundo MB nuevo con el guion en castellano.

#### Tabla de Equivalencias
| Versión | Nombre de Archivo | Tamaño | Idioma | Deriva de | Cambios Principales |
|---|---|---|---|---|---|
| Minato no Traysia (Japón) | Minato no Traysia (Japan).md | 1MB | Japonés | Original | Versión base. Fecha interna: 1991.DEC |
| Traysia (USA) | Traysia (USA).md | 1MB | Inglés | Japonesa | Traducción oficial. Añade textos en inglés y ajustes en código |
| Traysia (Evercade) | Traysia (World) (Evercade).md | 1MB | Inglés | USA | Solo modifica metadatos. Compatibilidad Evercade |
| Traysia (Español – Shinyuden) | Traysia (W).bin | 2MB | Español | USA (motor) | Traducción completa. ROM expandida a 2MB, texto reubicado al segundo MB |

#### Conclusiones de la Comparación
- La versión USA de Traysia no es solo una traducción: incluye ajustes profundos en el código.
- La versión Evercade parte de la USA y realiza cambios menores, probablemente solo en la cabecera.
- La versión en español de Shinyuden **hereda el motor de la build USA** (el sistema de guardado es idéntico byte a byte) y expande la ROM a 2MB reales, reubicando el texto. Es más, **incluye los textos originales en inglés de la versión USA**, con lo cual podría ser posible habilitar el cambio de idioma si encontramos la manera.
- El análisis de diferencias mediante parches .IPS, comparación binaria y desensamblado es una herramienta fundamental para la preservación y documentación de estas versiones.

---

## 🛠️ Herramientas incluidas

Este repositorio incluye una descripción detallada de los scripts desarrollados para el análisis y validación. Puedes encontrar una descripción de cada una de las herramientas y scripts en este [README_tools.md](tools/README_tools.md)

### 📂 Organización de las ROMs
Guarda todas las ROMs en una carpeta llamada `roms/` ubicada en la raíz del repositorio. Tanto `tools/fix_rom_traysia_shinyuden_anticrash.py` como `tools/traysia_rom_analyzer.py` y otros scripts buscan los archivos directamente en esa ruta.
* **Traysia (W).bin**: Versión oficial editada y traducida al castellano por Shinyuden en 2025. 2MB.
* **Traysia (World) (Evercade).md**: Reedición lanzada en 2022 por Blaze para Evercade y sistemas compatibles, incluido en el cartucho "Renovation Collection 1". 1MB.
* **Traysia (USA).md**: Traducción de la versión japonesa lanzada en Estados Unidos en abril de 1992.
* **Minato no Traysia (Japan).md**: versión original, lanzada en Japón en febrero de 1992.

---

## 📌 Cómo contribuir

Puedes ayudar:
- Ejecutando el plan de validación descrito arriba (depurador, breakpoints en `PC=$200000`, pruebas en hardware real).
- Aportando un `.srm` corrupto real de un cartucho afectado, sin manipular.
- Verificando el parche en partidas reales avanzadas y reportando cualquier regresión o incompatibilidad.
- Proponiendo mejoras o integraciones en los scripts.

---

## 🧠 Créditos y Licencia

- Investigación, análisis y parche por **@Arcanbytes**.
- Documentación generada con apoyo de herramientas propias.

Licencia: MIT – puedes usar, modificar y compartir este contenido libremente.

Si has detectado errores o quieres contribuir, puedes abrir un issue o forkear este repositorio.
