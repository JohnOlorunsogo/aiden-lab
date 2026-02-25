# AIDEN Labs - Startup Scripts

This folder contains cross-platform scripts to start AIDEN Labs backend and frontend services.

## Scripts Overview

| Script | Platform | Purpose |
|--------|----------|---------|
| `start.sh` | Linux/macOS | Start both services in one terminal |
| `start.bat` | Windows | Start both services in separate windows |
| `start_admin.bat` | Windows | Start with administrator privileges |
| `install_startup.bat` | Windows | Install auto-start at Windows login |
| `uninstall_startup.bat` | Windows | Remove auto-start from Windows |

## Usage

### Linux / macOS

```bash
# Make the script executable (first time only)
chmod +x scripts/start.sh

# Run the script
./scripts/start.sh
```

Press `Ctrl+C` to stop both services.

### Windows

**Normal Start:**
- Double-click `start.bat` or run from Command Prompt

**Start with Admin Privileges:**
- Double-click `start_admin.bat`
- Click "Yes" on the UAC prompt

**Auto-Start at Login (with Admin):**
1. Double-click `install_startup.bat`
2. Click "Yes" on the UAC prompt
3. AIDEN Labs will now start automatically when you log in

**Remove Auto-Start:**
1. Double-click `uninstall_startup.bat`
2. Click "Yes" on the UAC prompt

## Service URLs

Once running, access the services at:

- **Backend API:** http://localhost:8000
- **Frontend UI:** http://localhost:5173

## Requirements

- **Backend:** Python 3.x with dependencies installed
- **Frontend:** Node.js and npm with dependencies installed

## Notes

- The scripts automatically detect and activate the Python virtual environment if present
- Frontend will auto-install npm dependencies if `node_modules` is missing
- On Windows, each service runs in its own terminal window
- On Linux/macOS, both services run in the same terminal with combined output
