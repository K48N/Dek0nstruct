"""
All Phase 5 dialogs in one file
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QTime
from PyQt5.QtGui import QColor
from ui.themes.dark_theme import PortfolioTheme
from typing import Optional


class VideoInfoDialog(QDialog):
    """Display detailed video information"""
    
    def __init__(self, video_info: dict, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.setWindowTitle("Video Information")
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Video Details")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {PortfolioTheme.WHITE};")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        
        info_items = [
            ("Duration", f"{int(self.video_info.get('duration', 0))}s"),
            ("Size", self._format_size(self.video_info.get('size', 0))),
            ("Bitrate", f"{self.video_info.get('bitrate', 0) // 1000} kbps"),
            ("Format", self.video_info.get('format', 'Unknown'))
        ]
        
        for stream in self.video_info.get('streams', []):
            if stream['type'] == 'video':
                info_items.extend([
                    ("Video Codec", stream.get('codec', 'Unknown')),
                    ("Resolution", f"{stream.get('width')}x{stream.get('height')}"),
                    ("FPS", f"{stream.get('fps', 0):.2f}"),
                    ("Pixel Format", stream.get('pix_fmt', 'Unknown'))
                ])
            elif stream['type'] == 'audio':
                info_items.extend([
                    ("Audio Codec", stream.get('codec', 'Unknown')),
                    ("Sample Rate", f"{stream.get('sample_rate', 0)} Hz"),
                    ("Channels", str(stream.get('channels', 0)))
                ])
        
        table.setRowCount(len(info_items))
        for i, (key, value) in enumerate(info_items):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self._apply_style()
    
    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {PortfolioTheme.PRIMARY}; }}
            QLabel {{ color: {PortfolioTheme.WHITE}; }}
            QTableWidget {{ 
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                gridline-color: {PortfolioTheme.BORDER};
            }}
            QPushButton {{
                background: {PortfolioTheme.ACCENT};
                color: {PortfolioTheme.WHITE};
                padding: 10px 20px;
                border-radius: 4px;
            }}
        """)


class TimeInputDialog(QDialog):
    """Precision time input dialog"""
    
    def __init__(self, initial_time: float = 0.0, label: str = "Enter Time", parent=None):
        super().__init__(parent)
        self.time_value = initial_time
        self.setWindowTitle(label)
        self.setMinimumWidth(300)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setTime(self._seconds_to_qtime(self.time_value))
        layout.addWidget(QLabel("Time (HH:MM:SS):"))
        layout.addWidget(self.time_edit)
        
        self.ms_spin = QSpinBox()
        self.ms_spin.setRange(0, 999)
        self.ms_spin.setValue(int((self.time_value % 1) * 1000))
        layout.addWidget(QLabel("Milliseconds:"))
        layout.addWidget(self.ms_spin)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self._apply_style()
    
    def get_time(self) -> float:
        qtime = self.time_edit.time()
        seconds = qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second()
        seconds += self.ms_spin.value() / 1000.0
        return seconds
    
    def _seconds_to_qtime(self, seconds: float):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return QTime(h, m, s)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {PortfolioTheme.PRIMARY}; }}
            QLabel {{ color: {PortfolioTheme.WHITE}; }}
            QTimeEdit, QSpinBox {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                padding: 8px;
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
            }}
            QPushButton {{
                background: {PortfolioTheme.ACCENT};
                color: {PortfolioTheme.WHITE};
                padding: 8px 16px;
                border-radius: 4px;
            }}
        """)


class ColorPickerDialog(QDialog):
    """Color picker for segment color coding"""
    
    def __init__(self, initial_color: str = "#009682", parent=None):
        super().__init__(parent)
        self.selected_color = initial_color
        self.setWindowTitle("Choose Color")
        self.setMinimumSize(300, 200)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Preset Colors:"))
        
        colors_layout = QGridLayout()
        preset_colors = [
            ("#009682", "Teal"),
            ("#2196F3", "Blue"),
            ("#4CAF50", "Green"),
            ("#FFC107", "Yellow"),
            ("#FF9800", "Orange"),
            ("#F44336", "Red"),
            ("#9C27B0", "Purple"),
            ("#607D8B", "Gray")
        ]
        
        for i, (color, name) in enumerate(preset_colors):
            btn = QPushButton(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color: self._select_color(c))
            colors_layout.addWidget(btn, i // 4, i % 4)
        
        layout.addLayout(colors_layout)
        
        custom_btn = QPushButton("Custom Color...")
        custom_btn.clicked.connect(self._choose_custom)
        layout.addWidget(custom_btn)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self._apply_style()
    
    def _select_color(self, color: str):
        self.selected_color = color
    
    def _choose_custom(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
    
    def get_color(self) -> str:
        return self.selected_color
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {PortfolioTheme.PRIMARY}; }}
            QLabel {{ color: {PortfolioTheme.WHITE}; }}
            QPushButton {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                padding: 8px 16px;
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
            }}
        """)


class AudioProcessingDialog(QDialog):
    """Audio processing dialog with Demucs options"""
    
    processing_requested = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audio Processing")
        self.setMinimumSize(400, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Audio Processing")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {PortfolioTheme.WHITE};")
        layout.addWidget(title)
        
        ops_group = QGroupBox("Select Operation")
        ops_layout = QVBoxLayout()
        
        self.op_group = QButtonGroup()
        
        self.remove_music_radio = QRadioButton("Remove Background Music (Demucs)")
        self.remove_music_radio.setChecked(True)
        self.op_group.addButton(self.remove_music_radio, 0)
        ops_layout.addWidget(self.remove_music_radio)
        
        ops_layout.addWidget(QLabel("Separate vocals from music using AI"))
        
        self.normalize_radio = QRadioButton("Normalize Volume")
        self.op_group.addButton(self.normalize_radio, 1)
        ops_layout.addWidget(self.normalize_radio)
        
        self.noise_radio = QRadioButton("Reduce Noise")
        self.op_group.addButton(self.noise_radio, 2)
        ops_layout.addWidget(self.noise_radio)
        
        self.eq_radio = QRadioButton("Equalizer")
        self.op_group.addButton(self.eq_radio, 3)
        ops_layout.addWidget(self.eq_radio)
        
        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)
        
        self.settings_stack = QStackedWidget()
        
        demucs_widget = QWidget()
        demucs_layout = QVBoxLayout()
        self.keep_vocals = QCheckBox("Keep Vocals (remove music)")
        self.keep_vocals.setChecked(True)
        demucs_layout.addWidget(self.keep_vocals)
        demucs_widget.setLayout(demucs_layout)
        self.settings_stack.addWidget(demucs_widget)
        
        norm_widget = QWidget()
        norm_layout = QVBoxLayout()
        norm_layout.addWidget(QLabel("Target Level (LUFS):"))
        self.target_level = QSpinBox()
        self.target_level.setRange(-23, -5)
        self.target_level.setValue(-16)
        norm_layout.addWidget(self.target_level)
        norm_widget.setLayout(norm_layout)
        self.settings_stack.addWidget(norm_widget)
        
        noise_widget = QWidget()
        noise_layout = QVBoxLayout()
        noise_layout.addWidget(QLabel("Reduction Amount:"))
        self.noise_amount = QSlider(Qt.Horizontal)
        self.noise_amount.setRange(0, 100)
        self.noise_amount.setValue(10)
        noise_layout.addWidget(self.noise_amount)
        noise_widget.setLayout(noise_layout)
        self.settings_stack.addWidget(noise_widget)
        
        eq_widget = QWidget()
        eq_layout = QVBoxLayout()
        eq_layout.addWidget(QLabel("Bass:"))
        self.bass_slider = QSlider(Qt.Horizontal)
        self.bass_slider.setRange(-20, 20)
        eq_layout.addWidget(self.bass_slider)
        eq_layout.addWidget(QLabel("Mid:"))
        self.mid_slider = QSlider(Qt.Horizontal)
        self.mid_slider.setRange(-20, 20)
        eq_layout.addWidget(self.mid_slider)
        eq_layout.addWidget(QLabel("Treble:"))
        self.treble_slider = QSlider(Qt.Horizontal)
        self.treble_slider.setRange(-20, 20)
        eq_layout.addWidget(self.treble_slider)
        eq_widget.setLayout(eq_layout)
        self.settings_stack.addWidget(eq_widget)
        
        layout.addWidget(self.settings_stack)
        
        self.op_group.buttonClicked.connect(
            lambda btn: self.settings_stack.setCurrentIndex(self.op_group.id(btn))
        )
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        process_btn = QPushButton("Process")
        process_btn.clicked.connect(self._process)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(process_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self._apply_style()
    
    def _process(self):
        op_id = self.op_group.checkedId()
        
        if op_id == 0:
            self.processing_requested.emit('remove_music', {
                'keep_vocals': self.keep_vocals.isChecked()
            })
        elif op_id == 1:
            self.processing_requested.emit('normalize', {
                'target_level': self.target_level.value()
            })
        elif op_id == 2:
            self.processing_requested.emit('reduce_noise', {
                'noise_reduction': self.noise_amount.value()
            })
        elif op_id == 3:
            self.processing_requested.emit('eq', {
                'bass': self.bass_slider.value(),
                'mid': self.mid_slider.value(),
                'treble': self.treble_slider.value()
            })
        
        self.accept()
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog, QWidget {{ background: {PortfolioTheme.PRIMARY}; }}
            QLabel {{ color: {PortfolioTheme.WHITE}; }}
            QGroupBox {{
                background: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
                color: {PortfolioTheme.WHITE};
            }}
            QPushButton {{
                background: {PortfolioTheme.ACCENT};
                color: {PortfolioTheme.WHITE};
                padding: 10px 20px;
                border-radius: 4px;
            }}
        """)