# Dek0nstruct

A desktop video segmentation tool built with Python and PyQt5. Load any video, mark in/out points, build a list of segments, and export them — individually or in batch — to any format via FFmpeg. Designed for fast, precise clip extraction without a timeline-heavy NLE workflow.

## Features
- **VLC-powered preview** with full audio, volume control, and seek slider
- **In/Out point markers** to define segments with frame-accurate timestamps
- **Segment list** with reorder, rename, delete, and undo/redo support
- **Flexible export** to MP4, MKV, AVI, MOV, WebM, MP3, WAV, AAC, FLAC
- **Batch processing** for exporting many segments or files at once
- **Auto scene detection** to split a video into segments automatically
- **Project save/load** — resume work at any time with `.vedproj` files
- **Autosave + crash recovery** so you never lose a session
- **Export settings** in the top menu: GPU acceleration, codec copy, compatibility mode, audio channels, MP3 quality

## Requirements

- **Python 3.10+**
- **FFmpeg** — must be on your `PATH` or installed at `%LOCALAPPDATA%\Programs\ffmpeg\current\bin\`
  - Download: https://ffmpeg.org/download.html
- **VLC** — required for video preview with audio
  - Download: https://www.videolan.org/vlc/ (install to default location)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/yourname/dek0nstruct.git
cd dek0nstruct

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

## How To Use

### Basic Editing Flow
1. Click **Import Video** in the left panel and select any video file
2. Use the **seek slider** or `← →` arrow keys to navigate
3. Press **I** (or *Set In*) at the start of a clip, **O** (or *Set Out*) at the end
4. Click **Add Segment** — the segment appears in the list on the right
5. Repeat for as many segments as you need
6. Choose your output format in the left panel, click **Export All Segments**

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `← →` | Seek ±1 second |
| `I` | Set In point |
| `O` | Set Out point |
| `Ctrl+Z / Ctrl+Y` | Undo / Redo |
| `Ctrl+S` | Save project |
| `Ctrl+Shift+O` | Load project |
| `Ctrl+E` | Export |
| `Ctrl+B` | Batch processing |
| `Ctrl+D` | Auto-detect scenes |
| `F1` | Help |

### Saving and Loading Projects
- **Save**: left panel → `Save Project` button, or `Ctrl+S`
- **Load**: left panel → `Load Project` button, or `Ctrl+Shift+O`
- Projects are saved as `.vedproj` JSON files — portable and human-readable

### Export Options (top Export menu)
| Option | Description |
|--------|-------------|
| Fast Mode (Copy Codec) | Copies streams without re-encoding — very fast, lossless |
| Use GPU Acceleration | Uses NVENC/QSV/AMF if available |
| Ultimate Compatibility Mode | Forces widely-compatible codecs for maximum device support |
| Parallel Processing | Exports multiple segments simultaneously |
| Export Both Video + Audio | Produces a video file and a separate audio-only file |
| Audio Channels | Keep original / force Mono / force Stereo |
| MP3 Quality | Best / Balanced / Smallest |

## Project Structure

```
dek0nstruct/
├── main.py                  # Entry point
├── config.py                # App configuration
├── requirements.txt
├── core/                    # Business logic (segments, engine, undo, presets…)
├── models/                  # Data models (ExportJob…)
├── services/                # Background services (jobs, cache, export queue)
├── ui/
│   ├── main_app.py          # Main window + menus
│   ├── panels/              # Left panel, preview, timeline, parts list
│   ├── dialogs/             # Batch, scene detection, advanced dialogs
│   ├── components/          # Shared widgets
│   └── themes/              # Dark theme stylesheet
├── utils/
│   ├── ffmpeg_wrapper.py    # All FFmpeg calls
│   └── exceptions.py
└── tests/
```

## Troubleshooting

**No video in the preview / black screen**
- Make sure VLC is installed to its default location (`C:\Program Files\VideoLAN\VLC`)
- If VLC is installed elsewhere, update `_VLC_DIR` at the top of `ui/panels/preview_panel.py`

**FFmpeg not found**
- Install FFmpeg and ensure it is on your `PATH`: run `ffmpeg -version` in a terminal to verify
- Or install to `%LOCALAPPDATA%\Programs\ffmpeg\current\bin\ffmpeg.exe`

**Export fails**
- Check that the source file still exists at its original path
- Ensure the output directory is writable
- Enable *Debug Mode* (Tools menu) for full FFmpeg command logging

**App crashes on startup**
- Check the log file at `%TEMP%\dek0nstruct.log`
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## Running Tests

```bash
pytest
```

## License

See [LICENSE](LICENSE).


## Features
- **Precise segment editing** with timeline controls, in/out points, and validation
- **AI-assisted workflows** for scene detection, speech-to-text, and smart classification
- **Audio enhancement pipeline** with voice clarity, ducking, and loudness controls
- **Background export queue** with persisted jobs and status tracking
- **Crash recovery + autosave** to reduce lost work
- **Reusable project and export profiles** for repeatable output

## How It Works
1. Launches the Qt desktop app and initializes core services
2. Loads a source video and extracts media metadata with FFmpeg
3. Lets you create and adjust segments in the timeline UI
4. Applies export/audio options and queues jobs for background processing
5. Saves projects, recent files, logs, and recovery data in a local app directory

## Quick Start

### Local Installation (Windows / Linux / macOS)
```bash
pip install -r requirements.txt
python main.py
```

### Optional: Run Tests
```bash
pytest
```

## How To Use

### Basic Editing Flow
1. Open Dek0nstruct
2. Import a video from the File menu
3. Create segments using timeline controls
4. Review or adjust output/audio settings
5. Export selected segments

### Project Files
- Save project: File -> Save Project
- Load project: File -> Load Project
- Project extension: `.vedproj`

## App Data Locations
- Main app data directory: `~/.dek0nstruct` (or `%APPDATA%/Dek0nstruct` on Windows config path)
- Jobs queue data: `~/.dek0nstruct/jobs`
- Export profiles: `~/.dek0nstruct/export_profiles`
- Logs and crash reports: `~/.dek0nstruct/logs`, `~/.dek0nstruct/crashes`

## Production Notes
- **Service startup hardening**: background services initialize on startup and cleanly stop on exit
- **Single startup path**: application entrypoint is consolidated to avoid conflicting boot flows
- **Persistent operational data**: config, jobs, profiles, logs, and crash artifacts are stored under the Dek0nstruct namespace
- **Graceful error handling**: uncaught exceptions are logged and surfaced with user-readable dialogs

### Optional Telemetry (Opt-In)
Telemetry and remote error reporting are disabled by default.

Enable only when needed:
```bash
export DEK0NSTRUCT_TELEMETRY_ENABLED=true
export DEK0NSTRUCT_ERROR_REPORTING_ENABLED=true
export DEK0NSTRUCT_TELEMETRY_URL=https://your-telemetry-endpoint
```

PowerShell:
```powershell
$env:DEK0NSTRUCT_TELEMETRY_ENABLED = "true"
$env:DEK0NSTRUCT_ERROR_REPORTING_ENABLED = "true"
$env:DEK0NSTRUCT_TELEMETRY_URL = "https://your-telemetry-endpoint"
```

## Running Tests

```bash
pytest
```

## License

See [LICENSE](LICENSE).

