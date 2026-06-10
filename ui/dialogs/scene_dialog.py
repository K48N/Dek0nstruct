"""Auto-detect segments via scene changes or silence breaks."""
from typing import List

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from core.scene_detector import SceneDetector
from core.segment import Segment
from ui.themes.dark_theme import PortfolioTheme


class _DetectionThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, video_path: str, mode: str, ffmpeg_path: str, **kwargs):
        super().__init__()
        self.video_path = video_path
        self.mode = mode
        self.ffmpeg_path = ffmpeg_path
        self.kwargs = kwargs

    def run(self):
        try:
            detector = SceneDetector(self.ffmpeg_path)
            if self.mode == "scene":
                segments = detector.detect_scenes(
                    self.video_path,
                    threshold=self.kwargs.get("threshold", 0.3),
                    min_scene_length=self.kwargs.get("min_scene_length", 2.0),
                    duration=self.kwargs.get("duration", 0.0),
                )
            else:
                segments = detector.detect_silence(
                    self.video_path,
                    noise_threshold=self.kwargs.get("noise_threshold", "-30dB"),
                    min_silence_duration=self.kwargs.get("min_silence_duration", 1.0),
                    duration=self.kwargs.get("duration", 0.0),
                )
            self.finished.emit(segments)
        except Exception as e:
            self.error.emit(str(e))


class SceneDetectionDialog(QDialog):
    segments_detected = pyqtSignal(list)

    def __init__(self, video_path: str, duration: float = 0.0,
                 ffmpeg_path: str = "ffmpeg", parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.duration = duration
        self.ffmpeg_path = ffmpeg_path
        self._thread = None
        self.setWindowTitle("Auto-Detect Segments")
        self.setMinimumSize(480, 380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Automatic Segment Detection")
        title.setStyleSheet(
            f"font-size:18px;font-weight:700;color:{PortfolioTheme.WHITE};padding:10px;"
        )
        layout.addWidget(title)

        # Mode selection
        mode_group = QGroupBox("Detection Mode")
        mode_layout = QVBoxLayout()
        self._mode_group = QButtonGroup()

        self._scene_radio = QRadioButton("Scene Changes")
        self._scene_radio.setChecked(True)
        self._mode_group.addButton(self._scene_radio, 0)
        mode_layout.addWidget(self._scene_radio)
        mode_layout.addWidget(self._hint("Detect visual cuts and transitions"))

        self._silence_radio = QRadioButton("Silent Breaks")
        self._mode_group.addButton(self._silence_radio, 1)
        mode_layout.addWidget(self._silence_radio)
        mode_layout.addWidget(self._hint("Split on silence in the audio track"))

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Scene settings
        self._scene_box = QGroupBox("Scene Settings")
        sl = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel("Sensitivity:"))
        self._threshold_slider = QSlider(Qt.Horizontal)
        self._threshold_slider.setRange(1, 10)
        self._threshold_slider.setValue(3)
        self._threshold_val = QLabel("0.3")
        self._threshold_slider.valueChanged.connect(
            lambda v: self._threshold_val.setText(f"{v / 10:.1f}")
        )
        row.addWidget(self._threshold_slider)
        row.addWidget(self._threshold_val)
        sl.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Min scene length (s):"))
        self._min_scene = QSpinBox()
        self._min_scene.setRange(1, 60)
        self._min_scene.setValue(2)
        row2.addWidget(self._min_scene)
        row2.addStretch()
        sl.addLayout(row2)
        self._scene_box.setLayout(sl)
        layout.addWidget(self._scene_box)

        # Silence settings
        self._silence_box = QGroupBox("Silence Settings")
        self._silence_box.setVisible(False)
        sil = QVBoxLayout()
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Silence threshold (dB):"))
        self._noise_spin = QSpinBox()
        self._noise_spin.setRange(-60, -10)
        self._noise_spin.setValue(-30)
        r1.addWidget(self._noise_spin)
        r1.addStretch()
        sil.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Min silence duration (s):"))
        self._min_silence = QSpinBox()
        self._min_silence.setRange(1, 10)
        self._min_silence.setValue(1)
        r2.addWidget(self._min_silence)
        r2.addStretch()
        sil.addLayout(r2)
        self._silence_box.setLayout(sil)
        layout.addWidget(self._silence_box)

        self._mode_group.buttonClicked.connect(self._on_mode_changed)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};padding:4px;")
        layout.addWidget(self._status)

        layout.addStretch()

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        self._detect_btn = QPushButton("Detect Segments")
        self._detect_btn.setStyleSheet(f"""
            QPushButton {{
                background:{PortfolioTheme.ACCENT};color:{PortfolioTheme.WHITE};
                border:none;border-radius:6px;padding:12px 24px;font-weight:600;
            }}
            QPushButton:hover {{background:{PortfolioTheme.ACCENT_HOVER};}}
            QPushButton:disabled {{background:{PortfolioTheme.GRAY};}}
        """)
        self._detect_btn.clicked.connect(self._start)
        btns.addWidget(self._detect_btn)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        layout.addLayout(btns)

        self.setStyleSheet(f"""
            QDialog {{background:{PortfolioTheme.PRIMARY};}}
            QGroupBox {{
                background:{PortfolioTheme.SECONDARY};border:1px solid {PortfolioTheme.BORDER};
                border-radius:6px;margin-top:10px;padding-top:15px;
                font-weight:600;color:{PortfolioTheme.WHITE};
            }}
            QGroupBox::title {{
                subcontrol-origin:margin;subcontrol-position:top left;
                padding:5px 10px;color:{PortfolioTheme.ACCENT};
            }}
            QLabel {{color:{PortfolioTheme.WHITE};}}
            QPushButton {{
                background:{PortfolioTheme.TERTIARY};color:{PortfolioTheme.WHITE};
                border:1px solid {PortfolioTheme.BORDER};border-radius:4px;padding:8px 16px;
            }}
            QPushButton:hover {{background:{PortfolioTheme.GRAY};}}
            QSpinBox {{
                background:{PortfolioTheme.TERTIARY};color:{PortfolioTheme.WHITE};
                border:1px solid {PortfolioTheme.BORDER};border-radius:4px;padding:5px;
            }}
        """)

    @staticmethod
    def _hint(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;padding-left:24px;")
        return lbl

    def _on_mode_changed(self):
        scene = self._scene_radio.isChecked()
        self._scene_box.setVisible(scene)
        self._silence_box.setVisible(not scene)

    def _start(self):
        mode = "scene" if self._scene_radio.isChecked() else "silence"
        if mode == "scene":
            kwargs = {
                "threshold": self._threshold_slider.value() / 10.0,
                "min_scene_length": float(self._min_scene.value()),
                "duration": self.duration,
            }
        else:
            kwargs = {
                "noise_threshold": f"{self._noise_spin.value()}dB",
                "min_silence_duration": float(self._min_silence.value()),
                "duration": self.duration,
            }

        self._thread = _DetectionThread(
            self.video_path, mode, self.ffmpeg_path, **kwargs
        )
        self._thread.finished.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._detect_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status.setText("Analysing video\u2026")
        self._thread.start()

    def _on_done(self, segments: List[Segment]):
        self._progress.setVisible(False)
        self._detect_btn.setEnabled(True)
        self._status.setText("")
        if not segments:
            QMessageBox.information(self, "No Segments",
                                    "No segments detected with current settings.")
            return
        reply = QMessageBox.question(
            self, "Segments Detected",
            f"Found {len(segments)} segment(s).\n\nAdd them to the timeline?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.segments_detected.emit(segments)
            self.accept()

    def _on_error(self, msg: str):
        self._progress.setVisible(False)
        self._detect_btn.setEnabled(True)
        self._status.setText("")
        QMessageBox.critical(self, "Detection Error", f"Failed:\n{msg}")
