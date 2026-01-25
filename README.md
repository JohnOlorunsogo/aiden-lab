# AIDEN Labs - Log Monitoring & AI Error Analysis System

A real-time log monitoring system for Huawei ENSP devices that detects errors and provides AI-powered solutions with enhanced packet capture capabilities.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure paths and API key
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
- **Processing Layer**: Analyzes errors with Gemini AI and intelligent text cleaning
- **Output Layer**: Real-time web dashboard

## Configuration

Edit `.env` to configure:
- `LOG_WATCH_DIR`: Directory containing device log files  
- `ENSP_SNIFFER_LOG_DIR`: Directory for eNSP packet capture logs
- `GEMINI_API_KEY`: Your Google Gemini API key
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

## License

MIT
