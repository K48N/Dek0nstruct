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
    