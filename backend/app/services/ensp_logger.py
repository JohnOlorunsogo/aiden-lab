"""eNSP Console Logger - Passive packet capture using Scapy."""
import datetime
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

try:
    from scapy.all import AsyncSniffer, Raw, get_if_list  # type: ignore
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    AsyncSniffer = None
    Raw = None
    get_if_list = None

logger = logging.getLogger(__name__)

OUTGOING = "→"
INCOMING = "←"

TELNET_IAC = 255
TELNET_SE = 240
TELNET_SB = 250
TELNET_WILL = 251
TELNET_WONT = 252
TELNET_DO = 253
TELNET_DONT = 254

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

# If capture drops packets, avoid getting stuck waiting forever.
MAX_GAP_BYTES = 8192
GAP_TIMEOUT_SEC = 1.0


@dataclass
class TelnetDecodeState:
    """Tracks incremental Telnet parsing state across packet boundaries."""

    pending_iac: bool = False
    pending_option_for: Optional[int] = None
    in_subnegotiation: bool = False
    subnegotiation_iac: bool = False


@dataclass
class TcpStreamState:
    """Maintains stream-level TCP reassembly state for one direction."""

    next_seq: Optional[int] = None
    pending: Dict[int, bytes] = field(default_factory=dict)
    last_seen: float = field(default_factory=datetime.datetime.now().timestamp)
    gap_since: Optional[float] = None


class SessionLogger:
    """Manages log files for each eNSP console port with stream-safe text cleaning."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.files: Dict[int, Path] = {}
        self.handles: Dict[int, object] = {}
        self.device_names: Dict[int, str] = {}
        self.input_buffers: Dict[int, str] = {}
        self.output_buffers: Dict[int, str] = {}
        self.last_lines: Dict[Tuple[int, str], str] = {}
        self.duplicate_prompt_count: Dict[Tuple[int, str], int] = {}
        self.telnet_states: Dict[Tuple[int, str], TelnetDecodeState] = {}
        self.last_outgoing: Dict[int, Tuple[str, float]] = {}

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

    def _strip_telnet_controls(self, key: Tuple[int, str], data: bytes) -> bytes:
        """Strip Telnet IAC control sequences from raw data.
        
        Uses a stateless per-packet approach — processes each packet
        independently to avoid eating data bytes when IAC state carries
        across packet boundaries.
        """
        out = bytearray()
        i = 0
        n = len(data)

        while i < n:
            b = data[i]

            if b == TELNET_IAC and i + 1 < n:
                cmd = data[i + 1]

                if cmd == TELNET_IAC:
                    # Escaped 255 — emit one literal 255
                    out.append(TELNET_IAC)
                    i += 2
                    continue

                if cmd in (TELNET_WILL, TELNET_WONT, TELNET_DO, TELNET_DONT):
                    # 3-byte command: IAC CMD OPTION
                    i += 3
                    continue

                if cmd == TELNET_SB:
                    # Subnegotiation: IAC SB ... IAC SE
                    j = i + 2
                    while j < n - 1:
                        if data[j] == TELNET_IAC and data[j + 1] == TELNET_SE:
                            j += 2
                            break
                        j += 1
                    else:
                        # Subneg not terminated in this packet — skip to end
                        j = n
                    i = j
                    continue

                # Other 2-byte IAC command (e.g. IAC NOP, IAC GA)
                i += 2
                continue

            if b == TELNET_IAC and i + 1 == n:
                # Lone IAC at end of packet — discard (don't carry state)
                i += 1
                continue

            out.append(b)
            i += 1

        return bytes(out)

    @staticmethod
    def _apply_backspaces(text: str) -> str:
        """Apply terminal backspace/delete semantics to a text fragment."""
        out = []
        for ch in text:
            if ch in ("\b", "\x7f"):
                if out and out[-1] not in ("\n", "\r"):
                    out.pop()
                continue
            if ch == "\x00":
                continue
            out.append(ch)
        return "".join(out)

    @staticmethod
    def _is_prompt_line(s: str) -> bool:
        s = s.strip()
        return (
            (s.startswith("<") and s.endswith(">"))
            or (s.startswith("[") and s.endswith("]"))
            or s.endswith("#")
            or s.endswith(">")
        )

    @staticmethod
    def _clean_console_text(text: str) -> str:
        """Normalize one logical console line without command-specific rewriting."""
        cleaned = ANSI_ESCAPE_RE.sub("", text)
        cleaned = cleaned.replace("\x07", "")
        cleaned = CONTROL_CHARS_RE.sub("", cleaned)
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = cleaned.strip()
        return cleaned

    @staticmethod
    def _normalize_echo(text: str) -> str:
        """Normalize potential echo lines to compare with recent outgoing commands."""
        if not text:
            return ""

        if len(text) >= 2 and len(text) % 2 == 0:
            is_pair_doubled = True
            out = []
            for i in range(0, len(text), 2):
                if text[i] != text[i + 1]:
                    is_pair_doubled = False
                    break
                out.append(text[i])
            if is_pair_doubled:
                text = "".join(out)

        collapsed = []
        prev = None
        for ch in text:
            if ch == prev:
                continue
            collapsed.append(ch)
            prev = ch
        return "".join(collapsed)

    def write(self, port: int, direction: str, data: bytes):
        # Log raw bytes before ANY processing
        logger.info(f"[RAW] port={port} dir={direction} bytes={data!r}")

        key = (port, direction)
        payload = self._strip_telnet_controls(key, data)
        if not payload:
            return

        text = payload.decode("utf-8", errors="replace")
        if not text:
            return

        logger.info(f"[DECODED] port={port} dir={direction} text={text!r}")

        text = self._apply_backspaces(text)
        if not text:
            return

        buffer_name = "input_buffers" if direction == OUTGOING else "output_buffers"
        buffers: Dict[int, str] = getattr(self, buffer_name)
        buffers[port] = buffers.get(port, "") + text

        # Normalize line endings: \r\n → \n, then strip any remaining bare \r.
        # VRP uses \r\n for line endings and bare \r for cursor return (to
        # overwrite the caret indicator). For logging we just want the final
        # visible text, so stripping \r is the safest approach — it avoids
        # data loss when \r\n is split across TCP packets.
        buffers[port] = buffers[port].replace("\r\n", "\n").replace("\r", "")

        # Split on \n to extract complete lines
        while "\n" in buffers[port]:
            pos = buffers[port].find("\n")
            line = buffers[port][:pos]
            buffers[port] = buffers[port][pos + 1:]
            if line.strip():
                self._log_line(port, direction, line)

        if direction == INCOMING and buffers[port]:
            frag = buffers[port].strip()
            if self._is_prompt_line(frag):
                self._log_line(port, direction, frag)
                buffers[port] = ""

    def _log_line(self, port: int, direction: str, text: str):
        cleaned_text = self._clean_console_text(text)
        if not cleaned_text or cleaned_text.isspace():
            return

        key = (port, direction)
        last_line = self.last_lines.get(key, "")

        # Suppress incoming echo lines that are exact matches of the last outgoing command.
        # Using exact match only — the old _normalize_echo collapsed characters and
        # could incorrectly suppress legitimate response lines.
        if direction == INCOMING and len(cleaned_text) <= 64:
            last_out = self.last_outgoing.get(port)
            if last_out:
                last_cmd, ts = last_out
                if (datetime.datetime.now().timestamp() - ts) <= 2.0:
                    if cleaned_text.strip() == last_cmd.strip():
                        return

        # For OUTGOING (commands), suppress exact consecutive duplicates.
        # For INCOMING (responses), allow everything through — responses may
        # legitimately repeat (e.g. repeated status lines, table separators).
        if direction == OUTGOING and cleaned_text == last_line:
            return

        # For both directions, deduplicate consecutive identical prompts.
        if self._is_prompt_line(cleaned_text) and cleaned_text == last_line:
            self.duplicate_prompt_count[key] = self.duplicate_prompt_count.get(key, 0) + 1
            if self.duplicate_prompt_count[key] > 1:
                return
        else:
            self.duplicate_prompt_count[key] = 0

        self.last_lines[key] = cleaned_text
        self._detect_device_name(port, direction, cleaned_text)
        self._open(port)

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        device_name = self.device_names.get(port, f"device_{port}")
        line = f"[{ts}] [{device_name}] {direction} '{cleaned_text}'\n"
        handle = self.handles[port]
        handle.write(line)
        handle.flush()

        if direction == OUTGOING:
            self.last_outgoing[port] = (cleaned_text, datetime.datetime.now().timestamp())

    def _detect_device_name(self, port: int, direction: str, text: str):
        """Extract device hostname from router prompts."""
        if direction != INCOMING:
            return

        patterns = [
            r"<([^>\-\s]+(?:-[^>\s]+)?)>",      # <R1>, <Router-1>
            r"\[([^\]\-\s]+(?:-[^\]\s]+)?)\]",  # [R1], [Router-1]
            r"^([A-Za-z][A-Za-z0-9\-_]*)[#>]",  # R1#, R1>
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.strip())
            if not matches:
                continue

            hostname = matches[0].strip()
            excluded = [
                "system",
                "config",
                "user",
                "info",
                "warning",
                "error",
                "debug",
                "display",
                "show",
            ]
            if not hostname or hostname.lower() in excluded:
                continue

            if port not in self.device_names or len(hostname) > len(self.device_names[port]):
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
        self.telnet_states.clear()
        self.last_outgoing.clear()


class ENSPPacketSniffer:
    """Packet sniffer for eNSP console sessions with TCP stream reassembly."""

    def __init__(
        self,
        console_ports: Set[int],
        log_dir: Path,
        loopback_iface: str = "Npcap Loopback Adapter",
        auto_detect: bool = True,
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
        # Simple per-direction seq tracking for loopback dedup
        # Key: (port, direction), Value: highest seq end seen
        self._seq_tracker: Dict[Tuple[int, str], int] = {}

    def _build_bpf_filter(self) -> str:
        if self.auto_detect:
            if self.console_ports:
                min_port = min(self.console_ports)
                max_port = max(self.console_ports)
                return f"tcp and (portrange {min_port}-{max_port})"
            return "tcp and (portrange 2000-2010)"

        if not self.console_ports:
            return "tcp and (portrange 2000-2010)"
        parts = [f"port {p}" for p in sorted(self.console_ports)]
        return "tcp and (" + " or ".join(parts) + ")"

    def _resolve_iface(self, preferred: str) -> str:
        ifaces = get_if_list()
        if preferred in ifaces:
            return preferred
        for iface in ifaces:
            if "loopback" in iface.lower():
                return iface
        raise ValueError(f"Interface '{preferred}' not found. Available: {', '.join(ifaces)}")

    def _consume_pending(self, state: TcpStreamState) -> bytes:
        emitted = bytearray()
        if state.next_seq is None:
            return bytes(emitted)

        while state.pending:
            best_seq = None
            best_payload = b""
            for seq, payload in state.pending.items():
                end_seq = seq + len(payload)
                if seq <= state.next_seq < end_seq:
                    if best_seq is None or seq < best_seq:
                        best_seq = seq
                        best_payload = payload

            if best_seq is None:
                break

            state.pending.pop(best_seq)
            offset = state.next_seq - best_seq
            tail = best_payload[offset:]
            if not tail:
                continue

            emitted.extend(tail)
            state.next_seq += len(tail)

        return bytes(emitted)

    def _reassemble_payload(self, stream_key: Tuple[int, int, int, str], seq: int, payload: bytes) -> bytes:
        """
        Return only new contiguous bytes for this stream direction.

        Handles retransmits/overlap and short out-of-order windows.
        """
        if not payload:
            return b""

        state = self._seq_tracker.setdefault(stream_key, TcpStreamState())
        state.last_seen = datetime.datetime.now().timestamp()

        if state.next_seq is None:
            state.next_seq = seq

        end_seq = seq + len(payload)
        if state.next_seq is not None and end_seq <= state.next_seq:
            return b""

        if state.next_seq is not None and seq < state.next_seq:
            payload = payload[state.next_seq - seq :]
            seq = state.next_seq
            if not payload:
                return b""

        if state.next_seq is not None and seq > state.next_seq:
            # If we have a large/long gap, resync to avoid stalling.
            if state.gap_since is None:
                state.gap_since = state.last_seen
            gap_bytes = seq - state.next_seq
            gap_age = state.last_seen - (state.gap_since or state.last_seen)
            if gap_bytes >= MAX_GAP_BYTES or gap_age >= GAP_TIMEOUT_SEC:
                state.next_seq = seq
                state.pending.clear()
                state.gap_since = None
            else:
                current = state.pending.get(seq)
                if current is None or len(payload) > len(current):
                    state.pending[seq] = payload
                if len(state.pending) > 256:
                    oldest = min(state.pending)
                    state.pending.pop(oldest, None)
                return b""

        emitted = bytearray(payload)
        if state.next_seq is not None:
            state.next_seq += len(payload)
            state.gap_since = None
        emitted.extend(self._consume_pending(state))
        return bytes(emitted)

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
                direction = OUTGOING
            elif sport in self.console_ports:
                port = sport
                direction = INCOMING
            elif self.auto_detect:
                # Auto-detect: if either port is in the expected range, add it
                min_p = min(self.console_ports) if self.console_ports else 2000
                max_p = max(self.console_ports) if self.console_ports else 2020
                if min_p <= dport <= max_p:
                    self.console_ports.add(dport)
                    port = dport
                    direction = OUTGOING
                    logger.info(f"Auto-detected new console port: {dport}")
                elif min_p <= sport <= max_p:
                    self.console_ports.add(sport)
                    port = sport
                    direction = INCOMING
                    logger.info(f"Auto-detected new console port: {sport}")

            if port is None or direction is None:
                return

            raw_payload = bytes(pkt[Raw].load)
            if not raw_payload:
                return

            # Lightweight dedup: Npcap on loopback captures each packet twice.
            # Track the highest sequence-end per (port, direction) and skip
            # data we've already seen.
            seq = int(getattr(tcp, "seq", 0))
            payload_len = len(raw_payload)
            end_seq = seq + payload_len
            stream_key = (port, direction)

            if stream_key in self._seq_tracker:
                last_end = self._seq_tracker[stream_key]
                if end_seq <= last_end:
                    # Entire packet already processed (duplicate)
                    return
                if seq < last_end:
                    # Partial overlap — trim already-seen bytes
                    raw_payload = raw_payload[last_end - seq:]

            self._seq_tracker[stream_key] = end_seq

            if self.session_logger:
                self.session_logger.write(port, direction, raw_payload)
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

            logger.info("Starting eNSP packet sniffer")
            logger.info(f"Interface: {iface}")
            logger.info(f"Ports: {sorted(self.console_ports) if self.console_ports else 'auto-detect'}")
            logger.info(f"BPF filter: {bpf_filter}")
            logger.info(f"Log directory: {self.log_dir.resolve()}")

            self.session_logger = SessionLogger(self.log_dir)
            self._seq_tracker.clear()

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

        self._seq_tracker.clear()
        self._running = False
        logger.info("Packet sniffer stopped")

    @property
    def is_running(self) -> bool:
        return self._running
