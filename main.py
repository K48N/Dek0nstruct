"""Dek0nstruct — entry point."""
import sys
import logging
import traceback
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from config import config
from services import ServiceRegistry, BackgroundJobManager, ExportQueueService, MediaCacheService
from ui.main_app import VideoEditorApp

logger = logging.getLogger(__name__)


def _setup_logging():
    log_file = Path(config.get("export", "temp_directory")) / "dek0nstruct.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        handlers=[logging.FileHandler(str(log_file)), logging.StreamHandler()],
    )


def _init_services():
    registry = ServiceRegistry()
    registry.register(BackgroundJobManager)
    registry.register(MediaCacheService)
    registry.register(ExportQueueService)
    try:
        registry.start_all()
        logger.info("Services started")
    except Exception as e:
        logger.error("Service startup error: %s", e)


def _check_recovery():
    try:
        from core.autosave import AutoSaveManager
        mgr = AutoSaveManager()
        if not mgr.has_recovery_files():
            return
        reply = QMessageBox.question(
            None, "Crash Recovery",
            "Found auto-saved projects from a previous session.\nRecover them?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            files = mgr.get_recovery_files()
            names = "\n".join(f["name"] for f in files[:5])
            QMessageBox.information(None, "Recovery",
                f"Use File to open them.\n\n{names}")
        else:
            mgr.clear_recovery_files()
    except Exception as e:
        logger.warning("Crash recovery check failed: %s", e)


def _exception_hook(exctype, value, tb):
    logger.critical("Unhandled exception", exc_info=(exctype, value, tb))
    traceback.print_exception(exctype, value, tb)
    QMessageBox.critical(None, "Unexpected Error", f"{value}\n\nSee log for details.")


def main() -> int:
    _setup_logging()
    logger.info("Starting Dek0nstruct")
    sys.excepthook = _exception_hook

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("Dek0nstruct")
    app.setStyle("Fusion")

    _init_services()
    app.aboutToQuit.connect(lambda: ServiceRegistry().stop_all())
    _check_recovery()

    window = VideoEditorApp()
    window.show()
    logger.info("Application started successfully")
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
