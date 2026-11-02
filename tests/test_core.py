"""Functional tests for the GUI-independent core (run with python3)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from furiusisomount.core.checksum import ChecksumError, compute_checksum
from furiusisomount.core.converter import ConversionError, find_associated_bin
from furiusisomount.core.history import HistoryStore, MountedListStore, append_log
from furiusisomount.core.mounts import MountInfo, make_mount_point

failures = []


def check(name, condition, detail=""):
    if condition:
        print("PASS", name)
    else:
        print("FAIL", name, detail)
        failures.append(name)


with tempfile.TemporaryDirectory() as tmp:
    # --- checksum ------------------------------------------------------------
    img = os.path.join(tmp, "test.iso")
    with open(img, "wb") as fh:
        fh.write(b"hello furius " * 1000)
    import hashlib
    expected_md5 = hashlib.md5(b"hello furius " * 1000).hexdigest()
    seen = []
    digest = compute_checksum(img, "md5", progress=seen.append)
    check("checksum md5", digest == expected_md5, digest)
    check("checksum progress", seen and seen[-1] == 100, str(seen))
    digest = compute_checksum(img, "sha1")
    check("checksum sha1", digest == hashlib.sha1(b"hello furius " * 1000).hexdigest())

    try:
        compute_checksum(os.path.join(tmp, "missing.iso"))
        check("checksum missing file raises", False)
    except ChecksumError:
        check("checksum missing file raises", True)

    cancelled = compute_checksum  # noqa
    try:
        compute_checksum(img, "md5", should_cancel=lambda: True)
        check("checksum cancel raises", False)
    except ChecksumError:
        check("checksum cancel raises", True)

    # --- history -------------------------------------------------------------
    hist_file = os.path.join(tmp, "history.txt")
    store = HistoryStore(hist_file, limit=3)
    for i in range(5):
        store.add("/img/%d.iso" % i)
    check("history limit", store.items == ["/img/4.iso", "/img/3.iso", "/img/2.iso"], str(store.items))
    store2 = HistoryStore(hist_file, limit=3).load()
    check("history persistence", store2 == store.items, str(store2))

    # --- mounted list ----------------------------------------------------------
    mlist = MountedListStore(os.path.join(tmp, "mounted.csv"))
    info = MountInfo(mount_point="/mnt/a", image_file="/img/a.iso", method="FUSE", device="")
    loop_info = MountInfo(mount_point="/run/media/u/LABEL", image_file="/img/b.iso", method="Loop", device="/dev/loop3")
    mlist.save([info, loop_info])
    loaded = mlist.load()
    check("mounted list roundtrip", loaded == [info, loop_info], str(loaded))

    # --- log --------------------------------------------------------------------
    log_file = os.path.join(tmp, "log.txt")
    append_log(log_file, "hello")
    append_log(log_file, "world")
    with open(log_file) as fh:
        lines = fh.read().strip().splitlines()
    check("log append", len(lines) == 2 and lines[0].endswith("hello") and lines[1].endswith("world"))

    # --- converter --------------------------------------------------------------
    cue = os.path.join(tmp, "game.cue")
    with open(cue, "w") as fh:
        fh.write('FILE "game.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
    check("find_associated_bin none", find_associated_bin(cue) is None)
    with open(os.path.join(tmp, "game.bin"), "wb") as fh:
        fh.write(b"\x00" * 2352)
    check("find_associated_bin", find_associated_bin(cue) == os.path.join(tmp, "game.bin"))
    try:
        from furiusisomount.core.converter import convert_bin_cue
        convert_bin_cue(os.path.join(tmp, "nope.cue"), os.path.join(tmp, "out.iso"))
        check("convert missing cue raises", False)
    except ConversionError:
        check("convert missing cue raises", True)

    # --- make_mount_point ---------------------------------------------------------
    root = os.path.join(tmp, "home")
    os.mkdir(root)
    p1 = make_mount_point("/images/My Disc (2026).iso", root)
    p2 = make_mount_point("/images/My Disc (2026).iso", root)
    check("mount point unique", p1 != p2 and os.path.isdir(p2), "%s %s" % (p1, p2))
    check("mount point sanitized", " " not in os.path.basename(p1) and "(" not in os.path.basename(p1), p1)

print()
if failures:
    print("FAILURES:", failures)
    sys.exit(1)
print("ALL CORE TESTS PASSED")
