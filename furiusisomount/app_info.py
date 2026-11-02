"""Application metadata.

Kept in a single place so every module (about dialog, logs, README helpers)
agrees on names, version and credits.
"""

APP_NAME = "furiusisomount"
APP_DISPLAY_NAME = "Furius ISO Mount"
VERSION = "0.11.3.1"
LICENSE = "GNU General Public License v3 (GPL v3)"
LICENSE_SHORT = "GPL-3.0-or-later"

# Current maintainer (PyQt6 fork)
MAINTAINER_NAME = "Washington Indacochea Delgado"
MAINTAINER_EMAIL = "linuxfrontier@proton.me"
PROJECT_URL = "https://github.com/wachin/furiusisomount"

# Original author of the abandoned project
ORIGINAL_AUTHOR_NAME = "Dean Harris"
ORIGINAL_AUTHOR_EMAIL = "marcus_furius@hotmail.com"
ORIGINAL_PROJECT_URL = "https://github.com/prachpub/furiusisomount"

# Technologies used by the application (shown in the about dialog)
TECHNOLOGIES = (
    "Python 3",
    "PyQt6",
    "fuseiso (FUSE)",
    "udisks2 (loop devices)",
    "bchunk (BIN/CUE → ISO)",
    "brasero / wodim (burning)",
)
