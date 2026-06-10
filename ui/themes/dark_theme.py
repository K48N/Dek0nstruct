"""
Theme combining portfolio's dark aesthetic with KIT Karlsruhe's professional design
Clean, technical, and modern
"""

class PortfolioTheme:
    # Core Colors (Portfolio base)
    BLACK = "#000000"
    PRIMARY = "#0f0f0f"
    SECONDARY = "#1a1a1a"
    TERTIARY = "#222222"
    GRAY = "#2d2d2d"
    GRAY_LIGHT = "#666666"
    GRAY_LIGHTER = "#999999"
    WHITE = "#ffffff"
    
    # KIT Karlsruhe Brand Colors
    KIT_GREEN = "#009682"
    KIT_GREEN_LIGHT = "#00b89b"
    KIT_GREEN_DARK = "#007a6a"
    KIT_BLUE = "#4664aa"
    KIT_BLUE_LIGHT = "#5a7bc4"
    
    # Functional Colors
    ACCENT = KIT_GREEN
    ACCENT_HOVER = KIT_GREEN_LIGHT
    ACCENT_PRESSED = KIT_GREEN_DARK
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    ERROR = "#dc3545"
    INFO = KIT_BLUE
    
    # UI Elements
    BORDER = "rgba(255, 255, 255, 0.08)"
    BORDER_LIGHT = "rgba(255, 255, 255, 0.12)"
    BORDER_ACCENT = "rgba(0, 150, 130, 0.3)"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    GLOW = "rgba(0, 150, 130, 0.15)"
    
    # Typography (Technical/Academic)
    FONT_FAMILY = "'Inter', 'SF Pro Display', -apple-system, sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
    
    @classmethod
    def get_stylesheet(cls):
        return f"""
/* ===== GLOBAL RESET ===== */
* {{
    outline: none;
    margin: 0;
    padding: 0;
}}

QMainWindow, QWidget {{
    background-color: {cls.PRIMARY};
    color: {cls.WHITE};
    font-family: {cls.FONT_FAMILY};
    font-size: 13px;
    font-weight: 400;
}}

/* ===== MAIN WINDOW BACKGROUND GRADIENT ===== */
QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {cls.BLACK}, 
        stop:0.5 {cls.PRIMARY}, 
        stop:1 {cls.SECONDARY});
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background: {cls.SECONDARY};
    color: {cls.WHITE};
    border: 1px solid {cls.BORDER};
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 13px;
    letter-spacing: 0.3px;
}}

QPushButton:hover {{
    background: {cls.TERTIARY};
    border-color: {cls.BORDER_LIGHT};
}}

QPushButton:pressed {{
    background: {cls.GRAY};
    border-color: {cls.ACCENT};
}}

QPushButton:disabled {{
    background: {cls.SECONDARY};
    color: {cls.GRAY_LIGHT};
    border-color: {cls.BORDER};
}}

/* Primary Button (KIT Green) */
QPushButton[class="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {cls.KIT_GREEN_LIGHT}, stop:1 {cls.KIT_GREEN});
    color: {cls.WHITE};
    border: 1px solid {cls.KIT_GREEN};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 12px;
}}

QPushButton[class="primary"]:hover {{
    background: {cls.KIT_GREEN_LIGHT};
    box-shadow: 0 4px 12px {cls.GLOW};
}}

QPushButton[class="primary"]:pressed {{
    background: {cls.KIT_GREEN_DARK};
}}

/* Success Button */
QPushButton[class="success"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {cls.SUCCESS}, stop:1 #218838);
    border: 1px solid {cls.SUCCESS};
    color: {cls.WHITE};
    font-weight: 600;
}}

/* Danger Button */
QPushButton[class="danger"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {cls.ERROR}, stop:1 #c82333);
    border: 1px solid {cls.ERROR};
    color: {cls.WHITE};
    font-weight: 600;
}}

/* ===== INPUTS ===== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
    background-color: {cls.SECONDARY};
    border: 1px solid {cls.BORDER};
    border-radius: 6px;
    padding: 10px 14px;
    color: {cls.WHITE};
    selection-background-color: {cls.ACCENT};
    selection-color: {cls.WHITE};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
QComboBox:focus, QTextEdit:focus {{
    border-color: {cls.ACCENT};
    border-width: 2px;
    background-color: {cls.TERTIARY};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {cls.GRAY_LIGHTER};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {cls.TERTIARY};
    border: 1px solid {cls.BORDER_ACCENT};
    border-radius: 6px;
    selection-background-color: {cls.ACCENT};
    selection-color: {cls.WHITE};
    padding: 4px;
}}

/* ===== SCROLLBARS (Minimal) ===== */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {cls.GRAY};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {cls.GRAY_LIGHT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {cls.GRAY};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {cls.GRAY_LIGHT};
}}

/* ===== TABLES ===== */
QTableWidget {{
    background-color: {cls.PRIMARY};
    border: 1px solid {cls.BORDER};
    border-radius: 10px;
    gridline-color: {cls.BORDER};
    selection-background-color: {cls.ACCENT};
}}

QTableWidget::item {{
    padding: 12px 8px;
    border: none;
}}

QTableWidget::item:hover {{
    background-color: {cls.TERTIARY};
}}

QTableWidget::item:selected {{
    background-color: {cls.ACCENT};
    color: {cls.WHITE};
}}

QHeaderView::section {{
    background: {cls.SECONDARY};
    color: {cls.GRAY_LIGHTER};
    border: none;
    border-bottom: 2px solid {cls.ACCENT};
    padding: 12px 8px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QHeaderView::section:hover {{
    background: {cls.TERTIARY};
    color: {cls.WHITE};
}}

/* ===== PROGRESS BAR (KIT Style) ===== */
QProgressBar {{
    background-color: {cls.SECONDARY};
    border: 1px solid {cls.BORDER};
    border-radius: 8px;
    text-align: center;
    color: {cls.WHITE};
    font-weight: 600;
    height: 32px;
    font-family: {cls.FONT_MONO};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {cls.KIT_GREEN}, 
        stop:0.5 {cls.KIT_GREEN_LIGHT},
        stop:1 {cls.KIT_GREEN});
    border-radius: 7px;
}}

/* ===== GROUP BOX ===== */
QGroupBox {{
    border: 1px solid {cls.BORDER};
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
    font-size: 13px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {cls.SECONDARY}, stop:1 {cls.PRIMARY});
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 4px 12px;
    color: {cls.ACCENT};
    background-color: {cls.SECONDARY};
    border: 1px solid {cls.BORDER_ACCENT};
    border-radius: 6px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ===== TOOLBAR (Top Bar) ===== */
QToolBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {cls.SECONDARY}, stop:1 {cls.PRIMARY});
    border: none;
    border-bottom: 1px solid {cls.BORDER_ACCENT};
    spacing: 12px;
    padding: 12px 20px;
}}

QToolBar::separator {{
    background-color: {cls.BORDER};
    width: 1px;
    margin: 6px 10px;
}}

QToolButton {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    color: {cls.GRAY_LIGHTER};
    font-weight: 500;
    font-size: 13px;
}}

QToolButton:hover {{
    background-color: {cls.TERTIARY};
    color: {cls.WHITE};
}}

QToolButton:pressed {{
    background-color: {cls.ACCENT};
    color: {cls.WHITE};
}}

/* ===== STATUS BAR ===== */
QStatusBar {{
    background: {cls.SECONDARY};
    border-top: 1px solid {cls.BORDER_ACCENT};
    color: {cls.GRAY_LIGHTER};
    padding: 8px 20px;
    font-size: 12px;
    font-family: {cls.FONT_MONO};
}}

/* ===== MENU ===== */
QMenuBar {{
    background-color: {cls.SECONDARY};
    border-bottom: 1px solid {cls.BORDER};
    padding: 6px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 10px 18px;
    border-radius: 6px;
    font-weight: 500;
}}

QMenuBar::item:selected {{
    background-color: {cls.TERTIARY};
    color: {cls.ACCENT};
}}

QMenu {{
    background-color: {cls.TERTIARY};
    border: 1px solid {cls.BORDER_ACCENT};
    padding: 8px;
    border-radius: 10px;
}}

QMenu::item {{
    padding: 12px 40px 12px 20px;
    border-radius: 6px;
}}

QMenu::item:selected {{
    background-color: {cls.ACCENT};
    color: {cls.WHITE};
}}

QMenu::separator {{
    height: 1px;
    background-color: {cls.BORDER};
    margin: 8px 12px;
}}

/* ===== TOOLTIP ===== */
QToolTip {{
    background-color: {cls.TERTIARY};
    color: {cls.WHITE};
    border: 1px solid {cls.ACCENT};
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 12px;
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {cls.BORDER};
}}

QSplitter::handle:hover {{
    background-color: {cls.ACCENT};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* ===== SLIDER ===== */
QSlider::groove:horizontal {{
    background: {cls.SECONDARY};
    height: 8px;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {cls.ACCENT};
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid {cls.WHITE};
}}

QSlider::handle:horizontal:hover {{
    background: {cls.ACCENT_HOVER};
    width: 20px;
    height: 20px;
    margin: -6px 0;
}}

/* ===== LABELS ===== */
QLabel {{
    color: {cls.WHITE};
    background: transparent;
}}

QLabel[class="title"] {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.8px;
    color: {cls.WHITE};
}}

QLabel[class="subtitle"] {{
    font-size: 16px;
    font-weight: 500;
    color: {cls.GRAY_LIGHTER};
    letter-spacing: 0.2px;
}}

QLabel[class="caption"] {{
    font-size: 11px;
    color: {cls.GRAY_LIGHT};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel[class="mono"] {{
    font-family: {cls.FONT_MONO};
    font-size: 13px;
    color: {cls.ACCENT};
    background: {cls.SECONDARY};
    padding: 4px 8px;
    border-radius: 4px;
}}

QLabel[class="kit-badge"] {{
    background: {cls.KIT_GREEN};
    color: {cls.WHITE};
    font-weight: 700;
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 6px;
}}

/* ===== CHECKBOX & RADIO ===== */
QCheckBox, QRadioButton {{
    spacing: 10px;
    color: {cls.WHITE};
    font-size: 13px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {cls.BORDER};
    border-radius: 5px;
    background: {cls.SECONDARY};
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {cls.ACCENT};
    border-color: {cls.ACCENT};
    image: none;
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {cls.ACCENT};
}}

QRadioButton::indicator {{
    border-radius: 10px;
}}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {{
    background: {cls.SECONDARY};
    border: 1px solid {cls.BORDER};
    border-radius: 10px;
    top: -1px;
}}

QTabBar::tab {{
    background: {cls.TERTIARY};
    color: {cls.GRAY_LIGHTER};
    padding: 12px 24px;
    border: 1px solid {cls.BORDER};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background: {cls.SECONDARY};
    color: {cls.WHITE};
    border-bottom: 3px solid {cls.ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background: {cls.GRAY};
    color: {cls.WHITE};
}}

/* ===== DIALOG ===== */
QDialog {{
    background-color: {cls.SECONDARY};
    border: 1px solid {cls.BORDER_ACCENT};
    border-radius: 12px;
}}
"""