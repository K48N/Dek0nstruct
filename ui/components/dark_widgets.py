"""
Custom UI components with portfolio-inspired dark theme
Production-ready widgets with consistent styling
"""
from PyQt5.QtWidgets import (QFrame, QLabel, QPushButton, QCheckBox,
                           QVBoxLayout, QHBoxLayout, QWidget, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
from ui.themes.dark_theme import PortfolioTheme

class DarkFrame(QFrame):
    """Dark themed frame widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {PortfolioTheme.BACKGROUND_COLOR}")
        
class DarkLabel(QLabel):
    """Dark themed label widget"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"color: {PortfolioTheme.TEXT_COLOR}")
        self.setFont(QFont("Inter", 10))
        
class DarkButton(QPushButton):
    """Dark themed button widget"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {PortfolioTheme.BUTTON_COLOR};
                color: {PortfolioTheme.TEXT_COLOR};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {PortfolioTheme.BUTTON_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PortfolioTheme.BUTTON_PRESSED_COLOR};
            }}
        """)
        self.setFont(QFont("Inter", 10))

class DarkCheckbutton(QCheckBox):
    """Dark themed checkbox widget"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {PortfolioTheme.TEXT_COLOR};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {PortfolioTheme.BUTTON_COLOR};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {PortfolioTheme.BUTTON_COLOR};
            }}
        """)
        self.setFont(QFont("Inter", 10))

# Additional PyQt widgets below
from PyQt5.QtWidgets import (QPushButton, QFrame, QLabel, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent
from ui.themes.dark_theme import PortfolioTheme


class ModernButton(QPushButton):
    """Styled button with variants: default, primary, success, danger"""
    
    def __init__(self, text: str, variant: str = "default", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setFont(QFont("Inter", 10, QFont.Medium))
        self.setProperty("class", variant)
        
    def set_loading(self, loading: bool):
        """Show loading state"""
        if loading:
            self.setEnabled(False)
            self.setText(self.text() + " ...")
        else:
            self.setEnabled(True)
            self.setText(self.text().replace(" ...", ""))


class DropZone(QFrame):
    """Drag and drop zone for video files"""
    
    fileDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)
        self._setup_ui()
        self._default_state = True
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel("🎬")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 56px;
            color: {PortfolioTheme.GRAY_LIGHTER};
        """)
        layout.addWidget(icon_label)
        
        # Main text
        self.text_label = QLabel("Drop video file here")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {PortfolioTheme.GRAY_LIGHTER};
        """)
        layout.addWidget(self.text_label)
        
        # Subtext
        self.subtext_label = QLabel("or click to browse")
        self.subtext_label.setAlignment(Qt.AlignCenter)
        self.subtext_label.setStyleSheet(f"""
            font-size: 13px;
            color: {PortfolioTheme.GRAY_LIGHT};
        """)
        layout.addWidget(self.subtext_label)
        
        # Supported formats
        formats_label = QLabel("MP4, AVI, MOV, MKV, WebM")
        formats_label.setAlignment(Qt.AlignCenter)
        formats_label.setStyleSheet(f"""
            font-size: 11px;
            color: {PortfolioTheme.GRAY_LIGHT};
            margin-top: 8px;
        """)
        layout.addWidget(formats_label)
        
        self._apply_default_style()
        
    def _apply_default_style(self):
        self.setStyleSheet(f"""
            DropZone {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PortfolioTheme.SECONDARY}, 
                    stop:1 {PortfolioTheme.PRIMARY});
                border: 2px dashed {PortfolioTheme.BORDER};
                border-radius: 12px;
                min-height: 180px;
            }}
            DropZone:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PortfolioTheme.TERTIARY}, 
                    stop:1 {PortfolioTheme.SECONDARY});
                border-color: {PortfolioTheme.ACCENT};
            }}
        """)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                DropZone {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {PortfolioTheme.ACCENT}, 
                        stop:1 {PortfolioTheme.ACCENT_PRESSED});
                    border: 2px solid {PortfolioTheme.ACCENT_HOVER};
                    border-radius: 12px;
                }}
            """)
            
    def dragLeaveEvent(self, event):
        self._apply_default_style()
        
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files and files[0]:
            self.fileDropped.emit(files[0])
        self._apply_default_style()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Trigger browse
            self.fileDropped.emit("")  # Empty = browse
            
    def set_file_loaded(self, filename: str):
        """Update UI to show loaded file"""
        self.text_label.setText(f"✓ {filename}")
        self.subtext_label.setText("Click to change")
        self.setStyleSheet(f"""
            DropZone {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PortfolioTheme.TERTIARY}, 
                    stop:1 {PortfolioTheme.SECONDARY});
                border: 2px solid {PortfolioTheme.ACCENT};
                border-radius: 12px;
            }}
        """)


class InfoCard(QFrame):
    """Information display card"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 600;
                color: {PortfolioTheme.GRAY_LIGHTER};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            """)
            layout.addWidget(title_label)
        
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet(f"""
            font-size: 13px;
            color: {PortfolioTheme.WHITE};
            line-height: 1.6;
        """)
        layout.addWidget(self.content_label)
        
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 8px;
            }}
        """)
        
    def set_content(self, text: str):
        """Update card content"""
        self.content_label.setText(text)
        
    def set_success(self):
        """Style as success card"""
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.SUCCESS};
                border-left: 4px solid {PortfolioTheme.SUCCESS};
                border-radius: 8px;
            }}
        """)
        
    def set_error(self):
        """Style as error card"""
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.ERROR};
                border-left: 4px solid {PortfolioTheme.ERROR};
                border-radius: 8px;
            }}
        """)
        
    def set_warning(self):
        """Style as warning card"""
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.WARNING};
                border-left: 4px solid {PortfolioTheme.WARNING};
                border-radius: 8px;
            }}
        """)


class StatusBadge(QLabel):
    """Small status indicator badge"""
    
    def __init__(self, text: str = "", status: str = "default", parent=None):
        super().__init__(text, parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignCenter)
        
    def set_status(self, status: str):
        """Set badge status: default, success, warning, error, info"""
        colors = {
            "default": (PortfolioTheme.GRAY, PortfolioTheme.WHITE),
            "success": (PortfolioTheme.SUCCESS, PortfolioTheme.WHITE),
            "warning": (PortfolioTheme.WARNING, PortfolioTheme.BLACK),
            "error": (PortfolioTheme.ERROR, PortfolioTheme.WHITE),
            "info": (PortfolioTheme.INFO, PortfolioTheme.WHITE),
            "accent": (PortfolioTheme.ACCENT, PortfolioTheme.WHITE)
        }
        
        bg, fg = colors.get(status, colors["default"])
        
        self.setStyleSheet(f"""
            StatusBadge {{
                background-color: {bg};
                color: {fg};
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)


class LoadingSpinner(QWidget):
    """Animated loading spinner"""
    
    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.setFixedSize(size, size)
        
        self.timer = self.startTimer(50)  # Update every 50ms
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw arc
        pen = QPen(QColor(PortfolioTheme.ACCENT))
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.drawArc(rect, self.angle * 16, 120 * 16)
        
    def timerEvent(self, event):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def hideEvent(self, event):
        if self.timer:
            self.killTimer(self.timer)
        super().hideEvent(event)


class MetricDisplay(QFrame):
    """Display for key metrics"""
    
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self._setup_ui(label, value)
        
    def _setup_ui(self, label: str, value: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        
        # Value (large)
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {PortfolioTheme.ACCENT};
            font-family: {PortfolioTheme.FONT_MONO};
        """)
        layout.addWidget(self.value_label)
        
        # Label (small)
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: 11px;
            color: {PortfolioTheme.GRAY_LIGHTER};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(label_widget)
        
        self.setStyleSheet(f"""
            MetricDisplay {{
                background-color: {PortfolioTheme.SECONDARY};
                border: 1px solid {PortfolioTheme.BORDER};
                border-radius: 8px;
            }}
        """)
        
    def set_value(self, value: str):
        """Update metric value"""
        self.value_label.setText(value)
        
        # Animate
        animation = QPropertyAnimation(self.value_label, b"geometry")
        animation.setDuration(200)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()


class SectionHeader(QLabel):
    """Section header with divider"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {PortfolioTheme.GRAY_LIGHTER};
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 8px 0;
            border-bottom: 1px solid {PortfolioTheme.BORDER};
        """)


class CollapsibleSection(QWidget):
    """Collapsible section with header"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self._setup_ui(title)
        
    def _setup_ui(self, title: str):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header button
        self.header_btn = QPushButton(f"▼ {title}")
        self.header_btn.clicked.connect(self.toggle)
        self.header_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PortfolioTheme.TERTIARY};
                border: none;
                border-radius: 6px;
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
                color: {PortfolioTheme.WHITE};
            }}
            QPushButton:hover {{
                background: {PortfolioTheme.GRAY};
            }}
        """)
        self.main_layout.addWidget(self.header_btn)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 0)
        self.main_layout.addWidget(self.content_widget)
        
    def toggle(self):
        """Toggle collapsed state"""
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        arrow = "▶" if self.is_collapsed else "▼"
        text = self.header_btn.text()[2:]  # Remove old arrow
        self.header_btn.setText(f"{arrow} {text}")
        
    def add_widget(self, widget: QWidget):
        """Add widget to content area"""
        self.content_layout.addWidget(widget)