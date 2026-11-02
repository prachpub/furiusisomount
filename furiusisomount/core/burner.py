"""Disc burning helpers (brasero preferred, wodim as fallback)."""

from __future__ import annotations

import os
import shutil
import subprocess


class BurnError(Exception):
    """Raised when no burner is available or the image cannot be burned."""


def available_burner() -> str | None:
    """Return the name of the available burning program, if any."""
    for name in ("brasero", "wodim"):
        if shutil.which(name):
            return name
    return None


def burn_image(image_path: str) -> str:
    """Start burning *image_path*.  Returns the program used."""
    if not os.path.isfile(image_path):
        raise BurnError("Image not found: %s" % image_path)

    burner = available_burner()
    if burner is None:
        raise BurnError("No burning program found. Install brasero or wodim.")

    if burner == "brasero":
        cmd = ["brasero", "--image", image_path]
    else:
        cmd = ["wodim", "dev=/dev/sr0", image_path]

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise BurnError(str(exc)) from exc
    return burner
