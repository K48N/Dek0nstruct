"""
Control panel with export options and settings
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QGroupBox,
                            QFileDialog, QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.themes.dark_theme import PortfolioTheme
from core.video_engine import ProcessingOptions


class ControlPanel(QWidget):
    """Left control panel with options"""

    export_requested = pyqtSignal(str, ProcessingOptions)  # output_dir, options
    import_requested = pyqtSignal()
    load_project_requested = pyqtSignal()
    help_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(260)
        self.setMaximumWidth(420)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Advanced options are configured from the top menu, not the left stack.
        self._audio_channels = None
        self._mp3_quality = 5
        self._use_gpu = True
        self._codec_copy = True
        self._parallel_processing = True
        self._max_workers = 4
        self._compatibility_mode = True
        self._export_both_formats = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # File buttons
        import_btn = QPushButton("Import Video")
        import_btn.clicked.connect(self.import_requested)
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER_LIGHT};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {PortfolioTheme.TERTIARY}; }}
        """)
        layout.addWidget(import_btn)

        load_btn = QPushButton("Load Project")
        load_btn.clicked.connect(self.load_project_requested)
        load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER_LIGHT};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {PortfolioTheme.TERTIARY}; }}
        """)
        layout.addWidget(load_btn)

        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.help_requested)
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER_LIGHT};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {PortfolioTheme.TERTIARY}; }}
        """)
        layout.addWidget(help_btn)

        # Title
        title = QLabel("Export")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {PortfolioTheme.WHITE};
            padding-bottom: 10px;
        """)
        layout.addWidget(title)
        
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
        self.audio_format_combo.setCurrentText("mp3")
        self.audio_format_combo.setStyleSheet(self._combo_style())
        export_layout.addWidget(self.audio_format_combo)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        hint = QLabel("Advanced export and diagnostics settings are in the top Export and Tools menus.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            font-size: 11px;
            padding: 4px 8px;
        """)
        layout.addWidget(hint)
        
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

    def trigger_export(self):
        """Public API for menu actions to open export flow."""
        self._on_export_clicked()
    
    def set_export_enabled(self, enabled: bool):
        """Enable/disable export button"""
        self.export_button.setEnabled(enabled)

    def set_advanced_settings(
        self,
        *,
        audio_channels=None,
        mp3_quality=5,
        use_gpu=True,
        codec_copy=True,
        parallel_processing=True,
        max_workers=4,
        compatibility_mode=True,
        export_both_formats=False,
    ):
        """Update advanced export settings from menu controls."""
        self._audio_channels = audio_channels
        self._mp3_quality = int(mp3_quality)
        self._use_gpu = bool(use_gpu)
        self._codec_copy = bool(codec_copy)
        self._parallel_processing = bool(parallel_processing)
        self._max_workers = int(max_workers)
        self._compatibility_mode = bool(compatibility_mode)
        self._export_both_formats = bool(export_both_formats)

    def get_advanced_settings(self) -> dict:
        """Return current advanced export settings for menu sync/state."""
        return {
            "audio_channels": self._audio_channels,
            "mp3_quality": self._mp3_quality,
            "use_gpu": self._use_gpu,
            "codec_copy": self._codec_copy,
            "parallel_processing": self._parallel_processing,
            "max_workers": self._max_workers,
            "compatibility_mode": self._compatibility_mode,
            "export_both_formats": self._export_both_formats,
        }
    
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
        return ProcessingOptions(
            audio_channels=self._audio_channels,
            use_gpu=self._use_gpu,
            codec_copy=self._codec_copy,
            mp3_quality=self._mp3_quality,
            output_format=self.video_format_combo.currentText(),
            audio_output_format=self.audio_format_combo.currentText(),
            parallel_processing=self._parallel_processing,
            max_workers=self._max_workers,
            export_both_formats=self._export_both_formats,
            compatibility_mode=self._compatibility_mode,
        )