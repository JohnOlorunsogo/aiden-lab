"""eNSP Console Logger - Passive packet capture using Scapy."""
import datetime
import logging
from pathlib import Path
from typing import Dict, Set, Optional

try:
    from scapy.all import AsyncSniffer, Raw, get_if_list  # type: ignore
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    AsyncSniffer = None
    Raw = None
    get_if_list = None

logger = logging.getLogger(__name__)

TELNET_CTRL_MIN = 240


class SessionLogger:
    """Manages log files for each eNSP console port with text cleaning."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.files: Dict[int, Path] = {}
        self.handles: Dict[int, object] = {}
        self.device_names: Dict[int, str] = {}
        self.input_buffers: Dict[int, str] = {}
        self.output_buffers: Dict[int, str] = {}
        # Track last logged lines for deduplication
        self.last_lines: Dict[int, str] = {}
        # Track consecutive duplicate prompts
        self.duplicate_prompt_count: Dict[int, int] = {}

    def _open(self, port: int):
        if port in self.handles:
            return
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            device_name = self.device_names.get(port, f"device_{port}")
            path = self.log_dir / f"{device_name}_{port}_{ts}.log"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.handles[port] = open(path, "a", encoding="utf-8")
            self.files[port] = path
            logger.info(f"Logging port {port} ({device_name}) -> {path.resolve()}")
        except Exception as exc:
            logger.error(f"Error creating log file for port {port}: {exc}")
            raise

    def write(self, port: int, direction: str, data: bytes):
        cleaned = bytes(b for b in data if b < TELNET_CTRL_MIN)
        if not cleaned:
            return
        try:
            text = cleaned.decode("utf-8", errors="replace")
        except Exception:
            text = cleaned.decode("latin-1", errors="replace")
        if not text:
            return

        buffer_name = "input_buffers" if direction == "→" else "output_buffers"
        buffers: Dict[int, str] = getattr(self, buffer_name)
        buffers[port] = buffers.get(port, "") + text

        while "\n" in buffers[port] or "\r" in buffers[port]:
            buf = buffers[port]
            pos_n = buf.find("\n")
            pos_r = buf.find("\r")
            if pos_n == -1:
                split_at = pos_r
            elif pos_r == -1:
                split_at = pos_n
            else:
                split_at = min(pos_n, pos_r)

            line = buf[: split_at + 1]
            buffers[port] = buf[split_at + 1 :]
            if line.strip():
                self._log_line(port, direction, line)

        if direction == "←" and buffers[port]:
            frag = buffers[port].strip()
            if frag.endswith((">", "]")) or (frag.startswith("<") and frag.endswith(">")):
                self._log_line(port, direction, frag)
                buffers[port] = ""

    def _log_line(self, port: int, direction: str, text: str):
        def is_prompt_line(s: str) -> bool:
            """Check if line is a router prompt."""
            s = s.strip()
            return (s.startswith('<') and s.endswith('>')) or \
                   (s.startswith('[') and s.endswith(']')) or \
                   s.endswith('#') or s.endswith('>')

        def should_skip_line(port: int, clean_line: str) -> bool:
            """Skip duplicate lines and excessive prompts."""
            if not clean_line or clean_line.isspace():
                return True
            
            last_line = self.last_lines.get(port, "")
            if clean_line == last_line:
                return True
            
            # Limit consecutive duplicate prompts
            if is_prompt_line(clean_line):
                if clean_line == last_line:
                    self.duplicate_prompt_count[port] = self.duplicate_prompt_count.get(port, 0) + 1
                    if self.duplicate_prompt_count[port] > 1:
                        return True
                else:
                    self.duplicate_prompt_count[port] = 0
            else:
                self.duplicate_prompt_count[port] = 0
            
            return False

        def clean_console_text(text: str, direction: str) -> str:
            """Clean eNSP console artifacts and character doubling."""
            import re
            
            if not text or not text.strip():
                return ""
            
            # Remove control characters and ANSI sequences
            cleaned = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)
            cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
            cleaned = cleaned.replace('\x07', '')
            cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
            cleaned = cleaned.strip()
            
            # Fix command input issues (user typed commands)
            if direction == "→":
                # Handle character doubling in commands like "hehello" -> "hello"
                if "hello" in cleaned.lower():
                    match = re.search(r'h[eh]*ello', cleaned.lower())
                    if match and len(match.group()) > 5:
                        cleaned = cleaned.replace(match.group(), "hello")
                
                # Fix other doubled commands
                command_patterns = {
                    r'd[di]*splay': 'display',
                    r's[sh]*ow': 'show', 
                    r'p[pi]*ng': 'ping',
                    r't[te]*st': 'test'
                }
                
                for pattern, replacement in command_patterns.items():
                    if re.search(pattern, cleaned.lower()):
                        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            
            # Fix router response issues
            elif direction == "←":
                # Handle corrupted error messages
                if 'ee' in cleaned and ('error' in cleaned.lower() or 'unrecognized' in cleaned.lower()):
                    if 'unrecognized command' in cleaned.lower():
                        cleaned = "Error: Unrecognized command found at '^' position."
                
                # Remove repetitive error text
                if '.or:' in cleaned or 'position.or:' in cleaned:
                    parts = cleaned.split('or:')
                    if len(parts) > 1:
                        first_part = parts[0].strip()
                        cleaned = first_part + "." if not first_part.endswith('.') else first_part
            
            # Remove duplicate consecutive words
            words = cleaned.split()
            if len(words) >= 2:
                filtered = []
                prev = None
                for word in words:
                    if word.lower() != prev:
                        filtered.append(word)
                        prev = word.lower()
                cleaned = ' '.join(filtered)
            
            return re.sub(r'\s+', ' ', cleaned).strip()

        # Process the log line
        cleaned_text = clean_console_text(text, direction)
        
        if should_skip_line(port, cleaned_text):
            return
        
        self.last_lines[port] = cleaned_text
        self._detect_device_name(port, direction, cleaned_text)
        self._open(port)

        # Write to log file
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        device_name = self.device_names.get(port, f"device_{port}")
        line = f"[{ts}] [{device_name}] {direction} '{cleaned_text}'\n"
        handle = self.handles[port]
        handle.write(line)
        handle.flush()

    def _detect_device_name(self, port: int, direction: str, text: str):
        """Extract device hostname from router prompts."""
        if direction != "←":
            return
            
        import re
        
        # Look for common router prompt patterns
        patterns = [
            r'<([^>\-\s]+(?:-[^>\s]+)?)>',     # <R1>, <Router-1>
            r'\[([^\]\-\s]+(?:-[^\]\s]+)?)\]', # [R1], [Router-1] 
            r'^([A-Za-z][A-Za-z0-9\-_]*)[#>]' # R1#, R1>
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.strip())
            if matches:
                hostname = matches[0].strip()
                # Skip common system words
                excluded = ['huawei', 'system', 'config', 'user', 'info', 
                           'warning', 'error', 'debug', 'display', 'show']
                
                if hostname and hostname.lower() not in excluded:
                    if (port not in self.device_names or 
                        len(hostname) > len(self.device_names[port])):
                        old_name = self.device_names.get(port, f"device_{port}")
                        self.device_names[port] = hostname
                        if old_name != hostname:
                            logger.info(f"Port {port} device name: {hostname}")
                    break

    def close(self):
        """Close all log files and clean up resources."""
        for handle in self.handles.values():
            try:
                handle.close()
            except Exception:
                pass
        self.handles.clear()
        self.files.clear()
        self.last_lines.clear()
        self.duplicate_prompt_count.clear()


class ENSPPacketSniffer:
    """Packet sniffer for eNSP console sessions."""
    
    def __init__(
        self,
        console_ports: Set[int],
        log_dir: Path,
        loopback_iface: str = "Npcap Loopback Adapter",
        auto_detect: bool = True
    ):
        if not SCAPY_AVAILABLE:
            raise ImportError("scapy is not installed. Install with: pip install scapy>=2.5.0")
        
        self.console_ports = console_ports
        self.log_dir = log_dir
        self.loopback_iface = loopback_iface
        self.auto_detect = auto_detect
        self.session_logger: Optional[SessionLogger] = None
        self.sniffer: Optional[AsyncSniffer] = None
        self._running = False
        
    def _build_bpf_filter(self) -> str:
        if self.auto_detect:
            if self.console_ports:
                min_port = min(self.console_ports)
                max_port = max(self.console_ports)
                return f"tcp and (portrange {min_port}-{max_port})"
            return "tcp and (portrange 2000-2010)"
        else:
            if not self.console_ports:
                return "tcp and (portrange 2000-2010)"
            parts = [f"port {p}" for p in sorted(self.console_ports)]
            return "tcp and (" + " or ".join(parts) + ")"
    
    def _resolve_iface(self, preferred: str) -> str:
        ifaces = get_if_list()
        if preferred in ifaces:
            return preferred
        for i in ifaces:
            if "loopback" in i.lower():
                return i
        raise ValueError(f"Interface '{preferred}' not found. Available: {', '.join(ifaces)}")
    
    def _on_packet(self, pkt):
        try:
            if not pkt.haslayer(Raw):
                return
            tcp = pkt.getlayer("TCP")
            if tcp is None:
                return
            sport = int(tcp.sport)
            dport = int(tcp.dport)

            port = None
            direction = None
            if dport in self.console_ports:
                port = dport
                direction = "→"
            elif sport in self.console_ports:
                port = sport
                direction = "←"
            if port is None:
                return

            payload = bytes(pkt[Raw].load)
            if self.session_logger:
                self.session_logger.write(port, direction, payload)
        except Exception as exc:
            logger.error(f"Error processing packet: {exc}")
    
    def start(self):
        if self._running:
            logger.warning("Packet sniffer already running")
            return
        
        if not self.console_ports and not self.auto_detect:
            logger.error("No console ports configured and auto-detect disabled")
            raise ValueError("No console ports configured and auto-detect disabled")
        
        try:
            iface = self._resolve_iface(self.loopback_iface)
            bpf_filter = self._build_bpf_filter()
            
            logger.info(f"Starting eNSP packet sniffer")
            logger.info(f"Interface: {iface}")
            logger.info(f"Ports: {sorted(self.console_ports) if self.console_ports else 'auto-detect'}")
            logger.info(f"BPF filter: {bpf_filter}")
            logger.info(f"Log directory: {self.log_dir.resolve()}")
            
            self.session_logger = SessionLogger(self.log_dir)
            
            self.sniffer = AsyncSniffer(
                iface=iface,
                filter=bpf_filter,
                prn=self._on_packet,
                store=False,
            )
            
            self.sniffer.start()
            self._running = True
            logger.info("Packet sniffer started successfully")
            
        except Exception as exc:
            logger.error(f"Failed to start packet sniffer: {exc}")
            self._running = False
            raise
    
    def stop(self):
        if not self._running:
            return
        
        logger.info("Stopping packet sniffer...")
        try:
            if self.sniffer:
                self.sniffer.stop()
                self.sniffer = None
        except Exception as exc:
            logger.error(f"Error stopping sniffer: {exc}")
        
        try:
            if self.session_logger:
                self.session_logger.close()
                self.session_logger = None
        except Exception as exc:
            logger.error(f"Error closing session logger: {exc}")
        
        self._running = False
        logger.info("Packet sniffer stopped")
    
    @property
    def is_running(self) -> bool:
        return self._running
