# Dek0nstruct

> A frame-accurate desktop video segmentation tool for clipping, classifying, and exporting at scale with a VLC-powered preview and FFmpeg backend.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

Dek0nstruct is a native desktop application for fast, precise video segment extraction. It integrates VLC for smooth playback, FFmpeg for lossless processing, and a non-blocking export queue, keeping the interface responsive while jobs compile in the background. AI-assisted scene detection and an audio enhancement pipeline reduce manual scrubbing time significantly.

---

## Features

- **Frame-accurate segmentation**: set In/Out points with keyboard shortcuts for surgical clip extraction
- **VLC-powered preview**: reliable synchronized video and audio playback embedded in the app
- **Non-blocking export queue**: segments compile in the background without freezing the UI
- **AI scene detection**: automatically splits footage at scene boundaries (`Ctrl+D`)
- **Audio pipeline**: voice clarity, ducking, and loudness normalization controls
- **GPU acceleration**: optional NVENC/QSV/AMF encoding for supported hardware
- **Autosave & crash recovery**: project state persisted continuously; recovery dialog on restart
- **Batch processing**: manage and export multiple segments in a single run (`Ctrl+B`)

---

## Tech Stack

| Component | Technology |
|---|---|
| UI framework | PyQt5 |
| Media playback | python-vlc (requires VLC installed) |
| Video processing | FFmpeg (system PATH or local install) |
| Thumbnail generation | OpenCV, Pillow |
| Testing | pytest, pytest-qt |

---

## Prerequisites

| Dependency | Requirement |
|---|---|
| Python | 3.10+ |
| FFmpeg | On system `PATH` or at `%LOCALAPPDATA%\Programs\ffmpeg\current\bin\` |
| VLC | Installed to default system location |

---

## Getting Started

```bash
git clone <your-repo-url>
cd dek0nstruct
```

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `← →` | Seek ±1 second |
| `I` | Set In point |
| `O` | Set Out point |
| `Ctrl+Z / Ctrl+Y` | Undo / Redo |
| `Ctrl+S` | Save project |
| `Ctrl+Shift+O` | Load project |
| `Ctrl+E` | Export segment |
| `Ctrl+B` | Batch processing |
| `Ctrl+D` | Auto-detect scenes |

---

## Application Data

| Path | Contents |
|---|---|
| `~/.dek0nstruct/jobs` | Background export queue |
| `~/.dek0nstruct/export_profiles` | Custom export presets |
| `~/.dek0nstruct/logs` | Application logs |
| `~/.dek0nstruct/crashes` | Crash reports |

> On Windows, the root is `%APPDATA%\Dek0nstruct`.

---

## Development

```bash
pytest
pytest --cov=. --cov-report=term-missing
```

To enable verbose debug logging before launching:

```powershell
$env:DEK0NSTRUCT_DEBUG = "true"
python main.py
```

---

## Known Limitations

- Requires local FFmpeg and VLC installations; the app cannot locate them automatically if not in the expected paths.
- GPU acceleration depends entirely on host hardware and driver support.
- Moving or renaming source video files after project creation will break export references.

---

## License

MIT
