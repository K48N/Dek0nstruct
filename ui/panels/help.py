"""In-app help text content for quick guidance and shortcuts."""

QUICK_HELP_TEXT = (
	"1. File -> Import Video to load source media.\n"
	"2. Use preview controls to set In/Out markers.\n"
	"3. Add segments from the preview and refine in Timeline/Segments.\n"
	"4. Configure export format in the left panel.\n"
	"5. Run Export -> Export Segments when ready."
)

SHORTCUTS_HELP_TEXT = (
	"File\n"
	"- Ctrl+O: Import Video\n"
	"- Ctrl+Shift+O: Load Project\n"
	"- Ctrl+S: Save Project\n\n"
	"Playback / Editing\n"
	"- Space: Play / Pause\n"
	"- Left/Right: Seek 1 second\n"
	"- J/L: Seek -10s / +10s\n"
	"- I / O: Set In / Set Out\n"
	"- Ctrl+Enter: Add Segment\n\n"
	"Export\n"
	"- Ctrl+E: Export Segments\n\n"
	"Tools\n"
	"- Ctrl+B: Batch Processing\n"
	"- Ctrl+D: Auto-Detect Segments\n"
	"- Ctrl+Shift+A: Audio Processing\n"
	"- Ctrl+I: Video Information\n\n"
	"General\n"
	"- F1: Quick Start Help\n"
	"- Ctrl+/: Keyboard Shortcuts"
)

FULL_HELP_TEXT = (
	f"{QUICK_HELP_TEXT}\n\n"
	"Keyboard Shortcuts\n"
	"------------------\n"
	f"{SHORTCUTS_HELP_TEXT}"
)
