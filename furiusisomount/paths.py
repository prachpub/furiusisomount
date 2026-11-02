"""Filesystem locations used by the application.

The layout matches the historical Furius ISO Mount layout so that data from
older versions keeps working:

    ~/.furiusisomount/
        FuriusMountLog.txt      - append only activity log
        FuriusMountList.csv     - mounted images (mount point, image, method)
        FuriusMountHistory.txt  - recent image files
        settings.cfg            - misc settings
"""

from __future__ import annotations

import configparser
import glob
import os
from dataclasses import dataclass, field

from .app_info import APP_NAME


@dataclass
class AppPaths:
    home_directory: str = field(default_factory=lambda: os.path.expanduser("~"))
    settings_directory: str = ""
    mount_log: str = ""
    mount_list: str = ""
    history_list: str = ""
    settings_file: str = ""

    def __post_init__(self) -> None:
        if not self.settings_directory:
            self.settings_directory = os.path.join(self.home_directory, ".furiusisomount")
        self.mount_log = os.path.join(self.settings_directory, "FuriusMountLog.txt")
        self.mount_list = os.path.join(self.settings_directory, "FuriusMountList.csv")
        self.history_list = os.path.join(self.settings_directory, "FuriusMountHistory.txt")
        self.settings_file = os.path.join(self.settings_directory, "settings.cfg")

    # ------------------------------------------------------------------ setup
    def ensure_directories(self) -> None:
        os.makedirs(self.settings_directory, exist_ok=True)
        if not os.path.exists(self.settings_file):
            self.save_settings({"mount_point": self.home_directory})

    # --------------------------------------------------------------- settings
    def load_settings(self) -> dict:
        config = configparser.ConfigParser()
        settings = {"mount_point": self.home_directory}
        try:
            config.read(self.settings_file)
            if config.has_section("mount_options"):
                value = config.get("mount_options", "mount_point", fallback="").strip()
                if value:
                    settings["mount_point"] = value
        except (OSError, configparser.Error):
            pass
        return settings

    def save_settings(self, settings: dict) -> None:
        config = configparser.ConfigParser()
        config["mount_options"] = {"mount_point": settings.get("mount_point", self.home_directory)}
        try:
            os.makedirs(self.settings_directory, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as handle:
                config.write(handle)
        except OSError:
            pass


def resource_path(*parts: str) -> str:
    """Absolute path of a file shipped inside the project tree."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def icon_path() -> str:
    """Path of the application icon (PNG), used by the about dialog and window.

    Lookup order: the project tree (git checkout), the private data directory
    used by the Debian package, and the standard hicolor/pixmap locations.
    """
    candidates = [
        resource_path("resources", "icons", "furiusisomount.png"),
        resource_path("resources", "icons", "furiusisomount.svg"),
        "/usr/share/%s/icons/furiusisomount.png" % APP_NAME,
    ]
    # hicolor icon theme: /usr/share/icons/hicolor/<size>/apps/<name>.png
    candidates += sorted(glob.glob("/usr/share/icons/hicolor/*/apps/furiusisomount.png"))
    candidates += [
        "/usr/share/pixmaps/furiusisomount.png",
        "/usr/local/share/pixmaps/furiusisomount.png",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""
