"""Main application window."""
import os
import json
import logging
import tempfile
from typing import List, Optional

from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QHBoxLayout,
                              QAction, QActionGroup, QFileDialog, QMessageBox,
                              QSplitter, QApplication, QInputDialog, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence

from core.segment import Segment
from core.video_engine import VideoEngine, ProcessingOptions
from core.undo_manager import UndoManager, AddSegmentCommand, RemoveSegmentCommand
from core.preset_manager import PresetManager
from core.audio_processor import AudioProcessor
from core.recent_projects import RecentProjectsManager
from core.autosave import AutoSaveManager
from ui.themes.dark_theme import PortfolioTheme
from ui.panels.control_panel import ControlPanel
from ui.panels.timeline_panel import TimelinePanel
from ui.panels.preview_panel import VideoPreview
from ui.panels.parts_panel import PartsPanel
from ui.panels.help import FULL_HELP_TEXT
from ui.dialogs.batch_dialog import BatchDialog
from ui.dialogs.scene_dialog import SceneDetectionDialog
from ui.dialogs.advanced_dialogs import VideoInfoDialog, AudioProcessingDialog
from config import config

logger = logging.getLogger(__name__)


class _ExportThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, engine, segments, output_dir, options):
        super().__init__()
        self.engine = engine
        self.segments = segments
        self.output_dir = output_dir
        self.options = options

    def run(self):
        try:
            results = self.engine.process_segments(
                self.segments, self.output_dir, self.options,
                progress_callback=self.progress.emit,
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = VideoEngine()
        self.undo_manager = UndoManager()
        self.preset_manager = PresetManager()
        self.audio_processor = AudioProcessor()
        self.recent_projects = RecentProjectsManager()
        self.autosave = AutoSaveManager()
        self.segments: List[Segment] = []
        self.current_video: Optional[str] = None
        self._export_thread: Optional[_ExportThread] = None
        self._debug_mode_action: Optional[QAction] = None
        self._mode_indicator = QLabel()
        self._audio_channel_actions = {}
        self._mp3_quality_actions = {}
        self._codec_copy_action: Optional[QAction] = None
        self._gpu_action: Optional[QAction] = None
        self._compatibility_action: Optional[QAction] = None
        self._parallel_action: Optional[QAction] = None
        self._export_both_action: Optional[QAction] = None

        self.autosave.set_save_callback(self._autosave_callback)
        self.autosave.start()

        self.setWindowTitle("Dek0nstruct")
        self.setMinimumSize(1024, 660)
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        self._apply_theme()
        self._apply_runtime_settings()
        self.statusBar().showMessage("Ready")

    # ── UI setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.control_panel = ControlPanel()
        control_scroll = QScrollArea()
        control_scroll.setWidgetResizable(True)
        control_scroll.setFrameShape(QScrollArea.NoFrame)
        control_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        control_scroll.setWidget(self.control_panel)

        right = QSplitter(Qt.Vertical)
        self.preview_panel = VideoPreview()
        self.preview_panel.set_ffmpeg(self.engine.ffmpeg)
        right.addWidget(self.preview_panel)

        self.timeline_panel = TimelinePanel()
        right.addWidget(self.timeline_panel)

        self.parts_panel = PartsPanel()
        right.addWidget(self.parts_panel)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(control_scroll)
        main_splitter.addWidget(right)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([340, 1060])

        right.setChildrenCollapsible(False)
        right.setStretchFactor(0, 4)
        right.setStretchFactor(1, 2)
        right.setStretchFactor(2, 3)
        right.setSizes([420, 220, 280])

        layout.addWidget(main_splitter, stretch=1)

    def _setup_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("File")
        self._action(file_menu, "Import Video\u2026", self._open_video, QKeySequence.Open)
        self._action(file_menu, "Load Project\u2026", self._load_project, "Ctrl+Shift+O")
        file_menu.addSeparator()
        self._action(file_menu, "Save Project", self._save_project, QKeySequence.Save)
        file_menu.addSeparator()
        self.recent_menu = file_menu.addMenu("Recent Projects")
        self._update_recent_menu()
        file_menu.addSeparator()
        self._action(file_menu, "Exit", self.close, QKeySequence.Quit)

        # Edit
        edit_menu = mb.addMenu("Edit")
        self.undo_action = self._action(edit_menu, "Undo", self._undo, QKeySequence.Undo)
        self.undo_action.setEnabled(False)
        self.redo_action = self._action(edit_menu, "Redo", self._redo, QKeySequence.Redo)
        self.redo_action.setEnabled(False)
        edit_menu.addSeparator()
        self._action(edit_menu, "Clear All Segments", self._clear_all_segments, "Ctrl+Shift+Backspace")

        # Export
        export_menu = mb.addMenu("Export")
        self._action(export_menu, "Export Segments…", self.control_panel.trigger_export, "Ctrl+E")
        export_menu.addSeparator()

        self._codec_copy_action = self._check_action(
            export_menu, "Fast Mode (Copy Codec)", True,
            lambda checked: self._update_advanced_setting("codec_copy", checked),
        )
        self._gpu_action = self._check_action(
            export_menu, "Use GPU Acceleration", True,
            lambda checked: self._update_advanced_setting("use_gpu", checked),
        )
        self._compatibility_action = self._check_action(
            export_menu, "Ultimate Compatibility Mode", True,
            lambda checked: self._update_advanced_setting("compatibility_mode", checked),
        )
        self._parallel_action = self._check_action(
            export_menu, "Parallel Processing", True,
            lambda checked: self._update_advanced_setting("parallel_processing", checked),
        )
        self._export_both_action = self._check_action(
            export_menu, "Export Both Video + Audio", False,
            lambda checked: self._update_advanced_setting("export_both_formats", checked),
        )

        export_menu.addSeparator()
        audio_menu = export_menu.addMenu("Audio Channels")
        audio_group = QActionGroup(self)
        audio_group.setExclusive(True)
        self._audio_channel_actions = {
            None: self._radio_action(audio_menu, audio_group, "Keep Original", True,
                                     lambda: self._update_advanced_setting("audio_channels", None)),
            "mono": self._radio_action(audio_menu, audio_group, "Mono", False,
                                         lambda: self._update_advanced_setting("audio_channels", "mono")),
            "stereo": self._radio_action(audio_menu, audio_group, "Stereo", False,
                                           lambda: self._update_advanced_setting("audio_channels", "stereo")),
        }

        quality_menu = export_menu.addMenu("MP3 Quality")
        quality_group = QActionGroup(self)
        quality_group.setExclusive(True)
        self._mp3_quality_actions = {
            0: self._radio_action(quality_menu, quality_group, "Best Quality", False,
                                  lambda: self._update_advanced_setting("mp3_quality", 0)),
            5: self._radio_action(quality_menu, quality_group, "Balanced", True,
                                  lambda: self._update_advanced_setting("mp3_quality", 5)),
            9: self._radio_action(quality_menu, quality_group, "Smallest File", False,
                                  lambda: self._update_advanced_setting("mp3_quality", 9)),
        }

        export_menu.addSeparator()
        self._action(export_menu, "Set Worker Threads…", self._set_worker_threads)

        # Tools
        tools_menu = mb.addMenu("Tools")
        self._action(tools_menu, "Batch Processing…", self._open_batch, "Ctrl+B")
        self._action(tools_menu, "Auto-Detect Segments…", self._open_scene_dialog, "Ctrl+D")
        tools_menu.addSeparator()
        self._action(tools_menu, "Manage Presets…", self._manage_presets)
        tools_menu.addSeparator()
        self._action(tools_menu, "Audio Processing…", self._open_audio, "Ctrl+Shift+A")
        self._action(tools_menu, "Video Information…", self._show_video_info, "Ctrl+I")
        tools_menu.addSeparator()
        self._debug_mode_action = QAction("Debug Mode")
        self._debug_mode_action.setCheckable(True)
        self._debug_mode_action.toggled.connect(self._set_debug_mode)
        tools_menu.addAction(self._debug_mode_action)



    @staticmethod
    def _action(menu, label: str, slot, shortcut=None) -> QAction:
        act = QAction(label)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut) if isinstance(shortcut, str) else shortcut)
        menu.addAction(act)
        return act

    @staticmethod
    def _check_action(menu, label: str, checked: bool, slot) -> QAction:
        act = QAction(label)
        act.setCheckable(True)
        act.setChecked(checked)
        act.toggled.connect(slot)
        menu.addAction(act)
        return act

    @staticmethod
    def _radio_action(menu, group: QActionGroup, label: str, checked: bool, slot) -> QAction:
        act = QAction(label)
        act.setCheckable(True)
        act.setChecked(checked)
        act.triggered.connect(slot)
        group.addAction(act)
        menu.addAction(act)
        return act

    def _set_worker_threads(self):
        current = self.control_panel.get_advanced_settings().get("max_workers", 4)
        value, ok = QInputDialog.getInt(
            self,
            "Worker Threads",
            "Number of worker threads:",
            int(current),
            1,
            16,
        )
        if ok:
            self._update_advanced_setting("max_workers", value)

    def _update_advanced_setting(self, key: str, value):
        settings = self.control_panel.get_advanced_settings()
        settings[key] = value
        self.control_panel.set_advanced_settings(**settings)
        self._refresh_mode_indicator()

    def _sync_advanced_menu_from_panel(self):
        settings = self.control_panel.get_advanced_settings()

        for action, key in (
            (self._codec_copy_action, "codec_copy"),
            (self._gpu_action, "use_gpu"),
            (self._compatibility_action, "compatibility_mode"),
            (self._parallel_action, "parallel_processing"),
            (self._export_both_action, "export_both_formats"),
        ):
            if action is not None:
                action.blockSignals(True)
                action.setChecked(bool(settings.get(key, False)))
                action.blockSignals(False)

        audio_channels = settings.get("audio_channels")
        for channel, action in self._audio_channel_actions.items():
            action.blockSignals(True)
            action.setChecked(channel == audio_channels)
            action.blockSignals(False)

        mp3_quality = settings.get("mp3_quality", 5)
        for quality, action in self._mp3_quality_actions.items():
            action.blockSignals(True)
            action.setChecked(quality == mp3_quality)
            action.blockSignals(False)

    def _connect_signals(self):
        self.control_panel.import_requested.connect(self._open_video)
        self.control_panel.load_project_requested.connect(self._load_project)
        self.control_panel.help_requested.connect(self._show_help_guide)
        self.control_panel.export_requested.connect(self._start_export)
        self.preview_panel.position_changed.connect(self.timeline_panel.set_current_time)
        self.preview_panel.add_segment_button.clicked.connect(self._add_segment_from_preview)
        self.timeline_panel.segment_clicked.connect(self._on_segment_clicked)
        self.timeline_panel.segment_modified.connect(self._on_segment_modified_timeline)
        self.parts_panel.segment_clicked.connect(self._on_segment_clicked)
        self.parts_panel.segment_modified.connect(self._on_segment_modified_table)
        self.parts_panel.segment_deleted.connect(self._delete_segment)
        self.parts_panel.clear_all_requested.connect(self._clear_all_segments)
        self.undo_manager.add_callback(self._update_undo_actions)

    def _apply_theme(self):
        self.setStyleSheet(PortfolioTheme.get_stylesheet())
        accent_css = f"""
            QMenuBar {{
                background:{PortfolioTheme.SECONDARY};color:{PortfolioTheme.WHITE};
                border-bottom:1px solid {PortfolioTheme.BORDER};
            }}
            QMenuBar::item:selected {{background:{PortfolioTheme.TERTIARY};}}
            QMenu {{
                background:{PortfolioTheme.TERTIARY};color:{PortfolioTheme.WHITE};
                border:1px solid {PortfolioTheme.BORDER};
            }}
            QMenu::item:selected {{background:{PortfolioTheme.ACCENT};}}
        """
        self.menuBar().setStyleSheet(accent_css)
        self.statusBar().setStyleSheet(
            f"QStatusBar {{background:{PortfolioTheme.SECONDARY};"
            f"color:{PortfolioTheme.GRAY_LIGHTER};border-top:1px solid {PortfolioTheme.BORDER};}}"
        )
        self._mode_indicator.setStyleSheet(
            f"color:{PortfolioTheme.GRAY_LIGHTER}; padding:0 8px;"
        )
        self.statusBar().addPermanentWidget(self._mode_indicator)

    def _apply_runtime_settings(self):
        debug_mode = bool(config.get("app", "debug_mode"))
        self._set_debug_mode(debug_mode, persist=False, announce=False)
        self._sync_advanced_menu_from_panel()

    def _set_debug_mode(self, enabled: bool, persist: bool = True, announce: bool = True):
        debug_enabled = bool(enabled)
        if self._debug_mode_action:
            self._debug_mode_action.blockSignals(True)
            self._debug_mode_action.setChecked(debug_enabled)
            self._debug_mode_action.blockSignals(False)

        self.engine.ffmpeg.debug_mode = debug_enabled
        logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
        self._refresh_mode_indicator()

        if persist:
            config.set("app", "debug_mode", debug_enabled)
            config.save()

        if announce:
            self.statusBar().showMessage(
                "Debug mode enabled" if debug_enabled else "Debug mode disabled",
                3000,
            )

    def _refresh_mode_indicator(self):
        debug_enabled = bool(self.engine.ffmpeg.debug_mode)
        compatibility = self.control_panel.get_advanced_settings().get("compatibility_mode", True)
        self._mode_indicator.setText(
            f"Mode: {'DEBUG' if debug_enabled else 'NORMAL'} | Compatibility: {'ON' if compatibility else 'OFF'}"
        )

    # ── video ─────────────────────────────────────────────────────────────────

    def _open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv *.webm);;All Files (*)"
        )
        if not path:
            return
        try:
            info = self.engine.load_video(path)
        except Exception as e:
            logger.exception("Failed to probe video: %s", path)
            QMessageBox.critical(self, "Error", f"Failed to load video:\n{e}")
            return

        self.current_video = path
        self.timeline_panel.set_duration(info["duration"])
        self.segments.clear()
        self.undo_manager.clear()
        self._update_ui()

        # VLC handles all formats natively — load directly, no conversion needed
        self.preview_panel.load_video(path, info["duration"])
        dur = info["duration"]
        self.statusBar().showMessage(
            f"Loaded: {os.path.basename(path)} "
            f"({int(dur//60)}:{int(dur%60):02d})"
        )
        if dur < 3600:
            QTimer.singleShot(500, self._generate_waveform)

    def _generate_waveform(self):
        if not self.current_video:
            return
        try:
            tmp = os.path.join(tempfile.gettempdir(), "dek0_waveform.png")
            if self.engine.generate_waveform(tmp):
                self.timeline_panel.set_waveform(tmp)
        except Exception:
            pass

    # ── segments ──────────────────────────────────────────────────────────────

    def _add_segment_from_preview(self):
        start, end = self.preview_panel.get_segment_range()
        if end <= start:
            return
        seg = Segment(start=start, end=end, label=f"Part {len(self.segments) + 1}")
        self.undo_manager.execute(AddSegmentCommand(self.segments, seg))
        self.preview_panel.clear_markers()
        self._update_ui()
        self.statusBar().showMessage(f"Added segment: {seg.label}")

    def _delete_segment(self, index: int):
        if 0 <= index < len(self.segments):
            self.undo_manager.execute(
                RemoveSegmentCommand(self.segments, self.segments[index])
            )
            self._update_ui()

    def _clear_all_segments(self):
        if not self.segments:
            return
        if QMessageBox.question(self, "Clear All", "Delete all segments?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.segments.clear()
            self.undo_manager.clear()
            self._update_ui()

    def _on_segment_clicked(self, index: int):
        if 0 <= index < len(self.segments):
            self.preview_panel.seek_to(self.segments[index].start)
            self.parts_panel.select_segment(index)

    def _on_segment_modified_timeline(self, index: int, new_start: float, new_end: float):
        if 0 <= index < len(self.segments):
            self.segments[index].start = new_start
            self.segments[index].end = new_end
            self._update_ui()

    def _on_segment_modified_table(self, index: int, segment: Segment):
        if 0 <= index < len(self.segments):
            self.segments[index] = segment
            self._update_ui()

    def _update_ui(self):
        self.timeline_panel.set_segments(self.segments)
        self.parts_panel.set_segments(self.segments)
        self.control_panel.set_export_enabled(bool(self.segments))
        self._refresh_mode_indicator()

    # ── undo/redo ─────────────────────────────────────────────────────────────

    def _undo(self):
        if self.undo_manager.undo():
            self._update_ui()

    def _redo(self):
        if self.undo_manager.redo():
            self._update_ui()

    def _update_undo_actions(self):
        self.undo_action.setEnabled(self.undo_manager.can_undo())
        self.redo_action.setEnabled(self.undo_manager.can_redo())

    # ── export ────────────────────────────────────────────────────────────────

    def _start_export(self, output_dir: str, options: ProcessingOptions):
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Add segments before exporting.")
            return
        errors = self.engine.validate_segments(self.segments)
        if errors:
            QMessageBox.critical(self, "Validation Error", "\n".join(errors))
            return
        self._export_thread = _ExportThread(
            self.engine, self.segments, output_dir, options
        )
        self._export_thread.progress.connect(self.control_panel.show_progress)
        self._export_thread.finished.connect(self._on_export_done)
        self._export_thread.error.connect(self._on_export_error)
        self._export_thread.start()
        self.control_panel.set_export_enabled(False)

    def _on_export_done(self, results: list):
        self.control_panel.hide_progress()
        self.control_panel.set_export_enabled(True)
        ok = sum(1 for r in results if r.success)
        QMessageBox.information(self, "Export Complete", f"Exported {ok} segment(s).")

    def _on_export_error(self, error: str):
        self.control_panel.hide_progress()
        self.control_panel.set_export_enabled(True)
        QMessageBox.critical(self, "Export Error", error)

    # ── dialogs ───────────────────────────────────────────────────────────────

    def _open_batch(self):
        if not self.segments:
            QMessageBox.warning(self, "No Segments", "Create segments first.")
            return
        BatchDialog(self.segments, self).exec_()

    def _open_scene_dialog(self):
        if not self.current_video:
            QMessageBox.warning(self, "No Video", "Load a video first.")
            return
        duration = self.engine.video_info.get("duration", 0.0) if self.engine.video_info else 0.0
        ffmpeg = self.engine.ffmpeg.ffmpeg_path or "ffmpeg"
        dlg = SceneDetectionDialog(self.current_video, duration=duration,
                                   ffmpeg_path=ffmpeg, parent=self)
        dlg.segments_detected.connect(self._add_detected_segments)
        dlg.exec_()

    def _add_detected_segments(self, segments: List[Segment]):
        for seg in segments:
            self.undo_manager.execute(AddSegmentCommand(self.segments, seg))
        self._update_ui()
        self.statusBar().showMessage(f"Added {len(segments)} detected segment(s)")

    def _manage_presets(self):
        presets = self.preset_manager.list_presets()
        if not presets:
            QMessageBox.information(self, "Presets", "No presets saved yet.")
            return
        name, ok = QInputDialog.getItem(self, "Load Preset", "Select preset:", presets, 0, False)
        if ok and name:
            opts = self.preset_manager.load_preset(name)
            if opts:
                self._apply_preset(opts)
                self.statusBar().showMessage(f"Loaded preset: {name}")

    def _apply_preset(self, options: ProcessingOptions):
        cp = self.control_panel
        cp.video_format_combo.setCurrentText(options.output_format)
        cp.audio_format_combo.setCurrentText(options.audio_output_format)
        cp.set_advanced_settings(
            audio_channels=options.audio_channels,
            mp3_quality=options.mp3_quality,
            use_gpu=options.use_gpu,
            codec_copy=options.codec_copy,
            parallel_processing=options.parallel_processing,
            max_workers=options.max_workers,
            compatibility_mode=options.compatibility_mode,
            export_both_formats=options.export_both_formats,
        )
        self._sync_advanced_menu_from_panel()
        self._refresh_mode_indicator()

    def _show_video_info(self):
        if not self.current_video or not self.engine.video_info:
            QMessageBox.warning(self, "No Video", "Load a video first.")
            return
        VideoInfoDialog(self.engine.video_info, self).exec_()

    def _open_audio(self):
        if not self.current_video:
            QMessageBox.warning(self, "No Video", "Load a video first.")
            return
        dlg = AudioProcessingDialog(self)
        dlg.processing_requested.connect(self._process_audio)
        dlg.exec_()

    def _process_audio(self, operation: str, params: dict):
        if not self.current_video:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save Output", "",
                                              "Video Files (*.mp4 *.mkv)")
        if not out:
            return
        try:
            self.statusBar().showMessage(f"Processing audio ({operation})\u2026")
            QApplication.processEvents()
            ok = self.audio_processor.process_video_audio(
                self.current_video, out, operation, **params
            )
            msg = f"Saved to: {out}" if ok else "Audio processing failed."
            (QMessageBox.information if ok else QMessageBox.warning)(
                self, "Audio", msg
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed:\n{e}")
        finally:
            self.statusBar().showMessage("Ready")

    # ── project ───────────────────────────────────────────────────────────────

    def _save_project(self):
        if not self.segments:
            QMessageBox.warning(self, "Nothing to Save", "No segments to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "Project Files (*.vedproj)"
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump({
                    "video": self.current_video,
                    "segments": [s.to_dict() for s in self.segments],
                }, f, indent=2)
            self.recent_projects.add_project(path, self.current_video)
            self._update_recent_menu()
            self.statusBar().showMessage(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "Project Files (*.vedproj)"
        )
        if not path:
            return
        self._load_project_file(path)

    def _load_project_file(self, path: str):
        try:
            with open(path) as f:
                data = json.load(f)
            video = data.get("video")
            if video and os.path.exists(video):
                info = self.engine.load_video(video)
                self.current_video = video
                self.preview_panel.load_video(video, info["duration"])
                self.timeline_panel.set_duration(info["duration"])
            self.segments = [Segment.from_dict(s) for s in data.get("segments", [])]
            self._update_ui()
            self.recent_projects.add_project(path, data.get("video"))
            self._update_recent_menu()
            self.statusBar().showMessage(f"Loaded: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load:\n{e}")

    def _autosave_callback(self, backup_path: str):
        if not self.segments:
            return
        try:
            with open(backup_path, "w") as f:
                json.dump({
                    "video": self.current_video,
                    "segments": [s.to_dict() for s in self.segments],
                }, f)
        except Exception:
            pass

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recent = self.recent_projects.get_recent()
        if not recent:
            act = self.recent_menu.addAction("No Recent Projects")
            act.setEnabled(False)
            return
        for proj in recent[:10]:
            act = self.recent_menu.addAction(proj["name"])
            act.triggered.connect(
                lambda _checked, p=proj["path"]: self._load_project_file(p)
            )
        self.recent_menu.addSeparator()
        clear = self.recent_menu.addAction("Clear Recent")
        clear.triggered.connect(self._clear_recent)

    def _clear_recent(self):
        self.recent_projects.clear()
        self._update_recent_menu()

    def _show_about(self):
        QMessageBox.about(
            self, "About Dek0nstruct",
            "Dek0nstruct\n\nProfessional video segment editor.\n"
            "Cut, label, and export video segments with FFmpeg."
        )

    def _show_help_guide(self):
        QMessageBox.information(self, "Help", FULL_HELP_TEXT)

    def _show_shortcuts(self):
        QMessageBox.information(self, "Help", FULL_HELP_TEXT)


