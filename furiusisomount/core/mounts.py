"""Mount / unmount operations.

Two strategies are supported:

* ``fuse``:  ``fuseiso <image> <mount point>`` (no root required)
* ``loop``:  ``udisksctl loop-setup`` + ``udisksctl mount`` (udisks2)

Fixes over the historical implementation: no ``shell=True`` commands, the
loop device is parsed from udisksctl output instead of assuming
``/dev/loop0``, and the real mount point reported by udisksctl is stored.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, asdict

METHOD_FUSE = "FUSE"
METHOD_LOOP = "Loop"


class MountError(Exception):
    """Raised when a mount or unmount operation fails."""


@dataclass
class MountInfo:
    mount_point: str
    image_file: str
    method: str = METHOD_FUSE
    device: str = ""  # /dev/loopX for loop mounts

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MountInfo":
        return cls(
            mount_point=data.get("mount_point", ""),
            image_file=data.get("image_file", ""),
            method=data.get("method", METHOD_FUSE),
            device=data.get("device", ""),
        )


# --------------------------------------------------------------------- helpers
def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, check=check, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MountError("Command not found: %s" % cmd[0]) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise MountError(detail or str(exc)) from exc


def make_mount_point(image_path: str, root: str | None = None) -> str:
    """Create an empty directory to mount *image_path* into."""
    root = root or os.path.expanduser("~")
    base = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.splitext(os.path.basename(image_path))[0])
    base = base or "furiusisomount"
    candidate = os.path.join(root, base)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(root, "%s_%d" % (base, counter))
        counter += 1
    os.mkdir(candidate)
    return candidate


def mount_point_busy(mount_point: str) -> bool:
    """True when some process is using *mount_point* (needs lsof)."""
    lsof = shutil.which("lsof")
    if not lsof or not os.path.isdir(mount_point):
        return False
    result = subprocess.run([lsof, "+D", mount_point], capture_output=True, text=True)
    return result.returncode == 0


def find_loop_device(mount_point: str) -> str:
    """Return the /dev/loopX backing *mount_point*, reading /proc/mounts."""
    try:
        with open("/proc/mounts", "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == mount_point and parts[0].startswith("/dev/loop"):
                    return parts[0]
    except OSError:
        pass
    return ""


def _fusermount_binary() -> str:
    for name in ("fusermount3", "fusermount"):
        binary = shutil.which(name)
        if binary:
            return binary
    raise MountError("fusermount3/fusermount not found (install fuse3)")


# ---------------------------------------------------------------------- mount
def mount_fuse(image_path: str, mount_point: str | None = None) -> MountInfo:
    """Mount *image_path* with fuseiso.  Returns the resulting :class:`MountInfo`."""
    if not shutil.which("fuseiso"):
        raise MountError("fuseiso is not installed (e.g. 'sudo apt install fuseiso')")
    mount_point = mount_point or make_mount_point(image_path)
    _run(["fuseiso", image_path, mount_point])
    return MountInfo(mount_point=mount_point, image_file=image_path, method=METHOD_FUSE)


def mount_loop(image_path: str) -> MountInfo:
    """Attach *image_path* to a loop device and mount it through udisks2."""
    for binary in ("udisksctl",):
        if not shutil.which(binary):
            raise MountError("udisksctl is not installed (package: udisks2)")

    setup = _run(["udisksctl", "loop-setup", "-f", image_path, "--no-user-interaction"])
    match = re.search(r"(/dev/loop\d+)", setup.stdout or "")
    if not match:
        raise MountError("Could not determine the loop device:\n%s" % (setup.stdout or "").strip())
    device = match.group(1)

    try:
        mounted = _run(["udisksctl", "mount", "-b", device, "--no-user-interaction"])
    except MountError:
        # Roll back the loop device so it does not leak
        _run(["udisksctl", "loop-delete", "-b", device], check=False)
        raise

    match = re.search(r"at\s+(.+?)\.?\s*$", (mounted.stdout or "").strip())
    mount_point = match.group(1).strip() if match else ""
    if not mount_point:
        mount_point = find_loop_device_by_source(device)
    return MountInfo(
        mount_point=mount_point,
        image_file=image_path,
        method=METHOD_LOOP,
        device=device,
    )


def find_loop_device_by_source(device: str) -> str:
    """Return the mount point of *device* from /proc/mounts."""
    try:
        with open("/proc/mounts", "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == device:
                    return parts[1]
    except OSError:
        pass
    return ""


# -------------------------------------------------------------------- unmount
def unmount(info: MountInfo) -> None:
    """Undo a mount created by :func:`mount_fuse` / :func:`mount_loop`."""
    if info.method == METHOD_LOOP:
        device = info.device or find_loop_device(info.mount_point)
        if device:
            _run(["udisksctl", "unmount", "-b", device, "--no-user-interaction"])
            _run(["udisksctl", "loop-delete", "-b", device], check=False)
        if info.mount_point and os.path.isdir(info.mount_point):
            try:
                os.rmdir(info.mount_point)
            except OSError:
                pass  # udisksctl created and removed it for us
        return

    # FUSE
    fusermount = _fusermount_binary()
    _run([fusermount, "-u", info.mount_point])
    if info.mount_point and os.path.isdir(info.mount_point):
        try:
            os.rmdir(info.mount_point)
        except OSError:
            pass
