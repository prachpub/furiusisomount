"""Mount tab: select an image, mount/unmount it, checksum, burn."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core import burner, mounts
from ..core.checksum import SUPPORTED_ALGORITHMS
from ..core.history import HistoryStore, MountedListStore
from ..core.mounts import MountError, MountInfo
from ..paths import AppPaths
from .workers import ChecksumWorker, start_worker, stop_worker

IMAGE_FILTER = "Disc images (*.iso *.img *.bin *.mdf *.nrg);;All files (*)"


class MountTab(QWidget):
    def __init__(
        self,
        paths: AppPaths,
        history: HistoryStore,
        mount_store: MountedListStore,
        log: Callable[[str], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.paths = paths
        self.history = history
        self.mount_store = mount_store
        self.log = log

        self.settings = paths.load_settings()
        self.mounted_images: list[MountInfo] = []
        self.current_mount: MountInfo | None = None

        self._checksum_thread = None
        self._checksum_worker = None
        self._current_algorithm = "md5"

        self._init_ui()
        self._load_state()

    # --------------------------------------------------------------------- UI
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Image selection ------------------------------------------------------
        image_group = QGroupBox(self.tr("Select Image"))
        image_layout = QHBoxLayout()
        self.image_combo = QComboBox()
        self.image_combo.setEditable(True)
        self.image_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.image_combo.addItem("")
        self.image_combo.setCurrentIndex(0)
        browse_button = QPushButton(self.tr("Browse..."))
        browse_button.clicked.connect(self.browse_image)
        image_layout.addWidget(QLabel(self.tr("Image:")))
        image_layout.addWidget(self.image_combo, 1)
        image_layout.addWidget(browse_button)
        image_group.setLayout(image_layout)

        # Options ---------------------------------------------------------------
        options_group = QGroupBox(self.tr("Options"))
        options_layout = QHBoxLayout()
        self.fuse_radio = QRadioButton(self.tr("FUSE"))
        self.fuse_radio.setChecked(True)
        self.loop_radio = QRadioButton(self.tr("Loop"))
        self.md5_radio = QRadioButton(self.tr("MD5"))
        self.md5_radio.setChecked(True)
        self.sha1_radio = QRadioButton(self.tr("SHA1"))
        options_layout.addWidget(QLabel(self.tr("Method:")))
        options_layout.addWidget(self.fuse_radio)
        options_layout.addWidget(self.loop_radio)
        options_layout.addStretch()
        options_layout.addWidget(QLabel(self.tr("Checksum:")))
        options_layout.addWidget(self.md5_radio)
        options_layout.addWidget(self.sha1_radio)
        options_group.setLayout(options_layout)

        # Action buttons ---------------------------------------------------------
        actions_layout = QHBoxLayout()
        self.mount_button = QPushButton(self.tr("Mount"))
        self.mount_button.clicked.connect(self.mount_image)
        self.unmount_button = QPushButton(self.tr("Unmount"))
        self.unmount_button.clicked.connect(self.unmount_image)
        self.unmount_button.setEnabled(False)
        self.checksum_button = QPushButton(self.tr("Checksum"))
        self.checksum_button.clicked.connect(self.toggle_checksum)
        self.burn_button = QPushButton(self.tr("Burn"))
        self.burn_button.clicked.connect(self.burn_image)
        actions_layout.addWidget(self.mount_button)
        actions_layout.addWidget(self.unmount_button)
        actions_layout.addWidget(self.checksum_button)
        actions_layout.addWidget(self.burn_button)

        # Progress ---------------------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat(self.tr("No checksum calculated"))

        # Mounted images ----------------------------------------------------------
        self.mounted_list = QTreeWidget()
        self.mounted_list.setHeaderLabels(
            [self.tr("Mount point"), self.tr("Image file"), self.tr("Method")]
        )
        self.mounted_list.setColumnWidth(0, 260)
        self.mounted_list.setColumnWidth(1, 260)
        self.mounted_list.itemSelectionChanged.connect(self.update_selected_mount)

        mounted_group = QGroupBox(self.tr("Mounted images"))
        mounted_layout = QVBoxLayout()
        mounted_layout.addWidget(self.mounted_list)
        mounted_group.setLayout(mounted_layout)

        layout.addWidget(image_group)
        layout.addWidget(options_group)
        layout.addLayout(actions_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(mounted_group, 1)

        self.image_combo.currentTextChanged.connect(self._on_image_changed)

    # ------------------------------------------------------------------- state
    def _load_state(self) -> None:
        self.history.load()
        self.image_combo.clear()
        self.image_combo.addItems(self.history.items)
        if self.history.items:
            self.image_combo.setCurrentIndex(0)
        self.mounted_images = self.mount_store.load()
        self._refresh_mounted_list()

    def _refresh_mounted_list(self) -> None:
        self.mounted_list.clear()
        for info in self.mounted_images:
            item = QTreeWidgetItem([info.mount_point, info.image_file, info.method])
            item.setData(0, Qt.ItemDataRole.UserRole, info)
            self.mounted_list.addTopLevelItem(item)

    def _on_image_changed(self, text: str) -> None:
        self.current_image = text.strip()

    @property
    def current_image(self) -> str:
        return self.image_combo.currentText().strip()

    @current_image.setter
    def current_image(self, value: str) -> None:
        self.image_combo.setCurrentText(value)

    def set_image(self, file_path: str) -> None:
        """Programmatic selection (used by drag & drop and the convert tab)."""
        self.current_image = file_path

    # ------------------------------------------------------------------ images
    def browse_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select image"),
            self.settings.get("mount_point", self.paths.home_directory),
            IMAGE_FILTER,
        )
        if file_path:
            self.current_image = file_path

    # ------------------------------------------------------------------- mount
    def mount_image(self) -> None:
        image = self.current_image
        if not image:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select an image file"))
            return

        try:
            if self.fuse_radio.isChecked():
                mount_point = mounts.make_mount_point(
                    image, self.settings.get("mount_point", self.paths.home_directory)
                )
                info = mounts.mount_fuse(image, mount_point)
            else:
                info = mounts.mount_loop(image)
        except MountError as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Could not mount the image:\n{error}").format(error=exc),
            )
            self.log("mount failed: %s" % exc)
            return
        except OSError as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Could not mount the image:\n{error}").format(error=exc),
            )
            self.log("mount failed: %s" % exc)
            return

        self.mounted_images.append(info)
        self.mount_store.save(self.mounted_images)
        self._refresh_mounted_list()
        self.history.add(image)
        self._rebuild_history_combo()
        self.log("mounted %s at %s (%s)" % (image, info.mount_point, info.method))
        QMessageBox.information(
            self,
            self.tr("Success"),
            self.tr("Image mounted at\n{mount_point}").format(mount_point=info.mount_point),
        )

    def unmount_image(self) -> None:
        info = self.current_mount
        if info is None:
            return

        if mounts.mount_point_busy(info.mount_point):
            QMessageBox.warning(
                self,
                self.tr("Cannot unmount"),
                self.tr(
                    "Cannot unmount: the mount point is in use.\n"
                    "Close any file manager window that is inside this folder "
                    "and try again."
                ),
            )
            return

        try:
            mounts.unmount(info)
        except MountError as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Could not unmount the image:\n{error}").format(error=exc),
            )
            self.log("unmount failed: %s" % exc)
            return

        self.mounted_images = [m for m in self.mounted_images if m != info]
        self.mount_store.save(self.mounted_images)
        self._refresh_mounted_list()
        self.current_mount = None
        self.unmount_button.setEnabled(False)
        self.log("unmounted %s" % info.mount_point)
        QMessageBox.information(self, self.tr("Success"), self.tr("Image unmounted successfully"))

    def update_selected_mount(self) -> None:
        selected = self.mounted_list.selectedItems()
        if selected:
            self.current_mount = selected[0].data(0, Qt.ItemDataRole.UserRole)
            self.unmount_button.setEnabled(True)
        else:
            self.current_mount = None
            self.unmount_button.setEnabled(False)

    # ---------------------------------------------------------------- checksum
    def toggle_checksum(self) -> None:
        if self._checksum_worker is not None:  # running -> cancel
            self._checksum_worker.cancel()
            return

        image = self.current_image
        if not image:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select an image file"))
            return

        algorithm = "md5" if self.md5_radio.isChecked() else "sha1"
        assert algorithm in SUPPORTED_ALGORITHMS

        worker = ChecksumWorker(image, algorithm)
        self._current_algorithm = algorithm
        worker.progress.connect(self._on_checksum_progress)
        worker.finished.connect(self._on_checksum_done)
        worker.failed.connect(self._on_checksum_error)
        worker.cancelled.connect(self._on_checksum_cancelled)

        self._checksum_worker = worker
        self.checksum_button.setText(self.tr("Cancel"))
        self.mount_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(self.tr("Calculating..."))
        self.log("calculating %s checksum of %s" % (algorithm.upper(), image))
        self._checksum_thread = start_worker(worker, self)

    def _reset_checksum_ui(self) -> None:
        self._checksum_worker = None
        self._checksum_thread = None
        self.checksum_button.setText(self.tr("Checksum"))
        self.mount_button.setEnabled(True)

    def shutdown(self) -> None:
        """Stop background work cleanly before the window closes."""
        stop_worker(self._checksum_thread, self._checksum_worker)
        self._checksum_thread = None
        self._checksum_worker = None

    def _on_checksum_progress(self, percent: int) -> None:
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(self.tr("Calculating... %p%"))

    def _on_checksum_done(self, digest: str) -> None:
        algorithm = self._current_algorithm.upper()
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("%s: %s" % (algorithm, digest))
        self.log("%s checksum of %s: %s" % (algorithm, self.current_image, digest))
        self._reset_checksum_ui()

    def _on_checksum_error(self, message: str) -> None:
        self.progress_bar.setFormat(self.tr("Checksum error"))
        QMessageBox.critical(
            self,
            self.tr("Error"),
            self.tr("Could not calculate the checksum:\n{error}").format(error=message),
        )
        self._reset_checksum_ui()

    def _on_checksum_cancelled(self) -> None:
        self.progress_bar.setFormat(self.tr("Cancelled"))
        self._reset_checksum_ui()

    # -------------------------------------------------------------------- burn
    def burn_image(self) -> None:
        image = self.current_image
        if not image:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select an image file"))
            return
        try:
            program = burner.burn_image(image)
        except burner.BurnError as exc:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Could not start burning:\n{error}").format(error=exc),
            )
            self.log("burn failed: %s" % exc)
            return
        self.log("started burning %s with %s" % (image, program))

    # ------------------------------------------------------------------ helper
    def _rebuild_history_combo(self) -> None:
        current = self.current_image
        self.image_combo.blockSignals(True)
        self.image_combo.clear()
        self.image_combo.addItems(self.history.items)
        if current:
            self.image_combo.setCurrentText(current)
        self.image_combo.blockSignals(False)
