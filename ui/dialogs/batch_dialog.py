"""Batch processing dialog — apply segment layout to multiple videos."""
from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QListWidget, QFileDialog, QMessageBox,
                              QProgressBar, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from core.batch_processor import BatchProcessor
from core.segment import Segment
from core.video_engine import ProcessingOptions
from ui.themes.dark_theme import PortfolioTheme


class _BatchThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)

    def __init__(self, processor, options):
        super().__init__()
        self.processor = processor
        self.options = options

    def run(self):
        results = self.processor.process_all(
            self.options, progress_callback=self.progress.emit
        )
        self.finished.emit(results)


class BatchDialog(QDialog):
    def __init__(self, segments: List[Segment], parent=None):
        super().__init__(parent)
        self.segments = segments
        self.processor = BatchProcessor()
        self._thread: Optional[_BatchThread] = None
        self.setWindowTitle("Batch Processing")
        self.setMinimumSize(560, 420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        title = QLabel("Batch Process Multiple Videos")
        title.setStyleSheet(f"font-size:18px;font-weight:700;color:{PortfolioTheme.WHITE};padding:10px;")
        layout.addWidget(title)
        info = QLabel(f"Apply current {len(self.segments)} segment(s) to multiple videos.")
        info.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};padding:0 10px 8px;")
        layout.addWidget(info)
        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{background:{PortfolioTheme.SECONDARY};color:{PortfolioTheme.WHITE};
                border:1px solid {PortfolioTheme.BORDER};border-radius:4px;}}
            QListWidget::item {{padding:8px;}}
            QListWidget::item:selected {{background:{PortfolioTheme.ACCENT};}}
        """)
        layout.addWidget(self._list)
        row = QHBoxLayout()
        for label, slot in [("Add Videos\u2026", self._add), ("Remove Selected", self._remove), ("Clear", self._clear)]:
            b = QPushButton(label); b.clicked.connect(slot); row.addWidget(b)
        row.addStretch()
        layout.addLayout(row)
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)
        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{PortfolioTheme.GRAY_LIGHTER};font-size:11px;")
        layout.addWidget(self._status)
        btns = QHBoxLayout(); btns.addStretch()
        self._run_btn = QPushButton("Start Batch Processing")
        self._run_btn.setEnabled(False)
        self._run_btn.setStyleSheet(f"""
            QPushButton {{background:{PortfolioTheme.ACCENT};color:{PortfolioTheme.WHITE};
                border:none;border-radius:6px;padding:12px 24px;font-weight:600;}}
            QPushButton:hover {{background:{PortfolioTheme.ACCENT_HOVER};}}
            QPushButton:disabled {{background:{PortfolioTheme.GRAY};color:{PortfolioTheme.GRAY_LIGHT};}}
        """)
        self._run_btn.clicked.connect(self._start)
        btns.addWidget(self._run_btn)
        close_btn = QPushButton("Close"); close_btn.clicked.connect(self.reject); btns.addWidget(close_btn)
        layout.addLayout(btns)
        self.setStyleSheet(f"""
            QDialog {{background:{PortfolioTheme.PRIMARY};}}
            QLabel {{color:{PortfolioTheme.WHITE};}}
            QPushButton {{background:{PortfolioTheme.TERTIARY};color:{PortfolioTheme.WHITE};
                border:1px solid {PortfolioTheme.BORDER};border-radius:4px;padding:8px 16px;}}
            QPushButton:hover {{background:{PortfolioTheme.GRAY};}}
        """)

    def _add(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Videos", "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv);;All Files (*)")
        for f in files:
            item = QListWidgetItem(Path(f).name); item.setData(Qt.UserRole, f); self._list.addItem(item)
        self._run_btn.setEnabled(self._list.count() > 0)

    def _remove(self):
        for item in self._list.selectedItems(): self._list.takeItem(self._list.row(item))
        self._run_btn.setEnabled(self._list.count() > 0)

    def _clear(self):
        self._list.clear(); self._run_btn.setEnabled(False)

    def _start(self):
        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not out_dir: return
        parent = self.parent()
        options = parent.control_panel.get_processing_options() if hasattr(parent, "control_panel") else ProcessingOptions()
        self.processor.clear_jobs()
        for i in range(self._list.count()):
            item = self._list.item(i); self.processor.add_job(item.data(Qt.UserRole), self.segments, out_dir)
        self._thread = _BatchThread(self.processor, options)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_done)
        self._run_btn.setEnabled(False); self._progress.setVisible(True); self._thread.start()

    def _on_progress(self, cur, total, msg):
        self._progress.setMaximum(total); self._progress.setValue(cur); self._status.setText(msg)

    def _on_done(self, _jobs):
        self._progress.setVisible(False); self._run_btn.setEnabled(True)
        s = self.processor.get_summary()
        QMessageBox.information(self, "Batch Complete",
            f"Done\n\nSucceeded: {s['complete']}\nFailed: {s['failed']}\nTotal: {s['total']}")
        self.accept()


class BatchProcessingThread(QThread):
    """Thread for batch processing"""
    
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    
    def __init__(self, processor, options, export_profile: Optional[ExportProfile] = None):
        super().__init__()
        self.processor = processor
        self.options = options
        self.export_profile = export_profile
    
    def run(self):
        results = self.processor.process_all(
            self.options,
            export_profile=self.export_profile,
            progress_callback=self.progress.emit
        )
        self.finished.emit(results)


class BatchDialog(QDialog):
    """Batch processing dialog"""
    
    def __init__(self, segments: List[Segment], parent=None):
        super().__init__(parent)
        self.segments = segments
        self.processor = BatchProcessor()
        self.processing_thread = None
        self.profile_manager = ExportProfileManager()
        self.current_profile = None
        
        self.setWindowTitle("Batch Processing")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._load_profiles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Batch Process Multiple Videos")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {PortfolioTheme.WHITE};
            padding: 10px;
        """)
        layout.addWidget(title)
        
        # Info
        info = QLabel(f"Apply current segments ({len(self.segments)}) to multiple videos")
        info.setStyleSheet(f"color: {PortfolioTheme.GRAY_LIGHTER}; padding: 5px 10px;")
        layout.addWidget(info)
        
        # Video list
        self.video_list = QListWidget()
        self.video_list.setStyleSheet(f"""
            QListWidget {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
            }}
            QListWidget::item:selected {{
                background: {PortfolioTheme.ACCENT};
            }}
        """)
        layout.addWidget(self.video_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Videos")
        add_btn.clicked.connect(self._add_videos)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        btn_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Export Profile Group
        profile_group = QGroupBox("Export Profile")
        profile_group.setStyleSheet(f"""
            QGroupBox {{
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 0.5em;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
        """)
        profile_layout = QHBoxLayout()
        
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(f"""
            QComboBox {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
            }}
        """)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        profile_layout.addWidget(self.profile_combo)
        
        manage_profile_btn = QPushButton("Manage Profiles...")
        manage_profile_btn.clicked.connect(self._manage_profiles)
        profile_layout.addWidget(manage_profile_btn)
        
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                background: {PortfolioTheme.TERTIARY};
                text-align: center;
                color: {PortfolioTheme.WHITE};
            }}
            QProgressBar::chunk {{
                background: {PortfolioTheme.ACCENT};
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {PortfolioTheme.GRAY_LIGHTER}; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Process button
        process_layout = QHBoxLayout()
        process_layout.addStretch()
        
        self.process_btn = QPushButton("Start Batch Processing")
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.ACCENT};
                color: {PortfolioTheme.WHITE};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {PortfolioTheme.ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background: {PortfolioTheme.GRAY};
            }}
        """)
        self.process_btn.clicked.connect(self._start_processing)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)
        
        cancel_btn = QPushButton("Close")
        cancel_btn.clicked.connect(self.reject)
        process_layout.addWidget(cancel_btn)
        
        layout.addLayout(process_layout)
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {PortfolioTheme.PRIMARY};
            }}
            QPushButton {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {PortfolioTheme.GRAY};
            }}
        """)
    
    def _load_profiles(self):
        """Load available profiles into combo box."""
        self.profile_combo.clear()
        self.profile_combo.addItem("Default (No Profile)")
        
        # Add saved profiles
        for name in self.profile_manager.list_profiles():
            self.profile_combo.addItem(name)
        
        # Add presets
        self.profile_combo.insertSeparator(self.profile_combo.count())
        self.profile_combo.addItem("YouTube HD (Preset)")
        self.profile_combo.addItem("Vimeo HD (Preset)")
        self.profile_combo.addItem("Device Playback (Preset)")
        self.profile_combo.addItem("Archive Quality (Preset)")
    
    def _on_profile_selected(self, index):
        """Handle profile selection change."""
        name = self.profile_combo.currentText()
        
        if name == "Default (No Profile)":
            self.current_profile = None
            return
        
        if " (Preset)" in name:
            # Create from preset
            preset_name = name.replace(" (Preset)", "").lower()
            try:
                self.current_profile = ExportProfile.create_preset(preset_name)
            except ValueError:
                self.current_profile = None
                return
        else:
            # Load existing profile
            try:
                self.current_profile = self.profile_manager.get_profile(name)
            except KeyError:
                self.current_profile = None
                return
    
    def _manage_profiles(self):
        """Open export profile manager dialog."""
        dialog = ExportProfileDialog(self.profile_manager, self)
        if dialog.exec_():
            self._load_profiles()
    
    def _add_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Videos",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv);;All Files (*)"
        )
        
        if files:
            for file_path in files:
                item = QListWidgetItem(Path(file_path).name)
                item.setData(Qt.UserRole, file_path)
                self.video_list.addItem(item)
            
            self.process_btn.setEnabled(self.video_list.count() > 0)
    
    def _remove_selected(self):
        for item in self.video_list.selectedItems():
            self.video_list.takeItem(self.video_list.row(item))
        
        self.process_btn.setEnabled(self.video_list.count() > 0)
    
    def _clear_all(self):
        self.video_list.clear()
        self.process_btn.setEnabled(False)
    
    def _start_processing(self):
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Please add segments first.")
            return
        
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if not output_dir:
            return
        
        # Get processing options from parent
        if hasattr(self.parent(), 'control_panel'):
            options = self.parent().control_panel.get_processing_options()
        else:
            options = ProcessingOptions()
        
        # Add jobs
        self.processor.clear_jobs()
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            video_path = item.data(Qt.UserRole)
            self.processor.add_job(video_path, self.segments, output_dir)
        
        # Start processing
        self.processing_thread = BatchProcessingThread(
            self.processor, 
            options,
            export_profile=self.current_profile
        )
        self.processing_thread.progress.connect(self._on_progress)
        self.processing_thread.finished.connect(self._on_finished)
        
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.processing_thread.start()
    
    def _on_progress(self, current, total, message):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def _on_finished(self, results):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        summary = self.processor.get_summary()
        
        QMessageBox.information(
            self,
            "Batch Processing Complete",
            f"Complete: {summary['complete']}\n"
            f"Failed: {summary['failed']}\n"
            f"Total: {summary['total']}"
        )
        
        self.accept()