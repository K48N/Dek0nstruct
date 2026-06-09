# Dek0nstruct

A production-ready desktop video editing and segmentation suite with AI-assisted scene analysis, audio enhancement, export queueing, autosave, and project recovery.

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

## Troubleshooting

### App fails to start
1. Verify Python version and dependencies are installed
2. Ensure FFmpeg is available on PATH
3. Re-run and check generated logs in the app data logs directory

### Export issues
1. Confirm source media path still exists
2. Check output directory write permissions
3. Retry with fewer concurrent jobs

## Security & Reliability
- **Local-first processing**: no mandatory cloud dependency for core editing flow
- **Crash and error capture** for diagnostics
- **Autosave and recovery support** for safer long editing sessions
- **Configurable service behavior** via structured config storage

## License

See [LICENSE](LICENSE).

