"""
Timeline panel with waveform display and segment editing
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QCursor
from typing import List, Optional
import os

from core.segment import Segment
from ui.themes.dark_theme import PortfolioTheme


class TimelineWidget(QWidget):
    """Interactive timeline with segment visualization"""
    
    segment_clicked = pyqtSignal(int)  # index
    segment_modified = pyqtSignal(int, float, float)  # index, new_start, new_end
    add_segment_requested = pyqtSignal(float, float)  # start, end
    
    def __init__(self):
        super().__init__()
        self.segments: List[Segment] = []
        self.duration = 0.0
        self.current_time = 0.0
        self.waveform_image: Optional[QPixmap] = None
        
        # Interaction state
        self.selected_segment = -1
        self.dragging = False
        self.drag_edge = None  # 'start', 'end', or None
        self.drag_start_pos = 0
        self.hover_segment = -1
        self.hover_edge = None
        
        # Visual settings
        self.min_height = 120
        self.setMinimumHeight(self.min_height)
        self.setMouseTracking(True)
        
        # Styling
        self.setStyleSheet(f"""
            QWidget {{
                background: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 4px;
            }}
        """)
    
    def set_duration(self, duration: float):
        """Set video duration"""
        self.duration = duration
        self.update()
    
    def set_current_time(self, time: float):
        """Set current playback position"""
        self.current_time = time
        self.update()
    
    def set_segments(self, segments: List[Segment]):
        """Update segment list"""
        self.segments = segments
        self.update()
    
    def set_waveform(self, image_path: str):
        """Load waveform image"""
        if os.path.exists(image_path):
            self.waveform_image = QPixmap(image_path)
            self.update()
    
    def time_to_x(self, time: float) -> int:
        """Convert time to x coordinate"""
        if self.duration == 0:
            return 0
        margin = 10
        usable_width = self.width() - 2 * margin
        return int(margin + (time / self.duration) * usable_width)
    
    def x_to_time(self, x: int) -> float:
        """Convert x coordinate to time"""
        margin = 10
        usable_width = self.width() - 2 * margin
        time = ((x - margin) / usable_width) * self.duration
        return max(0, min(self.duration, time))
    
    def paintEvent(self, event):
        """Draw timeline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        margin = 10
        timeline_top = 40
        timeline_height = rect.height() - timeline_top - 30
        
        # Draw waveform background
        if self.waveform_image:
            waveform_rect = QRect(
                margin, timeline_top,
                rect.width() - 2 * margin, timeline_height
            )
            painter.setOpacity(0.3)
            painter.drawPixmap(waveform_rect, self.waveform_image)
            painter.setOpacity(1.0)
        
        # Draw timeline background
        timeline_rect = QRect(
            margin, timeline_top,
            rect.width() - 2 * margin, timeline_height
        )
        painter.fillRect(timeline_rect, QColor(PortfolioTheme.TERTIARY))
        
        # Draw time markers
        if self.duration > 0:
            painter.setPen(QPen(QColor(PortfolioTheme.GRAY_LIGHT), 1))
            num_markers = 10
            for i in range(num_markers + 1):
                time = (i / num_markers) * self.duration
                x = self.time_to_x(time)
                painter.drawLine(x, timeline_top, x, timeline_top + timeline_height)
                
                # Time label
                minutes = int(time // 60)
                seconds = int(time % 60)
                label = f"{minutes}:{seconds:02d}"
                painter.drawText(x - 20, timeline_top - 5, label)
        
        # Draw segments
        for i, segment in enumerate(self.segments):
            start_x = self.time_to_x(segment.start)
            end_x = self.time_to_x(segment.end)
            width = end_x - start_x
            
            # Segment color
            color = QColor(segment.color)
            if i == self.selected_segment:
                color.setAlpha(255)
            elif i == self.hover_segment:
                color.setAlpha(200)
            else:
                color.setAlpha(150)
            
            # Draw segment
            segment_rect = QRect(
                start_x, timeline_top,
                width, timeline_height
            )
            painter.fillRect(segment_rect, color)
            
            # Draw border
            if i == self.selected_segment:
                painter.setPen(QPen(QColor(PortfolioTheme.WHITE), 2))
            else:
                painter.setPen(QPen(QColor(PortfolioTheme.BORDER_LIGHT), 1))
            painter.drawRect(segment_rect)
            
            # Draw edge handles
            handle_width = 6
            if i == self.hover_segment or i == self.selected_segment:
                # Start handle
                handle_rect = QRect(
                    start_x - handle_width // 2, timeline_top,
                    handle_width, timeline_height
                )
                painter.fillRect(handle_rect, QColor(PortfolioTheme.ACCENT))
                
                # End handle
                handle_rect = QRect(
                    end_x - handle_width // 2, timeline_top,
                    handle_width, timeline_height
                )
                painter.fillRect(handle_rect, QColor(PortfolioTheme.ACCENT))
            
            # Draw label
            if width > 50:  # Only if enough space
                painter.setPen(QPen(QColor(PortfolioTheme.WHITE)))
                label_rect = QRect(start_x + 5, timeline_top + 5, width - 10, 20)
                painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignTop, segment.label)
        
        # Draw playback position
        if self.duration > 0:
            playback_x = self.time_to_x(self.current_time)
            painter.setPen(QPen(QColor(PortfolioTheme.ERROR), 2))
            painter.drawLine(
                playback_x, timeline_top,
                playback_x, timeline_top + timeline_height
            )
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() != Qt.LeftButton:
            return
        
        x = event.pos().x()
        time = self.x_to_time(x)
        
        # Check if clicking on a segment edge
        for i, segment in enumerate(self.segments):
            start_x = self.time_to_x(segment.start)
            end_x = self.time_to_x(segment.end)
            
            if abs(x - start_x) < 8:
                self.selected_segment = i
                self.dragging = True
                self.drag_edge = 'start'
                self.drag_start_pos = x
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return
            elif abs(x - end_x) < 8:
                self.selected_segment = i
                self.dragging = True
                self.drag_edge = 'end'
                self.drag_start_pos = x
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return
            elif start_x <= x <= end_x:
                self.selected_segment = i
                self.segment_clicked.emit(i)
                self.update()
                return
        
        # Clicked on empty space
        self.selected_segment = -1
        self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        x = event.pos().x()
        
        if self.dragging and self.selected_segment >= 0:
            # Dragging segment edge
            segment = self.segments[self.selected_segment]
            new_time = self.x_to_time(x)
            
            if self.drag_edge == 'start':
                new_start = max(0, min(new_time, segment.end - 1))
                self.segment_modified.emit(self.selected_segment, new_start, segment.end)
            elif self.drag_edge == 'end':
                new_end = max(segment.start + 1, min(new_time, self.duration))
                self.segment_modified.emit(self.selected_segment, segment.start, new_end)
            
            self.update()
        else:
            # Check for hover
            old_hover = self.hover_segment
            self.hover_segment = -1
            self.hover_edge = None
            
            for i, segment in enumerate(self.segments):
                start_x = self.time_to_x(segment.start)
                end_x = self.time_to_x(segment.end)
                
                if abs(x - start_x) < 8 or abs(x - end_x) < 8:
                    self.hover_segment = i
                    self.hover_edge = 'start' if abs(x - start_x) < 8 else 'end'
                    self.setCursor(QCursor(Qt.SizeHorCursor))
                    break
                elif start_x <= x <= end_x:
                    self.hover_segment = i
                    self.setCursor(QCursor(Qt.PointingHandCursor))
                    break
            
            if self.hover_segment == -1:
                self.setCursor(QCursor(Qt.ArrowCursor))
            
            if old_hover != self.hover_segment:
                self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.dragging = False
        self.drag_edge = None
        self.setCursor(QCursor(Qt.ArrowCursor))


class TimelinePanel(QWidget):
    """Complete timeline panel with controls"""
    
    segment_clicked = pyqtSignal(int)
    segment_modified = pyqtSignal(int, float, float)
    
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
        title = QLabel("Timeline")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {PortfolioTheme.WHITE};
            padding: 10px;
        """)
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Timeline widget
        self.timeline = TimelineWidget()
        self.timeline.segment_clicked.connect(self.segment_clicked.emit)
        self.timeline.segment_modified.connect(self.segment_modified.emit)
        layout.addWidget(self.timeline)
        
        # Info label
        self.info_label = QLabel("Load a video to start editing")
        self.info_label.setStyleSheet(f"""
            color: {PortfolioTheme.GRAY_LIGHTER};
            padding: 5px 10px;
            font-size: 12px;
        """)
        layout.addWidget(self.info_label)
    
    def set_duration(self, duration: float):
        """Set video duration"""
        self.timeline.set_duration(duration)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        self.info_label.setText(f"Total duration: {minutes}:{seconds:02d}")
    
    def set_current_time(self, time: float):
        """Set current time"""
        self.timeline.set_current_time(time)
    
    def set_segments(self, segments: List[Segment]):
        """Update segments"""
        self.timeline.set_segments(segments)
    
    def set_waveform(self, image_path: str):
        """Load waveform"""
        self.timeline.set_waveform(image_path)