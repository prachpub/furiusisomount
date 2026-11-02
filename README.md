# Furius ISO Mount

A simple application (PyQt6) for **mounting disc images** (ISO, IMG, BIN, MDF, and NRG)
without the need to burn them, featuring additional tools: MD5/SHA1 checksums,
image burning, and **BIN/CUE → ISO** conversion.

*A simple PyQt6 application to mount ISO/IMG/BIN/MDF/NRG disc images without burning
them, with MD5/SHA1 checksums, image burning and BIN/CUE → ISO conversion.*

---

## About

| | |
|---|---|
| **Version** | 0.11.3.1 |
| **Original Author** | Dean Harris &lt;marcus_furius@hotmail.com&gt; |
| **PyQt6 & Modular Fork** | Washington Indacochea Delgado |
| **Email** | [linuxfrontier@proton.me](mailto:linuxfrontier@proton.me) |
| **Website** | <https://github.com/wachin/furiusisomount> |
| **License** | GPL v3 |
| **Technologies** | Python 3, PyQt6, fuseiso, udisks2, bchunk, brasero/wodim |

The original project (<https://github.com/prachpub/furiusisomount>) was abandoned years
ago; this fork modernizes it with: **modular architecture**, **multi-language interface**
(Qt Linguist), bug fixes, and a revamped *About* dialog. ## Requirements

```bash
# Debian / Ubuntu
sudo apt install python3-pyqt6 fuseiso bchunk udisks2 brasero lsof
# Fedora
sudo dnf install python3-qt6 fuseiso bchunk udisks2 brasero lsof
```

## Running

```bash
python3 main.py            # from the repository
```

![](images/furius-iso-mount-ezgif.com.gif)


## Running from deb

If you create the deb package and install it then alternative from the system Applications you can run with:

```bash
furiusisomount             # if installed (.deb package)
```

also to see the version from terminal:

```bash
furiusisomount --version   # program version
```

Forced language (optional):

```bash
FURIUSISOMOUNT_LANG=es python3 main.py
```

## Project structure

```
furiusisomount/
├── main.py                    # entry point
├── furiusisomount/            # main package
│   ├── app_info.py            # metadata (version, credits, license)
│   ├── paths.py               # configuration/resource paths
│   ├── i18n.py                # translation loading (Qt Linguist)
│   ├── core/                  # interface-independent logic
│   │   ├── mounts.py          # mount/unmount (FUSE and loop/udisks2)
│   │   ├── checksum.py        # MD5/SHA1 with progress and cancellation
│   │   ├── converter.py       # BIN/CUE → ISO (bchunk)
│   │   ├── burner.py          # burning (brasero/wodim)
│   │   └── history.py         # history, mount list, and logging
│   └── ui/                    # PyQt6 interface
│       ├── main_window.py     # main window (tabs + drag & drop)
│       ├── mount_tab.py       # "Mount image" tab
│       ├── convert_tab.py     # "Convert BIN/CUE" tab
│       ├── about_dialog.py    # "About" dialog
│       └── workers.py         # worker threads
``` (checksum/conversion)
├── resources/icons/           # program icon
├── translations/              # Qt Linguist .ts / .qm files
├── debian/                    # Debian packaging (policy + lintian)
├── scripts/update_translations.sh
├── data/                      # .desktop, AppStream metainfo
└── tests/test_core.py         # logic tests (headless/no GUI)
```

## Debian Packaging

The `debian/` directory allows for building a package that complies with
Debian Policy and passes lintian checks without errors:

```bash
# Build the binary package and the source package
apt install debhelper dh-python python3-all python3-setuptools \
pybuild-plugin-pyproject lintian

dpkg-buildpackage -us -uc -b          # binary only
dpkg-buildpackage -us -uc -S          # source (3.0 native format)

# Check with lintian
lintian ../furiusisomount_0.11.3.1_*.changes

# Automated tests (autopkgtest)
autopkgtest . -- null                 # or against a schroot/sbuild environment
```

Included in the packaging:

- `debian/control` — dependencies, `Standards-Version: 4.7.4`, `Testsuite: autopkgtest`
- `debian/copyright` — DEP-5 format (GPL-3+)
- `debian/rules` — `dh` with `pybuild` (Python build system)
- `debian/furiusisomount.1` — man page
- `data/furiusisomount.metainfo.xml` — AppStream metadata
- `data/furiusisomount.desktop` — desktop shortcut
- `debian/tests/` — autopkgtest smoke test
- icon in `hicolor/128x128`, `.qm` translations in `/usr/share/furiusisomount/`

## Multilanguage (Qt Linguist)

The base language is **English**: all strings use `self.tr("...")` and are extracted
automatically.

```bash
# 1. Extract strings and create/update .ts files (default: es and fr)
./scripts/update_translations.sh
LANGS="es fr pt de" ./scripts/update_translations.sh

# 2. Translate using Qt Linguist
linguist translations/furiusisomount_pt.ts

# 3. Compile to .qm (handled by the script if lrelease is found)
./scripts/update_translations.sh
```

Included languages: **English** (source code) plus **Spanish, French, Portuguese,
German, Italian, Japanese, Russian, and Simplified Chinese** (all complete, 81/81
strings, in `.ts` and `.qm` formats). At runtime, `furiusisomount_<locale>.qm` is loaded based on the system language (or `FURIUSISOMOUNT_LANG`), along with the standard Qt translations (dialog buttons
