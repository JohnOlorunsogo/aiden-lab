# AIDEN Labs - Log Monitoring & AI Error Analysis System

A real-time log monitoring system for Huawei ENSP devices that detects errors and provides AI-powered solutions with enhanced packet capture capabilities.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure paths and LLM server URL
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Architecture

- **Monitoring Layer**: Watches log files for changes (watchdog)
- **Capture Layer**: Live eNSP console packet monitoring (Scapy)
- **Detection Layer**: Scans for Huawei VRP error patterns
- **Processing Layer**: Analyzes errors with a self-hosted LLM (llama.cpp) and intelligent text cleaning
- **Output Layer**: Real-time web dashboard

## Configuration

Edit `.env` to configure:
- `LOG_WATCH_DIR`: Directory containing device log files  
- `ENSP_SNIFFER_LOG_DIR`: Directory for eNSP packet capture logs
- `LLM_BASE_URL`: Base URL of your self-hosted LLM server (default: `http://159.138.135.202:8000`)
- `LLM_MODEL`: Model name for the LLM (default: `gemma-3-1b-it-GGUF`)
- `CONTEXT_LINES`: Lines of context for AI analysis (default: 30)
- `ENSP_MODE`: Console monitoring mode (standard, extended, lab, custom)
- `ENSP_CONSOLE_PORT_RANGE`: Port range for device detection (default: 2000-2004)
- `ENSP_AUTO_DETECT`: Enable automatic device detection (default: true)

## Enhanced eNSP Logger

New packet capture capabilities added:
- **Live Console Monitoring**: Direct packet capture from eNSP console traffic
- **Intelligent Text Processing**: Automatic character doubling repair (hehello → hello)
- **Multi-device Support**: Monitor multiple devices across console port ranges
- **Enhanced Error Detection**: Improved pattern matching for Huawei VRP errors
- **Windows Compatibility**: Optimized polling for reliable Windows operation

## Scripts

Cross-platform startup scripts are provided in the `scripts/` directory.

| Script | Platform | Purpose |
|--------|----------|---------|
| `start.sh` | Linux/macOS | Start both services in one terminal |
| `start.bat` | Windows | Start both services in separate windows |
| `start_admin.bat` | Windows | Start with administrator privileges |
| `install_startup.bat` | Windows | Install auto-start at Windows login |
| `uninstall_startup.bat` | Windows | Remove auto-start from Windows |

### Linux / macOS

```bash
chmod +x scripts/start.sh   # first time only
./scripts/start.sh
```

Press `Ctrl+C` to stop both services.

### Windows

- **Normal Start:** Double-click `start.bat`
- **Admin Start:** Double-click `start_admin.bat` → click "Yes" on UAC
- **Auto-Start at Login:** Double-click `install_startup.bat` → click "Yes" on UAC
- **Remove Auto-Start:** Double-click `uninstall_startup.bat` → click "Yes" on UAC

### Service URLs

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Frontend UI | http://localhost:5173 |

> **Note:** Scripts auto-detect Python virtual environments and install npm dependencies if `node_modules` is missing.

## License

MIT
