"""
Parts table panel with editable segments
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                            QMenu, QAction, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List

from core.segment import Segment
from ui.themes.dark_theme import PortfolioTheme


class PartsTable(QTableWidget):
    """Editable parts table"""
    
    segment_clicked = pyqtSignal(int)
    segment_modified = pyqtSignal(int, Segment)
    segment_deleted = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.segments: List[Segment] = []
        self._setup_table()
    
    def _setup_table(self):
        """Setup table"""
        # Columns
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Label", "Start", "End", "Duration", "Video", "Audio"
        ])
        
        # Styling
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {PortfolioTheme.SECONDARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
                gridline-color: {PortfolioTheme.BORDER};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background: {PortfolioTheme.ACCENT};
            }}
            QHeaderView::section {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {PortfolioTheme.BORDER};
                font-weight: 600;
            }}
        """)
        
        # Column sizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Label
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Start
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # End
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Video
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Audio
        
        # Behavior
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemChanged.connect(self._on_item_changed)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_segments(self, segments: List[Segment]):
        """Update table with segments"""
        self.segments = segments
        self.setRowCount(len(segments))
        
        for i, segment in enumerate(segments):
            self._populate_row(i, segment)
    
    def _populate_row(self, row: int, segment: Segment):
        """Populate table row"""
        # Block signals while populating
        self.blockSignals(True)
        
        # Label with color
        label_item = QTableWidgetItem(segment.label)
        label_item.setBackground(QColor(segment.color))
        self.setItem(row, 0, label_item)
        
        # Start time
        start_item = QTableWidgetItem(self._format_time(segment.start))
        start_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 1, start_item)
        
        # End time
        end_item = QTableWidgetItem(self._format_time(segment.end))
        end_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 2, end_item)
        
        # Duration
        duration_item = QTableWidgetItem(self._format_time(segment.duration))
        duration_item.setTextAlignment(Qt.AlignCenter)
        duration_item.setFlags(duration_item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, 3, duration_item)
        
        # Video checkbox
        video_item = QTableWidgetItem("✓" if segment.export_video else "✗")
        video_item.setTextAlignment(Qt.AlignCenter)
        video_item.setFlags(video_item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, 4, video_item)
        
        # Audio checkbox
        audio_item = QTableWidgetItem("✓" if segment.export_audio else "✗")
        audio_item.setTextAlignment(Qt.AlignCenter)
        audio_item.setFlags(audio_item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, 5, audio_item)
        
        self.blockSignals(False)
    
    def _format_time(self, seconds: float) -> str:
        """Format time as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def _parse_time(self, time_str: str) -> float:
        """Parse MM:SS to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
        except:
            pass
        return 0.0
    
    def _on_item_clicked(self, item):
        """Handle item click"""
        row = item.row()
        col = item.column()
        
        # Double-click on time columns for precision input
        if col in [1, 2]:
            from ui.dialogs.advanced_dialogs import TimeInputDialog
            
            segment = self.segments[row]
            current_time = segment.start if col == 1 else segment.end
            label = "Start Time" if col == 1 else "End Time"
            
            dialog = TimeInputDialog(current_time, label, self)
            if dialog.exec_() == QDialog.Accepted:
                new_time = dialog.get_time()
                if col == 1:
                    segment.start = new_time
                else:
                    segment.end = new_time
                self.segment_modified.emit(row, segment)
                self._populate_row(row, segment)
        else:
            self.segment_clicked.emit(row)
    
    def _on_item_changed(self, item):
        """Handle item edit"""
        if self.signalsBlocked():
            return
        
        row = item.row()
        col = item.column()
        
        if row >= len(self.segments):
            return
        
        segment = self.segments[row]
        
        # Handle edits
        if col == 0:  # Label
            segment.label = item.text()
            self.segment_modified.emit(row, segment)
        elif col == 1:  # Start
            new_start = self._parse_time(item.text())
            if new_start < segment.end:
                segment.start = new_start
                self.segment_modified.emit(row, segment)
            self._populate_row(row, segment)
        elif col == 2:  # End
            new_end = self._parse_time(item.text())
            if new_end > segment.start:
                segment.end = new_end
                self.segment_modified.emit(row, segment)
            self._populate_row(row, segment)
    
    def _show_context_menu(self, position):
        """Show context menu"""
        row = self.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {PortfolioTheme.TERTIARY};
                color: {PortfolioTheme.WHITE};
                border: 1px solid {PortfolioTheme.BORDER};
            }}
            QMenu::item:selected {{
                background: {PortfolioTheme.ACCENT};
            }}
        """)
        
        # Color action (Phase 5)
        color_action = QAction("Change Color", self)
        color_action.triggered.connect(lambda: self._change_color(row))
        menu.addAction(color_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete Segment", self)
        delete_action.triggered.connect(lambda: self.segment_deleted.emit(row))
        menu.addAction(delete_action)
        
        toggle_video = QAction("Toggle Video Export", self)
        toggle_video.triggered.connect(lambda: self._toggle_export(row, 'video'))
        menu.addAction(toggle_video)
        
        toggle_audio = QAction("Toggle Audio Export", self)
        toggle_audio.triggered.connect(lambda: self._toggle_export(row, 'audio'))
        menu.addAction(toggle_audio)
        
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def _change_color(self, row: int):
        """Change segment color (Phase 5)"""
        if row >= len(self.segments):
            return
        
        from ui.dialogs.advanced_dialogs import ColorPickerDialog
        
        segment = self.segments[row]
        dialog = ColorPickerDialog(segment.color, self)
        
        if dialog.exec_() == QDialog.Accepted:
            segment.color = dialog.get_color()
            self.segment_modified.emit(row, segment)
            self._populate_row(row, segment)
    
    def _toggle_export(self, row: int, export_type: str):
        """Toggle export option"""
        if row >= len(self.segments):
            return
        
        segment = self.segments[row]
        if export_type == 'video':
            segment.export_video = not segment.export_video
        elif export_type == 'audio':
            segment.export_audio = not segment.export_audio
        
        self.segment_modified.emit(row, segment)
        self._populate_row(row, segment)
    
    def select_segment(self, index: int):
        """Select segment by index"""
        if 0 <= index < self.rowCount():
            self.selectRow(index)


class PartsPanel(QWidget):
    """Parts table panel with controls"""
    
    segment_clicked = pyqtSignal(int)
    segment_modified = pyqtSignal(int, Segment)
    segment_deleted = pyqtSignal(int)
    clear_all_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Segments")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {PortfolioTheme.WHITE};
            padding: 10px;
        """)
        header.addWidget(title)
        
        self.count_label = QLabel("0 segments")
        self.count_label.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            padding: 10px;
        """)
        header.addWidget(self.count_label)
        
        header.addStretch()
        
        # Clear all button
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.ERROR};
                color: {PortfolioTheme.WHITE};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: #c82333;
            }}
        """)
        clear_btn.clicked.connect(self.clear_all_requested.emit)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Table
        self.table = PartsTable()
        self.table.segment_clicked.connect(self.segment_clicked.emit)
        self.table.segment_modified.connect(self.segment_modified.emit)
        self.table.segment_deleted.connect(self.segment_deleted.emit)
        layout.addWidget(self.table)
        
        # Info label
        self.info_label = QLabel("Add segments using the video preview controls")
        self.info_label.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            padding: 5px 10px;
            font-size: 12px;
        """)
        layout.addWidget(self.info_label)
    
    def set_segments(self, segments: List[Segment]):
        """Update segments"""
        self.table.set_segments(segments)
        self.count_label.setText(f"{len(segments)} segment{'s' if len(segments) != 1 else ''}")
        
        # Update info
        if segments:
            total_duration = sum(s.duration for s in segments)
            minutes = int(total_duration // 60)
            seconds = int(total_duration % 60)
            self.info_label.setText(
                f"Total output duration: {minutes}:{seconds:02d}"
            )
        else:
            self.info_label.setText("Add segments using the video preview controls")
    
    def select_segment(self, index: int):
        """Select segment"""
        self.table.select_segment(index)