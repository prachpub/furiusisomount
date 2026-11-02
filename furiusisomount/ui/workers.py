"""Background workers (QThread based) so the GUI never freezes.

The historical implementation calculated checksums and ran conversions in the
main thread with ``processEvents()`` loops; both moved to real worker threads.

Follows the canonical Qt pattern: worker moved to a QThread, the thread is
quit when the worker finishes, and everything is deleted with ``deleteLater``.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from ..core.checksum import ChecksumError, compute_checksum
from ..core.converter import ConversionError, convert_bin_cue


class ChecksumWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, image_path: str, algorithm: str, log_message=None):
        super().__init__()
        self.image_path = image_path
        self.algorithm = algorithm
        self.log_message = log_message
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            digest = compute_checksum(
                self.image_path,
                self.algorithm,
                progress=self.progress.emit,
                should_cancel=lambda: self._cancelled,
            )
        except ChecksumError as exc:
            if str(exc) == "cancelled":
                self.cancelled.emit()
            else:
                self.failed.emit(str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(str(exc))
            return
        self.finished.emit(digest)


class ConvertWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, cue_path: str, iso_path: str, log_message=None):
        super().__init__()
        self.cue_path = cue_path
        self.iso_path = iso_path
        self.log_message = log_message

    def run(self) -> None:
        try:
            result = convert_bin_cue(
                self.cue_path,
                self.iso_path,
                log=self.log_message or (lambda _msg: None),
                progress=self.progress.emit,
            )
        except ConversionError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


def start_worker(worker: QObject, parent: QObject | None = None) -> QThread:
    """Move *worker* into a fresh QThread, start it and return the thread.

    The thread stops itself when the worker emits ``finished`` or ``failed``.
    Callers keep a reference (``self._thread``) and call :func:`stop_worker`
    on shutdown.
    """
    thread = QThread(parent) if parent is not None else QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    for signal_name in ("finished", "failed", "cancelled"):
        signal = getattr(worker, signal_name, None)
        if signal is not None:
            signal.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread


def stop_worker(thread: QThread | None, worker: QObject | None = None, timeout_ms: int = 5000) -> None:
    """Cancel (if possible), quit and wait for *thread*.  Safe at shutdown."""
    if thread is None:
        return
    cancel = getattr(worker, "cancel", None)
    if callable(cancel):
        cancel()
    thread.quit()
    if not thread.wait(timeout_ms):
        thread.terminate()  # last resort, only while the app is closing
        thread.wait(1000)
