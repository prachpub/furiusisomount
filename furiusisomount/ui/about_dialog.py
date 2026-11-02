"""About dialog: big centered icon on the left, credits on the right.

The email and the project website are clickable links (``mailto:`` opens the
system mail client, ``https://`` opens the default web browser).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..app_info import (
    APP_DISPLAY_NAME,
    LICENSE,
    MAINTAINER_EMAIL,
    MAINTAINER_NAME,
    ORIGINAL_AUTHOR_EMAIL,
    ORIGINAL_AUTHOR_NAME,
    PROJECT_URL,
    VERSION,
)
from ..paths import icon_path

ICON_SIZE = 192  # px, "que el icono quede centrado y se vea grande"


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About {app}").format(app=APP_DISPLAY_NAME))
        self.setModal(True)

        # ---------------------------------------------------------- left: icon
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = self._load_icon()
        if pixmap is not None:
            icon_label.setPixmap(pixmap)
        else:  # pragma: no cover - fallback when the PNG is missing
            icon_label.setText("💿")
            font = QFont()
            font.setPointSize(48)
            icon_label.setFont(font)

        left_panel = QVBoxLayout()
        left_panel.addStretch()
        left_panel.addWidget(icon_label)
        left_panel.addStretch()

        # ----------------------------------------------------------- right: text
        text_label = QLabel(self._html())
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        text_label.setOpenExternalLinks(False)  # handled by _open_link()
        text_label.setWordWrap(True)
        text_label.setContentsMargins(8, 8, 8, 8)
        text_label.linkActivated.connect(self._open_link)

        right_panel = QVBoxLayout()
        right_panel.addWidget(text_label)
        right_panel.addStretch()

        # ------------------------------------------------------------- assembly
        content = QHBoxLayout()
        content.addLayout(left_panel)
        content.addWidget(self._separator())
        content.addLayout(right_panel, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(content)
        layout.addWidget(buttons)

        self.setMinimumWidth(620)

    # ------------------------------------------------------------------ helper
    def _load_icon(self) -> QPixmap | None:
        path = icon_path()
        pixmap = QPixmap(path) if path else QPixmap()
        if pixmap.isNull():
            return None
        return pixmap.scaled(
            ICON_SIZE,
            ICON_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _separator(self) -> QLabel:
        line = QLabel()
        line.setFrameShape(QLabel.Shape.VLine)
        line.setFrameShadow(QLabel.Shadow.Sunken)
        return line

    def _open_link(self, url: str) -> None:
        """Open the clicked link with the system default application."""
        QDesktopServices.openUrl(QUrl(url))

    def _html(self) -> str:
        description = self.tr(
            "A simple application to mount ISO, IMG, BIN, MDF and NRG disc "
            "images without burning them to a disc. It also converts BIN/CUE "
            "images to ISO."
        )
        label_original = self.tr("Original author")
        label_maintainer = self.tr("PyQt6 fork maintained by")
        label_email = self.tr("Email")
        label_website = self.tr("Website")
        label_license = self.tr("License")
        label_tech = self.tr("Technologies used")

        mail_link = '<a href="mailto:{email}">{email}</a>'.format(email=MAINTAINER_EMAIL)
        web_link = '<a href="{url}">{url}</a>'.format(url=PROJECT_URL)

        return (
            "<h2>{app}</h2>"
            "<p><b>{version}</b></p>"
            "<p>{description}</p>"
            "<hr>"
            "<p><b>{label_original}:</b> {original} &lt;{original_email}&gt;</p>"
            "<p><b>{label_maintainer}:</b> {maintainer}</p>"
            "<p><b>{label_email}:</b> {mail_link}</p>"
            "<p><b>{label_website}:</b> {web_link}</p>"
            "<p><b>{label_license}:</b> {license}</p>"
            "<p><b>{label_tech}:</b> {techs}</p>"
        ).format(
            app=APP_DISPLAY_NAME,
            version=self.tr("Version {version}").format(version=VERSION),
            description=description,
            label_original=label_original,
            original=ORIGINAL_AUTHOR_NAME,
            original_email=ORIGINAL_AUTHOR_EMAIL,
            label_maintainer=label_maintainer,
            maintainer=MAINTAINER_NAME,
            label_email=label_email,
            mail_link=mail_link,
            label_website=label_website,
            web_link=web_link,
            label_license=label_license,
            license=LICENSE,
            label_tech=label_tech,
            techs=self.tr("Python 3, PyQt6, fuseiso, udisks2, bchunk, brasero/wodim"),
        )
