"""BIN/CUE -> ISO conversion using ``bchunk``.

Fixes over the historical implementation:

* no global ``re`` import missing (progress parsing done without regex),
* the output of ``bchunk`` is discovered with ``glob`` instead of assuming
  it is always named ``<base>01.iso``,
* ``bchunk`` is executed without a shell (no quoting / injection problems).
"""

from __future__ import annotations

import glob
import os
import subprocess
from typing import Callable

LogFn = Callable[[str], None]
ProgressFn = Callable[[int, str], None]


class ConversionError(Exception):
    """Raised when the BIN/CUE conversion fails."""


def find_associated_bin(cue_path: str) -> str | None:
    """Return the .bin file that belongs to *cue_path*, if any."""
    base_dir = os.path.dirname(cue_path) or "."
    stem = os.path.splitext(os.path.basename(cue_path))[0]

    preferred = os.path.join(base_dir, stem + ".bin")
    if os.path.exists(preferred):
        return preferred

    # Case-insensitive match for the sibling file, then any .bin in the folder
    entries = sorted(os.listdir(base_dir))
    for name in entries:
        if name.lower() == (stem + ".bin").lower():
            return os.path.join(base_dir, name)
    for name in entries:
        if name.lower().endswith(".bin"):
            return os.path.join(base_dir, name)
    return None


def _track_count(cue_path: str) -> int:
    """Best-effort count of TRACK lines inside a .cue sheet."""
    count = 0
    try:
        with open(cue_path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.strip().upper().startswith("TRACK"):
                    count += 1
    except OSError:
        pass
    return max(count, 1)


def convert_bin_cue(
    cue_path: str,
    iso_path: str,
    log: LogFn | None = None,
    progress: ProgressFn | None = None,
) -> str:
    """Convert the BIN/CUE pair into an ISO image at *iso_path*.

    Returns the final ISO path.  Raises :class:`ConversionError` on failure.
    """
    if not cue_path or not os.path.isfile(cue_path):
        raise ConversionError("Please select a valid .cue file")

    bin_path = find_associated_bin(cue_path)
    if not bin_path:
        raise ConversionError("No associated .bin file was found")

    iso_path = os.path.abspath(iso_path)
    if not iso_path.lower().endswith(".iso"):
        iso_path += ".iso"
    iso_base = os.path.splitext(iso_path)[0]
    os.makedirs(os.path.dirname(iso_path) or ".", exist_ok=True)

    # Remove leftovers of previous runs so the glob only sees new files
    for stale in glob.glob(iso_base + "*"):
        if stale.lower().endswith((".iso", ".bin", ".img", ".wav", ".cdr")):
            try:
                os.remove(stale)
            except OSError:
                pass

    cmd = ["bchunk", "-v", bin_path, cue_path, iso_base]
    if log:
        log("[CONVERT] %s" % " ".join(cmd))

    total_tracks = _track_count(cue_path)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        raise ConversionError(
            "bchunk is not installed. Install it with your package manager "
            "(e.g. 'sudo apt install bchunk')."
        ) from exc

    assert process.stdout is not None
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        if log:
            log("[CONVERT] %s" % line)
        if "%" in line and progress is not None:
            digits = ""
            for token in line.replace("%", " %").split():
                if token.endswith("%"):
                    digits = token[:-1]
                    break
            if digits.isdigit():
                pct = min(100, int(digits) * 100 // total_tracks)
                progress(pct, line)

    return_code = process.wait()
    if return_code != 0:
        raise ConversionError("bchunk failed with exit code %d" % return_code)

    # bchunk writes <base><NN>.<ext>; find what was really produced
    produced = [
        name
        for name in sorted(glob.glob(iso_base + "*"))
        if os.path.isfile(name) and not name.lower().endswith(".cue")
    ]
    iso_files = [name for name in produced if name.lower().endswith(".iso")]
    candidates = iso_files or produced

    if not candidates:
        raise ConversionError("bchunk did not produce any output file")

    final_iso = candidates[0]
    if final_iso != iso_path:
        if os.path.exists(iso_path):
            os.remove(iso_path)
        os.rename(final_iso, iso_path)

    # Keep only the ISO: drop extra tracks generated as .bin/.wav
    for extra in produced:
        if extra != final_iso and extra != iso_path:
            try:
                os.remove(extra)
            except OSError:
                pass

    if progress is not None:
        progress(100, "done")
    return iso_path
