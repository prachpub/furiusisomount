#!/usr/bin/env python3
"""Development entry point.

The installed application is launched with the ``furiusisomount`` console
script (see pyproject.toml); this file only keeps ``python3 main.py`` working
from a git checkout.
"""

import sys

from furiusisomount.app import main

if __name__ == "__main__":
    sys.exit(main())
