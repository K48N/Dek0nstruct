"""Frame-scrubber video preview using ffmpeg thumbnail extraction.

Replaces the broken QMediaPlayer/DirectShow approach with reliable
ffmpeg-based frame extraction displayed via QLabel/QPixmap.
"""
import os
import tempfile
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap

from ui.themes.dark_theme import PortfolioTheme


class VideoPreview(QWidget):
    """Video preview panel backed by ffmpeg frame extraction."""

    position_changed = pyqtSignal(float)  # seconds

    def __init__(self):
        super().__init__()
        self._path: str = ""
        self._duration: float = 0.0
        self._position: float = 0.0
        self._in_point: float = 0.0
        self._out_point: float = 0.0
        self._ffmpeg = None
        self._frame_timer = QTimer(self)
        self._frame_timer.setSingleShot(True)
        self._frame_timer.timeout.connect(self._extract_frame)
        self._setup_ui()

    # ── public API ────────────────────────────────────────────────────────────

    def set_ffmpeg(self, wrapper):
        """Inject FFmpegWrapper for thumbnail extraction."""
        self._ffmpeg = wrapper

    def load_video(self, file_path: str, duration: float = 0.0):
        self._path = file_path
        self._duration = duration
        self._position = 0.0
        self._in_point = 0.0
        self._out_point = 0.0
        self._seek_slider.setEnabled(True)
        self._in_btn.setEnabled(True)
        self._out_btn.setEnabled(True)
        self.add_segment_button.setEnabled(False)
        self._update_time_label()
        self._update_marker_label()
        self._frame_label.setText("Extracting frame\u2026")
        self._schedule_frame(immediate=True)

    def seek_to(self, time: float):
        self._position = max(0.0, min(time, self._duration))
        self._sync_slider()
        self._update_time_label()
        self._schedule_frame()

    def get_current_time(self) -> float:
        return self._position

    def get_segment_range(self):
        return self._in_point, self._out_point

    def clear_markers(self):
        self._in_point = 0.0
        self._out_point = 0.0
        self.add_segment_button.setEnabled(False)
        self._update_marker_label()

    # ── setup ─────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        hdr = QLabel("Preview")
        hdr.setStyleSheet(
            f"font-size:16px;font-weight:600;color:{PortfolioTheme.WHITE};padding:10px;"
        )
        header.addWidget(hdr)
        self._time_label = QLabel("0:00.0 / 0:00")
        self._time_label.setStyleSheet(
            f"color:{PortfolioTheme.GRAY_LIGHTER};"
            f"font-family:{PortfolioTheme.FONT_MONO};padding:10px;"
        )
        header.addWidget(self._time_label)
        header.addStretch()
        layout.addLayout(header)

        # Frame display
        self._frame_label = QLabel("Load a video to start")
        self._frame_label.setAlignment(Qt.AlignCenter)
        self._frame_label.setMinimumHeight(350)
        self._frame_label.setStyleSheet(
            f"background:{PortfolioTheme.BLACK};"
            f"border:1px solid {PortfolioTheme.BORDER};"
            f"border-radius:4px;"
            f"color:{PortfolioTheme.GRAY_LIGHTER};"
            f"font-size:14px;"
        )
        layout.addWidget(self._frame_label, stretch=1)

        # Seek slider
        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.setEnabled(False)
        self._seek_slider.setRange(0, 10000)
        self._seek_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {PortfolioTheme.TERTIARY}; height: 8px; border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {PortfolioTheme.ACCENT}; width: 16px;
                margin: -4px 0; border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {PortfolioTheme.ACCENT_HOVER};
            }}
        """)
        self._seek_slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self._seek_slider)

        # Controls
        _btn = (
            f"QPushButton {{"
            f"background:{PortfolioTheme.TERTIARY};color:{PortfolioTheme.WHITE};"
            f"border:1px solid {PortfolioTheme.BORDER};border-radius:4px;padding:8px 14px;}}"
            f"QPushButton:hover {{background:{PortfolioTheme.GRAY};}}"
            f"QPushButton:disabled {{color:{PortfolioTheme.GRAY_LIGHT};}}"
        )
        controls = QHBoxLayout()
        controls.setSpacing(8)

        back = QPushButton("\u2190 10s")
        back.clicked.connect(lambda: self.seek_to(self._position - 10))
        back.setStyleSheet(_btn)
        controls.addWidget(back)

        fwd = QPushButton("10s \u2192")
        fwd.clicked.connect(lambda: self.seek_to(self._position + 10))
        fwd.setStyleSheet(_btn)
        controls.addWidget(fwd)

        controls.addStretch()

        self._in_btn = QPushButton("Set In [I]")
        self._in_btn.setEnabled(False)
        self._in_btn.clicked.connect(self._set_in)
        self._in_btn.setStyleSheet(_btn)
        controls.addWidget(self._in_btn)

        self._out_btn = QPushButton("Set Out [O]")
        self._out_btn.setEnabled(False)
        self._out_btn.clicked.connect(self._set_out)
        self._out_btn.setStyleSheet(_btn)
        controls.addWidget(self._out_btn)

        self.add_segment_button = QPushButton("Add Segment")
        self.add_segment_button.setEnabled(False)
        self.add_segment_button.setStyleSheet(f"""
            QPushButton {{
                background:{PortfolioTheme.SUCCESS};color:{PortfolioTheme.WHITE};
                border:none;border-radius:4px;padding:8px 16px;font-weight:500;
            }}
            QPushButton:hover {{background:#218838;}}
            QPushButton:disabled {{
                background:{PortfolioTheme.GRAY};color:{PortfolioTheme.GRAY_LIGHT};
            }}
        """)
        controls.addWidget(self.add_segment_button)

        layout.addLayout(controls)

        self._marker_label = QLabel("")
        self._marker_label.setStyleSheet(
            f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;padding:2px 0;"
        )
        layout.addWidget(self._marker_label)

        hint = QLabel("\u2190 \u2192 to seek 1s  |  I = Set In  |  O = Set Out")
        hint.setStyleSheet(f"color:{PortfolioTheme.GRAY};font-size:11px;")
        layout.addWidget(hint)

    # ── internals ─────────────────────────────────────────────────────────────

    def _on_slider(self, value: int):
        if self._duration <= 0:
            return
        self._position = (value / 10000.0) * self._duration
        self._update_time_label()
        self.position_changed.emit(self._position)
        self._schedule_frame()

    def _sync_slider(self):
        if self._duration <= 0:
            return
        self._seek_slider.blockSignals(True)
        self._seek_slider.setValue(int((self._position / self._duration) * 10000))
        self._seek_slider.blockSignals(False)

    def _set_in(self):
        self._in_point = self._position
        self._check_range()
        self._update_marker_label()

    def _set_out(self):
        self._out_point = self._position
        self._check_range()
        self._update_marker_label()

    def _check_range(self):
        ok = self._out_point > self._in_point and (self._out_point - self._in_point) >= 0.5
        self.add_segment_button.setEnabled(ok)

    def _update_time_label(self):
        def fmt(s: float) -> str:
            return f"{int(s // 60)}:{int(s % 60):02d}.{int((s * 10) % 10)}"
        self._time_label.setText(f"{fmt(self._position)} / {fmt(self._duration)}")

    def _update_marker_label(self):
        if self._in_point or self._out_point:
            def fmt(s):
                return f"{int(s // 60)}:{int(s % 60):02d}"
            dur = self._out_point - self._in_point
            self._marker_label.setText(
                f"In: {fmt(self._in_point)}  Out: {fmt(self._out_point)}  ({dur:.1f}s)"
            )
        else:
            self._marker_label.setText("")

    def _schedule_frame(self, immediate: bool = False):
        self._frame_timer.stop()
        self._frame_timer.start(0 if immediate else 120)

    def _extract_frame(self):
        if not self._path or not self._ffmpeg:
            return
        try:
            cache_dir = os.path.join(tempfile.gettempdir(), "dek0nstruct_frames")
            os.makedirs(cache_dir, exist_ok=True)
            digest = abs(hash(self._path)) % 1_000_000
            thumb = os.path.join(cache_dir, f"{digest}_{int(self._position * 10)}.jpg")
            if not os.path.exists(thumb):
                ok = self._ffmpeg.generate_thumbnail(
                    self._path, thumb, self._position, width=960, height=540
                )
                if not ok:
                    self._frame_label.setText(f"Frame unavailable at {self._position:.1f}s")
                    return
            pix = QPixmap(thumb)
            if not pix.isNull():
                self._frame_label.setPixmap(
                    pix.scaled(
                        self._frame_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                self._frame_label.setText(f"Frame at {self._position:.1f}s")
        except Exception as e:
            self._frame_label.setText(f"Preview error: {e}")

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_Left:
            self.seek_to(self._position - 1)
        elif k == Qt.Key_Right:
            self.seek_to(self._position + 1)
        elif k == Qt.Key_I:
            self._set_in()
        elif k == Qt.Key_O:
            self._set_out()
        else:
            super().keyPressEvent(event)
