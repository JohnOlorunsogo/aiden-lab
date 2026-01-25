"""Service wrapper for ENSP packet sniffer with lifecycle management."""
import logging
import threading
import platform
from pathlib import Path
from typing import Set, Optional

from app.config import settings
from app.services.ensp_logger import ENSPPacketSniffer, SCAPY_AVAILABLE

logger = logging.getLogger(__name__)


def check_admin_privileges() -> bool:
    if platform.system() == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return True


class ENSPLoggerService:
    """Service to manage ENSP packet sniffer lifecycle."""
    
    def __init__(self):
        self.sniffer: Optional[ENSPPacketSniffer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._enabled = True
        
    def _parse_port_range(self, port_range: str) -> Set[int]:
        ports = set()
        for part in port_range.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                ports.update(range(int(start), int(end) + 1))
            elif part.isdigit():
                ports.add(int(part))
        return ports
    
    def _get_console_ports(self) -> Set[int]:
        MODE_CONFIGS = {
            "standard": {"port_range": "2000-2004", "auto_detect": True},
            "extended": {"port_range": "2000-2010", "auto_detect": True},
            "lab": {"port_range": "2000-2020", "auto_detect": True},
            "custom": {"port_range": "2000-2004", "auto_detect": False},
        }
        
        port_range = settings.ensp_console_port_range
        if settings.ensp_mode in MODE_CONFIGS:
            mode_config = MODE_CONFIGS[settings.ensp_mode]
            if port_range == "2000-2004" and settings.ensp_mode != "standard":
                port_range = mode_config["port_range"]
        
        return self._parse_port_range(port_range)
    
    def _get_auto_detect(self) -> bool:
        MODE_CONFIGS = {
            "standard": {"auto_detect": True},
            "extended": {"auto_detect": True},
            "lab": {"auto_detect": True},
            "custom": {"auto_detect": False},
        }
        
        auto_detect = settings.ensp_auto_detect
        if settings.ensp_mode in MODE_CONFIGS:
            mode_config = MODE_CONFIGS[settings.ensp_mode]
            if settings.ensp_mode == "custom" and auto_detect == True:
                auto_detect = mode_config["auto_detect"]
        
        return auto_detect
    
    def _get_log_directory(self) -> Path:
        if settings.ensp_sniffer_log_dir:
            log_dir = Path(settings.ensp_sniffer_log_dir)
            if not log_dir.is_absolute():
                backend_root = Path(__file__).parent.parent.parent
                log_dir = backend_root / log_dir
        else:
            log_dir = settings.log_watch_dir
        
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def start(self) -> bool:
        if self._running:
            logger.warning("ENSP logger service already running")
            return True
        
        if not self._enabled:
            logger.info("ENSP logger service is disabled")
            return False
        
        if not SCAPY_AVAILABLE:
            logger.warning("Scapy not available - ENSP logger cannot start. Install with: pip install scapy>=2.5.0")
            return False
        
        if not check_admin_privileges():
            logger.warning(
                "Administrator privileges not detected. "
                "Packet capture may fail. "
                "On Windows, run as Administrator for full functionality."
            )
        
        try:
            console_ports = self._get_console_ports()
            log_dir = self._get_log_directory()
            
            logger.info(f"Initializing ENSP logger service")
            logger.info(f"Mode: {settings.ensp_mode}")
            logger.info(f"Console ports: {sorted(console_ports) if console_ports else 'auto-detect'}")
            logger.info(f"Log directory: {log_dir.resolve()}")
            
            self.sniffer = ENSPPacketSniffer(
                console_ports=console_ports,
                log_dir=log_dir,
                loopback_iface=settings.ensp_loopback_iface,
                auto_detect=self._get_auto_detect()
            )
            
            # Start sniffer in current thread (it uses AsyncSniffer which is async)
            self.sniffer.start()
            self._running = True
            logger.info("ENSP logger service started successfully")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to start ENSP logger service: {exc}", exc_info=True)
            self._running = False
            return False
    
    def stop(self):
        if not self._running:
            return
        
        logger.info("Stopping ENSP logger service...")
        try:
            if self.sniffer:
                self.sniffer.stop()
                self.sniffer = None
        except Exception as exc:
            logger.error(f"Error stopping ENSP logger: {exc}", exc_info=True)
        
        self._running = False
        logger.info("ENSP logger service stopped")
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        if self._running:
            self.stop()
        self._enabled = False
    
    def cleanup_logs(self):
        try:
            log_dir = self._get_log_directory()
            if not log_dir.exists():
                logger.debug(f"Log directory does not exist: {log_dir}")
                return
            
            deleted_count = 0
            for log_file in log_dir.glob("*.log"):
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as exc:
                    logger.warning(f"Failed to delete log file {log_file}: {exc}")
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} log file(s) from {log_dir}")
            else:
                logger.debug(f"No log files found to delete in {log_dir}")
                
        except Exception as exc:
            logger.error(f"Error cleaning up log files: {exc}", exc_info=True)
    
    @property
    def is_running(self) -> bool:
        return self._running and self.sniffer is not None and self.sniffer.is_running
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled


ensp_logger_service = ENSPLoggerService()
