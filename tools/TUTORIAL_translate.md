### Flujo de Trabajo para la Traducción de ROMs de MD

**Objetivo:** Traducir el texto de una ROM de juego de Mega Drive (en este caso, de español a inglés o alemán) y generar una nueva ROM con la traducción.

**Herramientas clave:**

-   `translate_spanish.py`: Para exportar e importar cadenas de texto de la ROM.

-   `translate_spanish_to_german.py` (o similar): Para realizar la traducción automática, formateo y revisión de la calidad de la traducción.

-   `translate_spanish_checkfit.py`: Para verificar si las cadenas traducidas caben en el espacio asignado en la ROM.

* * * * *

**Pasos del Flujo de Trabajo:**

1.  **Exportar las Cadenas de Texto Originales:**

    -   **Propósito:** Extraer todo el texto original (en español, en este caso) de la ROM a un archivo JSON. Este archivo incluirá el offset (dirección) y la longitud original de cada cadena.

    -   **Comando:**

        PowerShell

        ```
        & D:/Projects/Development/TraysiaROMFix/.venv/Scripts/python.exe d:/Projects/Development/TraysiaROMFix/tools/translate_spanish.py export "roms/Traysia (W).bin" translations/spanish.json

        ```

    -   **Resultado:** Se creará el archivo `translations/spanish.json` con todas las cadenas extraídas.

2.  **Traducir Automáticamente las Cadenas (Primer Borrador):**

    -   **Propósito:** Generar una traducción automática de las cadenas desde el archivo JSON de origen (español) a un nuevo archivo JSON de destino (inglés o alemán), utilizando un proveedor de traducción (ej. `googletrans`).

    -   **Comando:**

        PowerShell

        ```
        & D:/Projects/Development/TraysiaROMFix/.venv/Scripts/python.exe d:/Projects/Development/TraysiaROMFix/tools/translate_spanish_to_german.py translations/spanish.json translations/english.json --provider googletrans

        ```

    -   **Resultado:** Se generará `translations/english.json` (o `german.json` si se especifica otro idioma de destino) con las traducciones automáticas.

3.  **Formatear las Cadenas Traducidas:**

    -   **Propósito:** Aplicar cualquier formateo específico del juego o de la ROM a las cadenas traducidas. Esto puede incluir el manejo de caracteres especiales, saltos de línea, o la adaptación a las limitaciones del motor de texto del juego.

    -   **Comando:**

        PowerShell

        ```
        & D:/Projects/Development/TraysiaROMFix/.venv/Scripts/python.exe d:/Projects/Development/TraysiaROMFix/tools/translate_spanish_to_german.py translations/spanish.json translations/english.json --mode format

        ```

    -   **Resultado:** El archivo `translations/english.json` (o `german.json`) se actualizará con las cadenas formateadas.

4.  **Verificar la Calidad y Coherencia de la Traducción:**

    -   **Propósito:** Realizar una revisión automática de la traducción para detectar posibles incidencias, como problemas con variables, códigos de control, o patrones de texto que puedan haberse dañado durante la traducción o el formateo.

    -   **Comando:**

        PowerShell

        ```
        & D:/Projects/Development/TraysiaROMFix/.venv/Scripts/python.exe d:/Projects/Development/TraysiaROMFix/tools/translate_spanish_to_german.py translations/spanish.json translations/english.json --mode check

        ```

    -   **Resultado:** Se listarán las incidencias detectadas. Es crucial revisar estas incidencias manualmente en el archivo JSON y corregir la traducción o el formato según sea necesario.

5.  **Verificar si las Cadenas Traducidas Caben en la ROM:**

    -   **Propósito:** Asegurarse de que el texto traducido no excede la longitud máxima permitida por el espacio original asignado en la ROM para cada cadena. Esto es vital para evitar desbordamientos y corrupción de datos.

    -   **Comandos:**

        PowerShell

        ```
        python tools/translate_spanish_checkfit.py translations/german.json
        python tools/translate_spanish_checkfit.py translations/english.json

        ```

    -   **Resultado:** Deberías ver un mensaje "✓ Todas las cadenas caben." Si no es así, significa que algunas cadenas son demasiado largas y deben ser acortadas manualmente en el archivo JSON de traducción.

6.  **Importar las Cadenas Traducidas de Vuelta a la ROM:**

    -   **Propósito:** Escribir las cadenas de texto ya traducidas y verificadas desde el archivo JSON de destino a una nueva ROM, creando una versión localizada del juego.

    -   **Comando:**

        PowerShell

        ```
        & d:/Projects/Development/TraysiaROMFix/.venv/Scripts/python.exe d:/Projects/Development/TraysiaROMFix/tools/translate_spanish.py import "roms/Traysia (W).bin" translations/english.json "roms/Traysia (EN).bin"

        ```

    -   **Resultado:** Se generará una nueva ROM (`roms/Traysia (EN).bin` en este ejemplo) con el texto traducido.

* * * * *

**Notas Importantes:**

-   **Ruta del Entorno Virtual (`.venv`):** Asegúrate de que el entorno virtual esté siempre activado o que uses la ruta completa al `python.exe` dentro de tu `.venv` como se muestra en tus ejemplos.

-   **Revisión Manual:** La traducción automática es un buen punto de partida, pero la **revisión y edición manual** de las traducciones en el archivo JSON (después del paso 3) es **absolutamente crucial** para garantizar la calidad, el contexto y la coherencia del texto final del juego.

-   **Nombres de Archivos:** Adapta los nombres de los archivos JSON de traducción (`english.json`, `german.json`, etc.) según el idioma de destino.

-   **Problemas de Ajuste:** Si las cadenas no caben (paso 5), es necesario editar el archivo JSON de traducción para acortar las frases hasta que encajen.

-   **Configuración Inicial:** Asegúrate de que los scripts estén en la ubicación esperada (ej. `d:/Projects/Development/TraysiaROMFix/tools/`) o ajusta las rutas en los comandos.