# AIDEN Labs - Log Monitoring & AI Error Analysis System

A real-time log monitoring system for Huawei ENSP devices that detects errors and provides AI-powered solutions.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your GEMINI_API_KEY
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
- **Detection Layer**: Scans for Huawei VRP error patterns
- **Processing Layer**: Analyzes errors with Gemini AI
- **Output Layer**: Real-time web dashboard

## Configuration

Edit `.env` to configure:
- `LOG_WATCH_DIR`: Directory containing device log files
- `GEMINI_API_KEY`: Your Google Gemini API key
- `CONTEXT_LINES`: Lines of context for AI analysis (default: 30)

## License

MIT
