"""Convert tab: BIN/CUE -> ISO using bchunk (runs in a worker thread)."""

from __future__ import annotations

import os
from typing import Callable

from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.converter import ConversionError, find_associated_bin
from .workers import ConvertWorker, start_worker, stop_worker


class ConvertTab(QWidget):
    def __init__(self, log: Callable[[str], None], parent: QWidget | None = None):
        super().__init__(parent)
        self.log = log
        self._convert_thread = None
        self._convert_worker = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        cue_group = QGroupBox(self.tr("Convert BIN/CUE to ISO"))
        cue_layout = QHBoxLayout()
        self.cue_line = QLineEdit()
        self.cue_line.setPlaceholderText(self.tr("Select the .cue file"))
        cue_browse = QPushButton(self.tr("Browse..."))
        cue_browse.clicked.connect(self.browse_cue)
        cue_layout.addWidget(self.cue_line, 1)
        cue_layout.addWidget(cue_browse)
        cue_group.setLayout(cue_layout)

        self.convert_button = QPushButton(self.tr("Convert to ISO"))
        self.convert_button.clicked.connect(self.convert_bin_cue)
        self.convert_button.setStyleSheet("font-weight: bold;")

        self.convert_progress = QProgressBar()
        self.convert_progress.setRange(0, 100)
        self.convert_progress.setFormat(self.tr("Ready to convert"))

        layout.addWidget(cue_group)
        layout.addWidget(self.convert_button)
        layout.addWidget(self.convert_progress)
        layout.addStretch()

    # ------------------------------------------------------------------ action
    def browse_cue(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select CUE file"),
            os.path.expanduser("~"),
            self.tr("CUE files (*.cue)"),
        )
        if file_path:
            self.cue_line.setText(file_path)

    def set_cue_file(self, file_path: str) -> None:
        """Programmatic selection (used by drag & drop)."""
        self.cue_line.setText(file_path)

    def convert_bin_cue(self) -> None:
        if self._convert_worker is not None:
            return

        cue_path = self.cue_line.text().strip()
        if not cue_path:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select a .cue file"))
            return
        if not os.path.isfile(cue_path):
            QMessageBox.warning(self, self.tr("Error"), self.tr("The .cue file does not exist"))
            return
        if not find_associated_bin(cue_path):
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("No associated .bin file was found for:\n{cue}").format(cue=cue_path),
            )
            return

        default_iso = os.path.splitext(os.path.basename(cue_path))[0] + ".iso"
        default_dir = os.path.dirname(cue_path) or os.path.expanduser("~")
        iso_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save ISO as"),
            os.path.join(default_dir, default_iso),
            self.tr("ISO images (*.iso)"),
        )
        if not iso_path:
            return

        worker = ConvertWorker(cue_path, iso_path, log_message=self.log)
        worker.progress.connect(self._on_convert_progress)
        worker.finished.connect(self._on_convert_done)
        worker.failed.connect(self._on_convert_error)

        self._convert_worker = worker
        self.convert_button.setEnabled(False)
        self.convert_progress.setValue(0)
        self.convert_progress.setFormat(self.tr("Converting... %p%"))
        self._convert_thread = start_worker(worker, self)

    # ----------------------------------------------------------------- results
    def _reset_convert_ui(self) -> None:
        self._convert_worker = None
        self._convert_thread = None
        self.convert_button.setEnabled(True)

    def shutdown(self) -> None:
        """Stop background work cleanly before the window closes."""
        stop_worker(self._convert_thread, self._convert_worker)
        self._convert_thread = None
        self._convert_worker = None

    def _on_convert_progress(self, percent: int, _line: str) -> None:
        self.convert_progress.setValue(percent)

    def _on_convert_done(self, iso_path: str) -> None:
        self.convert_progress.setValue(100)
        self.convert_progress.setFormat(self.tr("Conversion completed"))
        self.log("conversion finished: %s" % iso_path)
        QMessageBox.information(
            self,
            self.tr("Success"),
            self.tr("ISO created:\n{iso}").format(iso=iso_path),
        )
        self._reset_convert_ui()

    def _on_convert_error(self, message: str) -> None:
        self.convert_progress.setFormat(self.tr("Conversion error"))
        self.log("conversion failed: %s" % message)
        QMessageBox.critical(
            self,
            self.tr("Error"),
            self.tr("Could not convert:\n{error}").format(error=message),
        )
        self._reset_convert_ui()
