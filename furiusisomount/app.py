#!/usr/bin/env python3
"""Furius ISO Mount - application entry point.

Used both as the console script installed by the Debian package
(``furiusisomount``) and from the git checkout (``python3 main.py``).

Original application by Dean Harris <marcus_furius@hotmail.com>.
PyQt6 fork by Washington Indacochea Delgado <linuxfrontier@proton.me>.
Licensed under the GNU GPL v3.
"""

from __future__ import annotations

import os
import sys

from .app_info import APP_DISPLAY_NAME, PROJECT_URL, VERSION

USAGE = """\
Usage: furiusisomount [OPTION]... [IMAGE|CUE]...

Mount ISO, IMG, BIN, MDF and NRG disc images without burning them to a disc.
It also converts BIN/CUE images to ISO.

Options:
  -h, --help      show this help message and exit
  -V, --version   show the version number and exit

Environment:
  FURIUSISOMOUNT_LANG           force the interface language (es, fr, de, ...)
  FURIUSISOMOUNT_TRANSLATIONS   directory containing compiled .qm translations

Files given on the command line are loaded on start-up (images are opened in
the mount tab, .cue files in the convert tab).

Report bugs at: {url}/issues
""".format(url=PROJECT_URL)

# File types understood on the command line
IMAGE_EXTENSIONS = (".iso", ".img", ".bin", ".mdf", ".nrg")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if any(a in ("-V", "--version") for a in args):
        print("%s %s" % (APP_DISPLAY_NAME, VERSION))
        return 0
    if any(a in ("-h", "--help") for a in args):
        sys.stdout.write(USAGE)
        return 0

    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        sys.stderr.write("furiusisomount: unrecognized option '%s'\n" % unknown[0])
        sys.stderr.write("Try 'furiusisomount --help' for more information.\n")
        return 2

    # Defer the Qt import so that --help/--version work without a display
    from PyQt6.QtWidgets import QApplication

    from .i18n import install_translations
    from .ui.main_window import FuriusIsoMount

    app = QApplication([sys.argv[0]] + args)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setOrganizationName("furiusisomount")
    app.setDesktopFileName("furiusisomount")

    # Load Qt + application translations (English is the source language)
    install_translations(app)

    window = FuriusIsoMount()
    window.show()

    # Open images / cue sheets passed on the command line
    for path in args:
        lower = path.lower()
        if lower.endswith(".cue"):
            window.tabs.setCurrentWidget(window.convert_tab)
            window.convert_tab.set_cue_file(os.path.abspath(path))
        elif lower.endswith(IMAGE_EXTENSIONS):
            window.tabs.setCurrentWidget(window.mount_tab)
            window.mount_tab.set_image(os.path.abspath(path))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
