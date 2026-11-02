# Traducciones / Translations

Este directorio contiene los archivos de **Qt Linguist** del programa.

## Flujo de trabajo

1. **Extraer cadenas** (el idioma base es el inglés):

   ```bash
   ./scripts/update_translations.sh              # crea/actualiza furiusisomount_es.ts
   LANGS="pt fr de" ./scripts/update_translations.sh
   ```

2. **Traducir** con Qt Linguist:

   ```bash
   linguist translations/furiusisomount_es.ts
   ```

3. **Compilar** a `.qm` (el script lo hace si `lrelease` está instalado):

   ```bash
   ./scripts/update_translations.sh
   ```

## Cómo se cargan en tiempo de ejecución

`furiusisomount/i18n.py` busca `furiusisomount_<locale>.qm` en este orden:

1. `$FURIUSISOMOUNT_TRANSLATIONS` (ruta explícita)
2. `translations/` del árbol del proyecto (ejecución desde el repositorio)
3. `/usr/share/furiusisomount/translations` o `/usr/local/share/...`
4. `~/.local/share/furiusisomount/translations`

Idioma seleccionado: el del sistema, o el forzado con `FURIUSISOMOUNT_LANG`
(ej. `FURIUSISOMOUNT_LANG=es python3 main.py`).

## Archivos incluidos

| Archivo | Idioma | Estado |
|---|---|---|
| `furiusisomount_es.ts` / `.qm` | Español | 81/81 ✅ |
| `furiusisomount_fr.ts` / `.qm` | Francés | 81/81 ✅ |
| `furiusisomount_pt.ts` / `.qm` | Portugués | 81/81 ✅ |
| `furiusisomount_de.ts` / `.qm` | Alemán | 81/81 ✅ |
| `furiusisomount_it.ts` / `.qm` | Italiano | 81/81 ✅ |
| `furiusisomount_ja.ts` / `.qm` | Japonés | 81/81 ✅ |
| `furiusisomount_ru.ts` / `.qm` | Ruso | 81/81 ✅ |
| `furiusisomount_zh_CN.ts` / `.qm` | Chino simplificado | 81/81 ✅ |

Idioma fuente: inglés (las cadenas viven en el código con `tr()`).
