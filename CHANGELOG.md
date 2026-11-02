# Changelog

All notable changes to this project are documented here.

## 0.11.3.1 - 2026-10-05

### Added

- Modular architecture: `core/` (mounts, checksum, converter, burner, history),
  `ui/` (main window, tabs, about dialog, workers) and `i18n/`-style helpers.
- Multi-language interface with Qt Linguist: English (source), Spanish, French,
  Portuguese, German, Italian, Japanese, Russian and Chinese Simplified.
- New about dialog: large centered icon on the left, credits on the right and
  clickable e-mail (`mailto:`) and website links.
- BIN/CUE to ISO conversion tab (bchunk).
- Debian packaging (`debian/`), man page, AppStream metadata and autopkgtest.
- Console entry point with `--help` and `--version`.

### Fixed

- `re` module was used without being imported, breaking BIN/CUE conversion.
- Checksum and conversion ran in the GUI thread and froze the window; both now
  run in worker threads with real progress and a cancel button.
- The loop device was hard-coded to `/dev/loop0`; udisks2 now reports the real
  device and mount point.
- Commands were executed through a shell with manual quoting; they now use
  argument lists (spaces in paths are safe).
- The bchunk output name was assumed (`base01.iso`); it is detected with glob.
- `fusermount3` is supported (fuse3).
- The image selection was lost when the history combo box was refreshed.
- Duplicated mount points when the mount directory already existed.
- Worker threads were destroyed while running at application exit.
- `settings.cfg` was written but never used; it now sets the base mount folder.

## 0.11.3 (historical, upstream)

- Last release of the original Furius ISO Mount by Dean Harris.
