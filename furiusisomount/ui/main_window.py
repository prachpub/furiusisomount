"""Main window: two tabs (mount / convert), log tools and the about dialog."""

from __future__ import annotations

import os
import shutil
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..app_info import APP_DISPLAY_NAME
from ..core.history import HistoryStore, MountedListStore, append_log
from ..paths import AppPaths, icon_path
from .about_dialog import AboutDialog
from .convert_tab import ConvertTab
from .mount_tab import MountTab

IMAGE_EXTENSIONS = (".iso", ".img", ".bin", ".mdf", ".nrg")


class FuriusIsoMount(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setGeometry(100, 100, 820, 640)

        icon_file = icon_path()
        if icon_file:
            self.setWindowIcon(QIcon(icon_file))

        # Shared services -----------------------------------------------------
        self.paths = AppPaths()
        self.paths.ensure_directories()
        self.history = HistoryStore(self.paths.history_list)
        self.mount_store = MountedListStore(self.paths.mount_list)

        # UI ------------------------------------------------------------------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.mount_tab = MountTab(self.paths, self.history, self.mount_store, self.log)
        self.convert_tab = ConvertTab(self.log)
        self.tabs.addTab(self.mount_tab, self.tr("Mount Image"))
        self.tabs.addTab(self.convert_tab, self.tr("Convert BIN/CUE"))
        layout.addWidget(self.tabs)

        # Bottom bar -----------------------------------------------------------
        bottom_layout = QHBoxLayout()
        log_button = QPushButton(self.tr("View Log"))
        log_button.clicked.connect(self.view_log)
        clear_log_button = QPushButton(self.tr("Clear Log"))
        clear_log_button.clicked.connect(self.clear_log)
        about_button = QPushButton(self.tr("About"))
        about_button.clicked.connect(self.show_about)
        bottom_layout.addWidget(log_button)
        bottom_layout.addWidget(clear_log_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(about_button)
        layout.addLayout(bottom_layout)

        # Drag & drop -----------------------------------------------------------
        self.setAcceptDrops(True)

    # ----------------------------------------------------------------- logging
    def log(self, message: str) -> None:
        append_log(self.paths.mount_log, message)

    def view_log(self) -> None:
        if not os.path.exists(self.paths.mount_log):
            QMessageBox.information(self, self.tr("Information"), self.tr("No log file available"))
            return
        opener = shutil.which("xdg-open")
        if opener is None:  # pragma: no cover - non Linux systems
            QMessageBox.information(
                self,
                self.tr("Information"),
                self.tr("The log is at:\n{path}").format(path=self.paths.mount_log),
            )
            return
        try:
            subprocess.Popen([opener, self.paths.mount_log])
        except OSError as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Could not open the log:\n{error}").format(error=exc),
            )

    def clear_log(self) -> None:
        if not os.path.exists(self.paths.mount_log):
            QMessageBox.information(
                self, self.tr("Information"), self.tr("There is no log file to delete")
            )
            return
        answer = QMessageBox.question(
            self,
            self.tr("Confirm"),
            self.tr("Do you want to delete the log file?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            os.remove(self.paths.mount_log)
            QMessageBox.information(self, self.tr("Success"), self.tr("Log file deleted"))
        except OSError as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Could not delete the log:\n{error}").format(error=exc),
            )

    # ------------------------------------------------------------------- about
    def show_about(self) -> None:
        AboutDialog(self).exec()

    # ------------------------------------------------------------ drag & drop
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            file_path = url.toLocalFile()
            lower = file_path.lower()
            if lower.endswith(IMAGE_EXTENSIONS):
                self.tabs.setCurrentWidget(self.mount_tab)
                self.mount_tab.set_image(file_path)
                return
            if lower.endswith(".cue"):
                self.tabs.setCurrentWidget(self.convert_tab)
                self.convert_tab.set_cue_file(file_path)
                return

    # --------------------------------------------------------------- lifecycle
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self.mount_tab.shutdown()
        self.convert_tab.shutdown()
        self.mount_store.save(self.mount_tab.mounted_images)
        super().closeEvent(event)
