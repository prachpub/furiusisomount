"""Translation support (Qt Linguist workflow).

* Source strings are written in English and wrapped in ``self.tr(...)`` /
  ``QCoreApplication.translate(...)``.
* Translators add languages with Qt Linguist: edit the ``.ts`` files under
  ``translations/`` and compile them with ``lrelease`` (see
  ``scripts/update_translations.sh``).
* Runtime lookup order for ``furiusisomount_<locale>.qm``:

      1. ``$FURIUSISOMOUNT_TRANSLATIONS`` (explicit override)
      2. ``translations/`` inside the project tree (development builds)
      3. ``<prefix>/share/furiusisomount/translations`` (installed builds)
      4. ``~/.local/share/furiusisomount/translations`` (per user)

The environment variable ``FURIUSISOMOUNT_LANG`` (e.g. ``es``, ``es_ES``,
``de``) can force a language regardless of the system locale.
"""

from __future__ import annotations

import glob
import os

from PyQt6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator
from PyQt6.QtWidgets import QApplication

from .app_info import APP_NAME
from .paths import resource_path

# Keep strong references: Qt does not take ownership of translators.
_loaded_translators: list[QTranslator] = []


def translation_dirs() -> list[str]:
    dirs = []
    override = os.environ.get("FURIUSISOMOUNT_TRANSLATIONS")
    if override:
        dirs.append(override)
    dirs.append(resource_path("translations"))
    dirs.append("/usr/share/%s/translations" % APP_NAME)
    dirs.append("/usr/local/share/%s/translations" % APP_NAME)
    dirs.append(os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME, "translations"))
    return [d for d in dirs if d and os.path.isdir(d)]


def _load_app_translator(app: QApplication, locale: QLocale) -> bool:
    """Try to load furiusisomount_<locale>.qm from every known directory."""
    name = QLocale(locale).name()  # e.g. "es_ES"
    if name in ("C", "POSIX"):
        # The source language is English: nothing to load
        return False
    languages = [name]
    if "_" in name:
        languages.append(name.split("_")[0])

    for directory in translation_dirs():
        for language in languages:
            # Canonical name first, then other prefixes with the same language.
            # Patterns are anchored to "_<language>." so that a locale like "C"
            # can never match a file such as furiusisomount_zh_CN.qm.
            candidates = [os.path.join(directory, "%s_%s.qm" % (APP_NAME, language))]
            candidates += sorted(glob.glob(os.path.join(directory, "*_%s.qm" % language)))
            candidates += sorted(glob.glob(os.path.join(directory, "*_%s_*.qm" % language)))
            for candidate in candidates:
                translator = QTranslator()
                if translator.load(candidate):
                    app.installTranslator(translator)
                    _loaded_translators.append(translator)
                    return True
    return False


def _load_qt_translator(app: QApplication, locale: QLocale) -> bool:
    """Translate the standard Qt dialogs (buttons, file dialogs...)."""
    translator = QTranslator()
    translations = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load(locale, "qtbase", "_", translations):
        app.installTranslator(translator)
        _loaded_translators.append(translator)
        return True
    return False


def install_translations(app: QApplication | None = None) -> QLocale:
    """Install application + Qt base translations. Returns the locale used."""
    app = app or QApplication.instance()
    forced = os.environ.get("FURIUSISOMOUNT_LANG", "").strip()
    locale = QLocale(forced) if forced else QLocale.system()

    if app is not None:
        _load_qt_translator(app, locale)
        _load_app_translator(app, locale)

    return locale


def tr(context: str, text: str) -> str:
    """Translate a string from a non-QObject module."""
    return QCoreApplication.translate(context, text)
