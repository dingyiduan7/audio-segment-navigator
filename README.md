# Audio Segment Navigator

A local-first web app that finds likely song boundaries in a long audio or video file and turns
them into a navigable track list. Select any detected track, or use Previous and Next to move
through the recording.

## What it does

- Accepts MP3, WAV, FLAC, M4A, AAC, OGG, Opus, MP4, MKV, WebM, MOV, and AVI files.
- Extracts analysis audio with FFmpeg without changing the original upload.
- Detects clear silence gaps and corroborated acoustic changes.
- Streams the original audio or video back to the browser.
- Keeps uploads in temporary local storage and removes stale jobs after six hours.
- Labels results `Track 1`, `Track 2`, and so on. It does not identify title or artist.

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- FFmpeg and FFprobe available on `PATH`

On Windows, Node.js and FFmpeg can be installed with:

```powershell
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
```

Open a new terminal after installation and verify:

```powershell
node --version
ffmpeg -version
ffprobe -version
```

## Run locally

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Its health endpoint is
`http://127.0.0.1:8000/api/health`.

### 2. Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` calls to the backend.

## Tests

```powershell
cd backend
python -m pytest

cd ..\frontend
npm install
npm test
npm run build
```

The backend tests generate their own tones and silence, so no copyrighted media fixture is
needed.

## Configuration

The backend supports these environment variables:

- `AUDIO_PARSER_TEMP_DIR`: upload and analysis workspace
- `AUDIO_PARSER_MAX_UPLOAD_MB`: upload limit, default `2048`
- `AUDIO_PARSER_JOB_TTL_SECONDS`: local-file retention, default `21600`
- `AUDIO_PARSER_ALLOWED_ORIGINS`: comma-separated frontend origins
- `FFMPEG_BINARY` and `FFPROBE_BINARY`: custom executable names or paths

## API

- `POST /api/jobs`: upload media as multipart field `file`
- `GET /api/jobs/{id}`: poll progress and retrieve segments
- `GET /api/jobs/{id}/media`: stream the original media
- `DELETE /api/jobs/{id}`: remove a job and its local files

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Detection behavior and limitations

The detector is intentionally conservative. It works best for complete songs placed one after
another with a brief quiet gap. Crossfaded playlists, DJ sets, live applause, speech between
songs, or consistently quiet music can produce missed or extra boundaries. A one-track result
means no transition met the confidence and minimum-duration thresholds.

Media never leaves the computer running the backend. Do not expose this development server to
the public internet without adding authentication, durable job storage, rate limiting, and a
production worker queue.
