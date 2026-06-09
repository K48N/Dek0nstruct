"""
Control panel with export options and settings
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QGroupBox,
                            QSpinBox, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.themes.dark_theme import PortfolioTheme
from core.video_engine import ProcessingOptions


class ControlPanel(QWidget):
    """Left control panel with options"""
    
    export_requested = pyqtSignal(str, ProcessingOptions)  # output_dir, options
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setMaximumWidth(350)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Export Settings")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {PortfolioTheme.WHITE};
            padding-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Audio Options Group
        audio_group = self._create_group("Audio Options")
        audio_layout = QVBoxLayout()
        
        audio_layout.addWidget(QLabel("Audio Channels:"))
        self.audio_combo = QComboBox()
        self.audio_combo.addItems([
            "Keep Original (Fastest)",
            "Mono (Smaller Size)", 
            "Stereo (Best Quality)"
        ])
        self.audio_combo.setStyleSheet(self._combo_style())
        audio_layout.addWidget(self.audio_combo)
        
        audio_layout.addSpacing(10)
        audio_layout.addWidget(QLabel("MP3 Quality:"))
        self.mp3_quality_combo = QComboBox()
        self.mp3_quality_combo.addItems([
            "Best Quality (Largest)",
            "Balanced", 
            "Lower Quality (Smallest)"
        ])
        self.mp3_quality_combo.setCurrentIndex(1)  # Default to Balanced
        self.mp3_quality_combo.setStyleSheet(self._combo_style())
        audio_layout.addWidget(self.mp3_quality_combo)
        
        # MP3 quality descriptor
        mp3_desc = QLabel("0 = Best quality (largest)\n5 = Balanced\n9 = Smallest (lower quality)")
        mp3_desc.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 10px;
            padding: 5px;
        """)
        audio_layout.addWidget(mp3_desc)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # Video Options Group
        video_group = self._create_group("Video Options")
        video_layout = QVBoxLayout()
        
        self.codec_copy = QCheckBox("Fast Mode (Copy Codec)")
        self.codec_copy.setChecked(True)
        self.codec_copy.setStyleSheet(self._checkbox_style())
        video_layout.addWidget(self.codec_copy)
        
        codec_desc = QLabel("Fast but less precise cuts (±1 frame)")
        codec_desc.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 10px;
            padding-left: 25px;
        """)
        video_layout.addWidget(codec_desc)
        
        video_layout.addSpacing(5)
        
        self.use_gpu = QCheckBox("Use GPU Acceleration")
        self.use_gpu.setChecked(True)
        self.use_gpu.setStyleSheet(self._checkbox_style())
        video_layout.addWidget(self.use_gpu)
        
        gpu_desc = QLabel("2-5x faster if available")
        gpu_desc.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 10px;
            padding-left: 25px;
        """)
        video_layout.addWidget(gpu_desc)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # Performance Options Group
        perf_group = self._create_group("Performance")
        perf_layout = QVBoxLayout()
        
        self.parallel_processing = QCheckBox("Parallel Processing")
        self.parallel_processing.setChecked(True)
        self.parallel_processing.setStyleSheet(self._checkbox_style())
        perf_layout.addWidget(self.parallel_processing)
        
        perf_layout.addSpacing(10)
        perf_layout.addWidget(QLabel("Worker Threads:"))
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 16)
        self.max_workers.setValue(4)
        self.max_workers.setStyleSheet(self._spinbox_style())
        perf_layout.addWidget(self.max_workers)
        
        # Worker threads descriptor
        workers_desc = QLabel("Higher = faster but more CPU/memory.\nRecommended: CPU cores - 2")
        workers_desc.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 10px;
            padding: 5px;
        """)
        perf_layout.addWidget(workers_desc)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # Export Options Group
        export_group = self._create_group("Export Formats")
        export_layout = QVBoxLayout()
        
        # Video export
        self.export_video = QCheckBox("Export Video")
        self.export_video.setChecked(True)
        self.export_video.setStyleSheet(self._checkbox_style())
        self.export_video.stateChanged.connect(self._on_export_video_changed)
        export_layout.addWidget(self.export_video)
        
        export_layout.addWidget(QLabel("Video Format:"))
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems(["mp4", "mkv", "avi", "mov", "webm"])
        self.video_format_combo.setStyleSheet(self._combo_style())
        export_layout.addWidget(self.video_format_combo)
        
        export_layout.addSpacing(10)
        
        # Audio export
        self.export_audio = QCheckBox("Export Audio")
        self.export_audio.setChecked(True)
        self.export_audio.setStyleSheet(self._checkbox_style())
        self.export_audio.stateChanged.connect(self._on_export_audio_changed)
        export_layout.addWidget(self.export_audio)
        
        export_layout.addWidget(QLabel("Audio Format:"))
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "wav", "aac", "flac", "ogg"])
        self.audio_format_combo.setStyleSheet(self._combo_style())
        export_layout.addWidget(self.audio_format_combo)
        
        export_layout.addSpacing(10)
        
        # Quick option
        self.export_both = QCheckBox("Export Both Formats")
        self.export_both.setChecked(False)
        self.export_both.setStyleSheet(self._checkbox_style())
        self.export_both.stateChanged.connect(self._on_export_both_changed)
        export_layout.addWidget(self.export_both)
        
        both_desc = QLabel("Creates both video and audio files")
        both_desc.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 10px;
            padding-left: 25px;
        """)
        export_layout.addWidget(both_desc)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        # Export Button
        self.export_button = QPushButton("Export All Segments")
        self.export_button.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.ACCENT};
                color: {PortfolioTheme.WHITE};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {PortfolioTheme.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background: {PortfolioTheme.ACCENT_PRESSED};
            }}
            QPushButton:disabled {{
                background: {PortfolioTheme.GRAY};
                color: {PortfolioTheme.GRAY_LIGHT};
            }}
        """)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                background: {PortfolioTheme.TERTIARY};
                text-align: center;
                color: {PortfolioTheme.WHITE};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background: {PortfolioTheme.ACCENT};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 11px;
            padding: 5px;
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
    
    def _on_export_video_changed(self, state):
        """Handle video export checkbox change"""
        self.video_format_combo.setEnabled(state == Qt.Checked)
    
    def _on_export_audio_changed(self, state):
        """Handle audio export checkbox change"""
        self.audio_format_combo.setEnabled(state == Qt.Checked)
    
    def _on_export_both_changed(self, state):
        """Handle export both checkbox change"""
        if state == Qt.Checked:
            self.export_video.setChecked(True)
            self.export_audio.setChecked(True)
    
    def _create_group(self, title: str) -> QGroupBox:
        """Create styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: 600;
                color: {PortfolioTheme.WHITE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: {PortfolioTheme.ACCENT};
            }}
        """)
        return group
    
    def _combo_style(self) -> str:
        """Combo box style"""
        return f"""
            QComboBox {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
            QComboBox:hover {{
                border: 1px solid {PortfolioTheme.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                selection-background-color: {PortfolioTheme.ACCENT};
            }}
        """
    
    def _spinbox_style(self) -> str:
        """Spinbox style"""
        return f"""
            QSpinBox {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
            QSpinBox:hover {{
                border: 1px solid {PortfolioTheme.ACCENT};
            }}
        """
    
    def _checkbox_style(self) -> str:
        """Checkbox style"""
        return f"""
            QCheckBox {{
                color: {PortfolioTheme.WHITE};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 3px;
                background: {PortfolioTheme.TERTIARY};
            }}
            QCheckBox::indicator:checked {{
                background: {PortfolioTheme.ACCENT};
                border: 1px solid {PortfolioTheme.ACCENT};
            }}
        """
    
    def _on_export_clicked(self):
        """Handle export button click"""
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not output_dir:
            return
        
        # Get options
        options = self.get_processing_options()
        
        # Emit signal
        self.export_requested.emit(output_dir, options)
    
    def set_export_enabled(self, enabled: bool):
        """Enable/disable export button"""
        self.export_button.setEnabled(enabled)
    
    def show_progress(self, current: int, total: int, message: str = ""):
        """Show export progress"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
    
    def get_processing_options(self) -> ProcessingOptions:
        """Get current processing options"""
        audio_map = {
            0: None,
            1: 'mono',
            2: 'stereo'
        }
        
        return ProcessingOptions(
            audio_channels=audio_map[self.audio_combo.currentIndex()],
            use_gpu=self.use_gpu.isChecked(),
            codec_copy=self.codec_copy.isChecked(),
            mp3_quality=self.mp3_quality.value(),
            output_format=self.video_format_combo.currentText(),
            parallel_processing=self.parallel_processing.isChecked(),
            max_workers=self.max_workers.value(),
            export_both_formats=self.export_both.isChecked()
        )