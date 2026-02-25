"""Telnet proxy logger — captures full eNSP CLI traffic (commands AND responses).

The proxy listens on offset ports (e.g., 3000-3004) and forwards connections
to eNSP console ports (e.g., 2000-2004), logging all traffic bidirectionally.
Users connect their Telnet client to the proxy ports instead of directly to eNSP.
"""
import asyncio
import datetime
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

OUTGOING = "→"
INCOMING = "←"

# ANSI escape sequences and control characters for cleaning log display
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


class ProxySessionLogger:
    """Manages log files for proxy sessions with clean text output."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.handles: Dict[int, object] = {}
        self.files: Dict[int, Path] = {}
        self.device_names: Dict[int, str] = {}
        self.buffers: Dict[Tuple[int, str], str] = {}

    def _open(self, port: int):
        """Open or return existing log file handle for a port."""
        if port in self.handles:
            return
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            device_name = self.device_names.get(port, f"device_{port}")
            path = self.log_dir / f"{device_name}_{port}_{ts}.log"
            self.handles[port] = open(path, "a", encoding="utf-8")
            self.files[port] = path
            logger.info(f"Proxy logging port {port} ({device_name}) -> {path.resolve()}")
        except Exception as exc:
            logger.error(f"Error creating proxy log file for port {port}: {exc}")
            raise

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for logging — strip ANSI escapes and control chars."""
        cleaned = ANSI_ESCAPE_RE.sub("", text)
        cleaned = cleaned.replace("\x07", "")  # bell
        cleaned = CONTROL_CHARS_RE.sub("", cleaned)
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        return cleaned

    def _detect_device_name(self, port: int, text: str):
        """Extract device hostname from router prompts in response text."""
        patterns = [
            r"<([^>\s]+(?:-[^>\s]+)?)>",     # <R1>, <Router-1>
            r"\[([^\]\s]+(?:-[^\]\s]+)?)\]",  # [R1], [Router-1]
            r"^([A-Za-z][A-Za-z0-9\-_]*)[#>]",  # R1#, R1>
        ]
        excluded = {"huawei", "system", "config", "user", "info", "warning", "error", "debug"}

        for pattern in patterns:
            matches = re.findall(pattern, text.strip())
            if not matches:
                continue
            hostname = matches[0].strip()
            if not hostname or hostname.lower() in excluded:
                continue
            if port not in self.device_names or hostname != self.device_names[port]:
                old = self.device_names.get(port, f"device_{port}")
                self.device_names[port] = hostname
                if old != hostname:
                    logger.info(f"Proxy port {port} device name: {hostname}")
            break

    def log_data(self, port: int, direction: str, data: bytes):
        """Log raw data from a proxy session.

        Buffers partial lines and flushes complete lines to the log file.
        """
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            return

        if not text:
            return

        key = (port, direction)
        self.buffers[key] = self.buffers.get(key, "") + text

        # Flush complete lines
        while "\n" in self.buffers[key] or "\r" in self.buffers[key]:
            buf = self.buffers[key]
            # Find earliest line ending
            pos_n = buf.find("\n")
            pos_r = buf.find("\r")
            if pos_n == -1:
                split_at = pos_r
            elif pos_r == -1:
                split_at = pos_n
            else:
                split_at = min(pos_n, pos_r)

            line_raw = buf[: split_at + 1]
            self.buffers[key] = buf[split_at + 1 :]

            cleaned = self._clean_text(line_raw).strip()
            if not cleaned:
                continue

            # Detect device name from incoming traffic
            if direction == INCOMING:
                self._detect_device_name(port, cleaned)

            self._write_line(port, direction, cleaned)

    def _write_line(self, port: int, direction: str, text: str):
        """Write a cleaned line to the log file."""
        self._open(port)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        device_name = self.device_names.get(port, f"device_{port}")
        line = f"[{ts}] [{device_name}] {direction} '{text}'\n"
        handle = self.handles[port]
        handle.write(line)
        handle.flush()

    def flush_all(self):
        """Flush any remaining buffered content."""
        for key, buf in list(self.buffers.items()):
            port, direction = key
            cleaned = self._clean_text(buf).strip()
            if cleaned:
                self._write_line(port, direction, cleaned)
            self.buffers[key] = ""

    def close(self):
        """Close all log files."""
        self.flush_all()
        for handle in self.handles.values():
            try:
                handle.close()
            except Exception:
                pass
        self.handles.clear()
        self.files.clear()
        self.buffers.clear()


class TelnetProxySession:
    """Manages a single proxied Telnet session between a client and eNSP."""

    def __init__(
        self,
        console_port: int,
        target_host: str,
        session_logger: ProxySessionLogger,
    ):
        self.console_port = console_port
        self.target_host = target_host
        self.session_logger = session_logger
        self._client_reader: Optional[asyncio.StreamReader] = None
        self._client_writer: Optional[asyncio.StreamWriter] = None
        self._target_reader: Optional[asyncio.StreamReader] = None
        self._target_writer: Optional[asyncio.StreamWriter] = None

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection by proxying to eNSP."""
        client_addr = writer.get_extra_info("peername")
        logger.info(f"Proxy: client {client_addr} -> eNSP port {self.console_port}")

        self._client_reader = reader
        self._client_writer = writer

        try:
            # Connect to eNSP
            self._target_reader, self._target_writer = await asyncio.open_connection(
                self.target_host, self.console_port
            )
            logger.info(f"Proxy: connected to {self.target_host}:{self.console_port}")
        except Exception as exc:
            logger.error(f"Proxy: failed to connect to eNSP {self.target_host}:{self.console_port}: {exc}")
            writer.close()
            return

        # Relay bidirectionally
        try:
            await asyncio.gather(
                self._relay(self._client_reader, self._target_writer, OUTGOING),
                self._relay(self._target_reader, self._client_writer, INCOMING),
            )
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug(f"Proxy session ended for port {self.console_port}: {exc}")
        finally:
            self._close()
            logger.info(f"Proxy: session closed for port {self.console_port}")

    async def _relay(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        direction: str,
    ):
        """Relay data from reader to writer, logging everything."""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break

                # Log the data
                self.session_logger.log_data(self.console_port, direction, data)

                # Forward to the other side
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass

    def _close(self):
        """Close both sides of the proxy connection."""
        for w in (self._client_writer, self._target_writer):
            if w:
                try:
                    w.close()
                except Exception:
                    pass


class TelnetProxy:
    """Async Telnet proxy server that captures full eNSP CLI traffic.

    Listens on proxy ports (console port + offset) and forwards connections
    to the actual eNSP console ports, logging all traffic.
    """

    def __init__(
        self,
        console_ports: Set[int],
        target_host: str,
        port_offset: int,
        log_dir: Path,
    ):
        self.console_ports = console_ports
        self.target_host = target_host
        self.port_offset = port_offset
        self.log_dir = log_dir
        self.session_logger = ProxySessionLogger(log_dir)
        self._servers: Dict[int, asyncio.AbstractServer] = {}
        self._running = False

    async def start(self):
        """Start proxy servers for all configured console ports."""
        if self._running:
            logger.warning("Telnet proxy already running")
            return

        logger.info("Starting Telnet proxy servers...")
        logger.info(f"Target host: {self.target_host}")
        logger.info(f"Port offset: {self.port_offset}")
        logger.info(f"Log directory: {self.log_dir.resolve()}")

        for console_port in sorted(self.console_ports):
            proxy_port = console_port + self.port_offset
            try:
                session = TelnetProxySession(
                    console_port=console_port,
                    target_host=self.target_host,
                    session_logger=self.session_logger,
                )
                server = await asyncio.start_server(
                    session.handle,
                    host="0.0.0.0",
                    port=proxy_port,
                )
                self._servers[console_port] = server
                logger.info(f"  Proxy: port {proxy_port} -> eNSP port {console_port}")
            except OSError as exc:
                logger.error(f"  Failed to bind proxy port {proxy_port}: {exc}")

        if self._servers:
            self._running = True
            port_list = ", ".join(
                f"{cp + self.port_offset}->{cp}" for cp in sorted(self._servers)
            )
            logger.info(f"Telnet proxy started: {port_list}")
        else:
            logger.error("Telnet proxy: no ports could be bound")

    async def stop(self):
        """Stop all proxy servers and close log files."""
        if not self._running:
            return

        logger.info("Stopping Telnet proxy...")
        for console_port, server in self._servers.items():
            try:
                server.close()
                await server.wait_closed()
            except Exception as exc:
                logger.error(f"Error stopping proxy for port {console_port}: {exc}")

        self._servers.clear()
        self.session_logger.close()
        self._running = False
        logger.info("Telnet proxy stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def proxy_ports(self) -> Dict[int, int]:
        """Return mapping of proxy_port -> console_port for active servers."""
        return {cp + self.port_offset: cp for cp in self._servers}
