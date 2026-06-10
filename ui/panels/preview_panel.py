"""Video preview using embedded VLC player (full video + audio)."""
import os
import sys

# Point python-vlc at the VLC installation before importing
_VLC_DIR = r"C:\Program Files\VideoLAN\VLC"
if os.path.isdir(_VLC_DIR):
    os.add_dll_directory(_VLC_DIR)
    os.environ.setdefault("PYTHON_VLC_MODULE_PATH", _VLC_DIR)

import vlc  # noqa: E402

from PyQt5.QtWidgets import (  # noqa: E402
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal  # noqa: E402
from PyQt5.QtGui import QFont  # noqa: E402

from ui.themes.dark_theme import PortfolioTheme  # noqa: E402


class _LoadingOverlay(QWidget):
    """Progress card shown during ffmpeg transcode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QWidget()
        card.setFixedWidth(340)
        card.setStyleSheet(
            f"background:rgba(15,15,15,0.90);"
            f"border:1px solid {PortfolioTheme.BORDER_ACCENT};"
            f"border-radius:12px;"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)

        self._title = QLabel("Converting video")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setFont(QFont("Inter", 13, QFont.Medium))
        self._title.setStyleSheet(f"color:{PortfolioTheme.WHITE};background:transparent;border:none;")
        cl.addWidget(self._title)

        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet(f"""
            QProgressBar {{background:{PortfolioTheme.TERTIARY};border-radius:4px;border:none;}}
            QProgressBar::chunk {{background:{PortfolioTheme.ACCENT};border-radius:4px;}}
        """)
        cl.addWidget(self._bar)

        row = QHBoxLayout()
        self._pct = QLabel("0%")
        self._pct.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;background:transparent;border:none;")
        row.addWidget(self._pct)
        row.addStretch()
        self._eta = QLabel("Estimating\u2026")
        self._eta.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;background:transparent;border:none;")
        row.addWidget(self._eta)
        cl.addLayout(row)

        outer.addWidget(card)
        self.hide()

    def show_converting(self):
        self._bar.setValue(0)
        self._pct.setText("0%")
        self._eta.setText("Estimating\u2026")
        self.show()
        self.raise_()

    def set_progress(self, fraction: float, eta: float):
        self._bar.setValue(int(fraction * 1000))
        self._pct.setText(f"{int(fraction*100)}%")
        if eta > 0:
            m, s = divmod(int(eta), 60)
            self._eta.setText(f"ETA {m}:{s:02d}" if m else f"ETA {s}s")
        else:
            self._eta.setText("Almost done")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.parent():
            self.setGeometry(self.parent().rect())


class VideoPreview(QWidget):
    """Video preview using embedded VLC — full video and audio."""

    position_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._path = ""
        self._duration = 0.0
        self._in_point = 0.0
        self._out_point = 0.0
        self._slider_dragging = False
        self._ffmpeg = None

        self._instance = vlc.Instance("--no-xlib", "--quiet")
        self._player = self._instance.media_player_new()

        # Poll timer for slider / time label
        self._poll = QTimer(self)
        self._poll.setInterval(250)
        self._poll.timeout.connect(self._on_poll)

        self._setup_ui()

        # Tell VLC to render into our frame widget
        wid = int(self._video_frame.winId())
        if sys.platform == "win32":
            self._player.set_hwnd(wid)
        else:
            self._player.set_xwindow(wid)

    # ── public API ────────────────────────────────────────────────────────────

    def set_ffmpeg(self, wrapper):
        self._ffmpeg = wrapper

    def show_loading(self):
        self._overlay.show_converting()
        self._play_btn.setEnabled(False)
        self._seek_slider.setEnabled(False)

    def set_progress(self, fraction: float, eta: float):
        self._overlay.set_progress(fraction, eta)

    def hide_loading(self):
        self._overlay.hide()
        self._play_btn.setEnabled(True)

    def load_video(self, path: str, duration: float = 0.0):
        self.hide_loading()
        self._path = path
        self._duration = duration
        self._in_point = 0.0
        self._out_point = 0.0

        media = self._instance.media_new(path)
        self._player.set_media(media)
        # Pause-play to load first frame without playing
        self._player.play()
        QTimer.singleShot(300, self._player.pause)

        self._seek_slider.setEnabled(True)
        self._in_btn.setEnabled(True)
        self._out_btn.setEnabled(True)
        self.add_segment_button.setEnabled(False)
        self._poll.start()
        self._update_marker_label()
        self._update_time_label(0.0)

    def seek_to(self, time: float):
        if self._duration <= 0:
            return
        time = max(0.0, min(time, self._duration))
        self._player.set_time(int(time * 1000))

    def seek_relative(self, delta: float):
        pos = (self._player.get_time() or 0) / 1000.0
        self.seek_to(pos + delta)

    def toggle_playback(self):
        if self._player.is_playing():
            self.pause()
        else:
            self.play()

    def play(self):
        if self._path:
            self._player.play()
            self._play_btn.setText("Pause")

    def pause(self):
        self._player.pause()
        self._play_btn.setText("Play")

    def set_in_marker(self):  self._set_in()
    def set_out_marker(self): self._set_out()

    def get_current_time(self) -> float:
        ms = self._player.get_time()
        return ms / 1000.0 if ms and ms > 0 else 0.0

    def get_segment_range(self):
        return self._in_point, self._out_point

    def clear_markers(self):
        self._in_point = 0.0
        self._out_point = 0.0
        self.add_segment_button.setEnabled(False)
        self._update_marker_label()

    # ── UI setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # header
        header = QHBoxLayout()
        hdr = QLabel("Preview")
        hdr.setStyleSheet(f"font-size:14px;font-weight:600;color:{PortfolioTheme.WHITE};padding:6px 0;")
        header.addWidget(hdr)
        self._time_label = QLabel("0:00.0 / 0:00")
        self._time_label.setStyleSheet(
            f"color:{PortfolioTheme.GRAY_LIGHTER};font-family:{PortfolioTheme.FONT_MONO};font-size:12px;"
        )
        header.addWidget(self._time_label)
        header.addStretch()
        layout.addLayout(header)

        # video area (16:9 container)
        self._video_container = _VideoContainer()
        self._video_frame = QFrame(self._video_container)
        self._video_frame.setStyleSheet("background:#000000;")
        self._overlay = _LoadingOverlay(self._video_container)
        layout.addWidget(self._video_container, stretch=1)

        # seek slider
        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.setEnabled(False)
        self._seek_slider.setRange(0, 10000)
        self._seek_slider.setFixedHeight(18)
        self._seek_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background:{PortfolioTheme.TERTIARY}; height:6px; border-radius:3px;
            }}
            QSlider::handle:horizontal {{
                background:{PortfolioTheme.ACCENT}; width:14px; margin:-4px 0; border-radius:7px;
            }}
            QSlider::handle:horizontal:hover {{ background:{PortfolioTheme.ACCENT_HOVER}; }}
        """)
        self._seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self._seek_slider.sliderReleased.connect(self._on_slider_released)
        self._seek_slider.sliderMoved.connect(self._on_slider_moved)
        layout.addWidget(self._seek_slider)

        _btn = (
            f"QPushButton {{background:{PortfolioTheme.TERTIARY};color:{PortfolioTheme.WHITE};"
            f"border:1px solid {PortfolioTheme.BORDER};border-radius:4px;padding:6px 12px;}}"
            f"QPushButton:hover {{background:{PortfolioTheme.GRAY};}}"
            f"QPushButton:disabled {{color:{PortfolioTheme.GRAY_LIGHT};}}"
        )
        controls = QHBoxLayout()
        controls.setSpacing(6)

        self._play_btn = QPushButton("Play")
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self.toggle_playback)
        self._play_btn.setStyleSheet(_btn)
        controls.addWidget(self._play_btn)

        back = QPushButton("\u25c0 10s")
        back.clicked.connect(lambda: self.seek_relative(-10))
        back.setStyleSheet(_btn)
        controls.addWidget(back)

        fwd = QPushButton("10s \u25b6")
        fwd.clicked.connect(lambda: self.seek_relative(10))
        fwd.setStyleSheet(_btn)
        controls.addWidget(fwd)

        vol_label = QLabel("Vol")
        vol_label.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;margin-left:8px;")
        controls.addWidget(vol_label)
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(80)
        self._player.audio_set_volume(80)
        self._vol_slider.valueChanged.connect(self._player.audio_set_volume)
        self._vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{background:{PortfolioTheme.TERTIARY};height:4px;border-radius:2px;}}
            QSlider::handle:horizontal {{background:{PortfolioTheme.ACCENT};width:12px;margin:-4px 0;border-radius:6px;}}
        """)
        controls.addWidget(self._vol_slider)
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
            QPushButton {{background:{PortfolioTheme.SUCCESS};color:{PortfolioTheme.WHITE};
                border:none;border-radius:4px;padding:6px 14px;font-weight:500;}}
            QPushButton:hover {{background:#218838;}}
            QPushButton:disabled {{background:{PortfolioTheme.GRAY};color:{PortfolioTheme.GRAY_LIGHT};}}
        """)
        controls.addWidget(self.add_segment_button)
        layout.addLayout(controls)

        self._marker_label = QLabel("")
        self._marker_label.setStyleSheet(
            f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;padding:1px 0;"
        )
        layout.addWidget(self._marker_label)

        hint = QLabel("\u2190 \u2192 seek 1s  |  I = Set In  |  O = Set Out  |  Space = Play/Pause")
        hint.setStyleSheet(f"color:{PortfolioTheme.GRAY};font-size:10px;")
        layout.addWidget(hint)

    # ── internals ─────────────────────────────────────────────────────────────

    def _on_poll(self):
        """Update slider and time label from VLC position."""
        if self._duration <= 0:
            return
        ms = self._player.get_time()
        if ms is None or ms < 0:
            return
        pos = ms / 1000.0
        self._update_time_label(pos)
        self.position_changed.emit(pos)
        if not self._slider_dragging:
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int((pos / self._duration) * 10000))
            self._seek_slider.blockSignals(False)
        # Sync play button text
        self._play_btn.setText("Pause" if self._player.is_playing() else "Play")

    def _on_slider_pressed(self):
        self._slider_dragging = True

    def _on_slider_released(self):
        self._slider_dragging = False
        if self._duration > 0:
            pos = (self._seek_slider.value() / 10000.0) * self._duration
            self._player.set_time(int(pos * 1000))

    def _on_slider_moved(self, value: int):
        if self._duration > 0:
            self._update_time_label((value / 10000.0) * self._duration)

    def _set_in(self):
        self._in_point = self.get_current_time()
        self._check_range()
        self._update_marker_label()

    def _set_out(self):
        self._out_point = self.get_current_time()
        self._check_range()
        self._update_marker_label()

    def _check_range(self):
        ok = self._out_point > self._in_point and (self._out_point - self._in_point) >= 0.5
        self.add_segment_button.setEnabled(ok)

    def _update_time_label(self, pos: float = None):
        if pos is None:
            pos = self.get_current_time()
        def fmt(s):
            return f"{int(s//60)}:{int(s%60):02d}.{int((s*10)%10)}"
        self._time_label.setText(f"{fmt(pos)} / {fmt(self._duration)}")

    def _update_marker_label(self):
        if self._in_point or self._out_point:
            def fmt(s):
                return f"{int(s//60)}:{int(s%60):02d}"
            dur = self._out_point - self._in_point
            self._marker_label.setText(
                f"In: {fmt(self._in_point)}  Out: {fmt(self._out_point)}  ({dur:.1f}s)"
            )
        else:
            self._marker_label.setText("")

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_Space:
            self.toggle_playback()
        elif k == Qt.Key_Left:
            self.seek_relative(-1)
        elif k == Qt.Key_Right:
            self.seek_relative(1)
        elif k == Qt.Key_I:
            self._set_in()
        elif k == Qt.Key_O:
            self._set_out()
        else:
            super().keyPressEvent(event)


class _VideoContainer(QWidget):
    """16:9 container that keeps video frame and overlay in sync."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 180)
        self.setStyleSheet("background:#000000;border:1px solid rgba(255,255,255,0.08);border-radius:4px;")

    def hasHeightForWidth(self): return True
    def heightForWidth(self, w): return w * 9 // 16

    def resizeEvent(self, e):
        super().resizeEvent(e)
        for child in self.children():
            if isinstance(child, QWidget):
                child.setGeometry(self.rect())
