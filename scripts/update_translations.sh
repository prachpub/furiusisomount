#!/usr/bin/env bash
# Update and compile the Qt Linguist translations.
#
#   ./scripts/update_translations.sh              # updates all .ts files
#   LANGS="es fr pt de it ja ru zh_CN" ./scripts/update_translations.sh
#
# Requirements:
#   - pylupdate6        (pip install PyQt6)
#   - lrelease          (Qt linguist tools: "qt6-l10n-tools" / "linguist-qt6" /
#                        "qttools5-dev-tools" depending on the distro) or
#                        pyside6-lrelease (pip install PySide6-Essentials)
#
# Workflow for a new language (example: Portuguese "pt"):
#   1. LANGS=pt ./scripts/update_translations.sh      -> creates furiusisomount_pt.ts
#   2. Open translations/furiusisomount_pt.ts with Qt Linguist and translate
#   3. Run this script again to compile furiusisomount_pt.qm
#   4. Test with:  FURIUSISOMOUNT_LANG=pt python3 main.py
set -euo pipefail

cd "$(dirname "$0")/.."

SOURCES=(main.py furiusisomount/*.py furiusisomount/core/*.py furiusisomount/ui/*.py)
LANGS=(${LANGS:-es fr pt de it ja ru zh_CN})

mkdir -p translations

echo "* Extracting source strings with pylupdate6..."
for lang in "${LANGS[@]}"; do
    ts="translations/furiusisomount_${lang}.ts"
    echo "  - ${ts}"
    pylupdate6 "${SOURCES[@]}" -ts "${ts}"
done

echo "* Compiling .qm files..."
LRELEASE=""
if command -v lrelease >/dev/null 2>&1; then
    LRELEASE="lrelease"
else
    # lrelease from Qt ships with a versioned name on some distros
    for candidate in lrelease-qt6 lrelease-qt5 lrelease6; do
        if command -v "${candidate}" >/dev/null 2>&1; then
            LRELEASE="${candidate}"
            break
        fi
    done
fi
if [ -z "${LRELEASE}" ] && command -v pyside6-lrelease >/dev/null 2>&1; then
    LRELEASE="pyside6-lrelease"
fi

if [ -n "${LRELEASE}" ]; then
    for ts in translations/*.ts; do
        [ -e "${ts}" ] || continue
        "${LRELEASE}" -silent "${ts}" -qm "${ts%.ts}.qm"
        echo "  - ${ts%.ts}.qm"
    done
else
    echo "  (no lrelease found: install the Qt linguist tools or 'pip install PySide6-Essentials')"
fi

echo "Done."
