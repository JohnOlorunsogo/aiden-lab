"""eNSP Console Logger - Passive packet capture using Scapy."""
import datetime
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

try:
    from scapy.all import AsyncSniffer, Raw, get_if_list, sniff, IP, IPv6  # type: ignore
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    AsyncSniffer = None
    Raw = None
    get_if_list = None
    sniff = None
    IP = None
    IPv6 = None

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
RECENT_LINE_TTL_SEC = 0.5
FORCE_FLUSH_PATTERNS = (
    "Unrecognized command found at '^' position.",
    "Error:",
)
SERVER_HINT_PATTERNS = (
    b"Unrecognized command",
    b"Error:",
    b"position.",
    b"<",
    b"[",
    b"Username",
    b"Password",
    b"login",
    b"Login",
    b"^",
)


@dataclass
class TelnetDecodeState:
    """Tracks incremental Telnet parsing state across packet boundaries."""

    pending_iac: bool = False
    pending_option_for: Optional[int] = None
    in_subnegotiation: bool = False
    subnegotiation_iac: bool = False
    subnegotiation_len: int = 0


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
        self.file_timestamps: Dict[int, str] = {}
        self.input_buffers: Dict[int, str] = {}
        self.output_buffers: Dict[int, str] = {}
        self.last_lines: Dict[Tuple[int, str], str] = {}
        self.duplicate_prompt_count: Dict[Tuple[int, str], int] = {}
        self.telnet_states: Dict[Tuple[int, str], TelnetDecodeState] = {}
        self.last_outgoing: Dict[int, Tuple[str, float]] = {}
        self.recent_lines: Dict[Tuple[int, str, str], float] = {}
        self.debug_port: Optional[int] = None
        dbg = os.getenv("ENSP_DEBUG_PORT")
        if dbg and dbg.isdigit():
            self.debug_port = int(dbg)

    def _open(self, port: int):
        if port in self.handles:
            return
        try:
            ts = self.file_timestamps.get(port) or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.file_timestamps[port] = ts
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
        """Parse Telnet IAC control sequences and emit printable payload bytes only."""
        state = self.telnet_states.setdefault(key, TelnetDecodeState())
        out = bytearray()
        i = 0

        while i < len(data):
            b = data[i]

            if state.in_subnegotiation:
                state.subnegotiation_len += 1
                if state.subnegotiation_len > 512:
                    # Safety valve: avoid being stuck in subnegotiation if SE was lost.
                    state.in_subnegotiation = False
                    state.subnegotiation_iac = False
                    state.subnegotiation_len = 0
                    continue
                if state.subnegotiation_iac:
                    if b == TELNET_SE:
                        state.in_subnegotiation = False
                        state.subnegotiation_len = 0
                    state.subnegotiation_iac = False
                    i += 1
                    continue
                if b == TELNET_IAC:
                    state.subnegotiation_iac = True
                i += 1
                continue

            if state.pending_option_for is not None:
                # Consume option byte for IAC WILL/WONT/DO/DONT/SB.
                if state.pending_option_for == TELNET_SB:
                    state.in_subnegotiation = True
                    state.subnegotiation_iac = False
                    state.subnegotiation_len = 0
                state.pending_option_for = None
                i += 1
                continue

            if state.pending_iac:
                state.pending_iac = False
                if b == TELNET_IAC:
                    out.append(TELNET_IAC)
                elif b in (TELNET_WILL, TELNET_WONT, TELNET_DO, TELNET_DONT, TELNET_SB):
                    state.pending_option_for = b
                # Other IAC commands are intentionally ignored.
                i += 1
                continue

            if b == TELNET_IAC:
                state.pending_iac = True
                i += 1
                continue

            out.append(b)
            i += 1

        return bytes(out)

    def _debug_log(self, port: int, reason: str, payload: bytes, text: str, cleaned: str):
        if self.debug_port is None or port != self.debug_port:
            return
        try:
            path = self.log_dir / f"_debug_{port}.log"
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = (
                f"[{ts}] reason={reason} raw_len={len(payload)} "
                f"text_len={len(text)} clean_len={len(cleaned)}\n"
                f"  raw_hex={payload.hex()}\n"
                f"  text={text!r}\n"
                f"  clean={cleaned!r}\n"
            )
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line)
        except Exception:
            pass

    def _debug_payload(self, port: int, reason: str, payload: bytes, text: str, cleaned: str):
        if self.debug_port is None or port != self.debug_port:
            return
        # Only log payloads for incoming direction to keep the file small.
        self._debug_log(port, reason, payload, text, cleaned)

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

        # Fix exact full-line duplication (common with packet overlap artefacts).
        if len(cleaned) >= 2 and len(cleaned) % 2 == 0:
            half = len(cleaned) // 2
            if cleaned[:half] == cleaned[half:]:
                cleaned = cleaned[:half]

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Repair and normalize error lines when capture drops leading bytes
        # or mixes echoed command text with the error.
        if "Unrecognized command found at '^' position." in cleaned:
            if cleaned.startswith("or: "):
                cleaned = "Error: " + cleaned[4:]

            idx = cleaned.find("Error:")
            if idx >= 0:
                cleaned = cleaned[idx:]
            else:
                marker = "Unrecognized command found at '^' position."
                idx = cleaned.find(marker)
                if idx >= 0:
                    cleaned = "Error: " + cleaned[idx:]

            cleaned = cleaned.replace("^ Error:", "Error:")
            if cleaned.startswith("^ "):
                cleaned = cleaned[2:].lstrip()

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
        key = (port, direction)
        payload = self._strip_telnet_controls(key, data)
        if not payload:
            self._debug_log(port, "payload_empty_after_telnet_strip", data, "", "")
            return

        text = payload.decode("utf-8", errors="replace")
        if not text:
            self._debug_log(port, "text_empty_after_decode", payload, "", "")
            return
        text = self._apply_backspaces(text)
        if not text:
            self._debug_log(port, "text_empty_after_backspace", payload, "", "")
            return

        # Create the file early so logs appear as soon as traffic starts.
        self._open(port)

        if direction == INCOMING:
            # Trace incoming payloads for the debug port even if they are later filtered.
            preview_clean = self._clean_console_text(text)
            self._debug_payload(port, "incoming_payload", payload, text, preview_clean)

        buffer_name = "input_buffers" if direction == OUTGOING else "output_buffers"
        buffers: Dict[int, str] = getattr(self, buffer_name)
        buffers[port] = buffers.get(port, "") + text

        if direction == INCOMING:
            buf = buffers[port]
            if any(pat in buf for pat in FORCE_FLUSH_PATTERNS):
                self._log_line(port, direction, buf)
                buffers[port] = ""
                return

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

        if direction == INCOMING and buffers[port]:
            frag = buffers[port].strip()
            if self._is_prompt_line(frag):
                self._log_line(port, direction, frag)
                buffers[port] = ""

    def _log_line(self, port: int, direction: str, text: str):
        cleaned_text = self._clean_console_text(text)
        if not cleaned_text or cleaned_text.isspace():
            self._debug_log(port, "cleaned_empty", b"", text, cleaned_text)
            return

        key = (port, direction)
        last_line = self.last_lines.get(key, "")
        now_ts = datetime.datetime.now().timestamp()

        recent_key = (port, direction, cleaned_text)
        last_seen = self.recent_lines.get(recent_key)
        if last_seen is not None and (now_ts - last_seen) <= RECENT_LINE_TTL_SEC:
            return
        self.recent_lines[recent_key] = now_ts
        if len(self.recent_lines) > 2000:
            self.recent_lines.clear()

        # Suppress incoming echo lines that match recent outgoing commands.
        # Never suppress error markers or prompts.
        if (
            direction == INCOMING
            and len(cleaned_text) <= 64
            and "Error:" not in cleaned_text
            and cleaned_text != "^"
            and not self._is_prompt_line(cleaned_text)
        ):
            last_out = self.last_outgoing.get(port)
            if last_out:
                last_cmd, ts = last_out
                if (datetime.datetime.now().timestamp() - ts) <= 2.0:
                    if self._normalize_echo(cleaned_text) == self._normalize_echo(last_cmd):
                        self._debug_log(port, "echo_suppressed", b"", text, cleaned_text)
                        return

        if cleaned_text == last_line and self._is_prompt_line(cleaned_text):
            self.duplicate_prompt_count[key] = self.duplicate_prompt_count.get(key, 0) + 1
            if self.duplicate_prompt_count[key] > 1:
                self._debug_log(port, "prompt_dedup", b"", text, cleaned_text)
                return
        elif cleaned_text != last_line:
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
                "huawei",
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
                    self._rename_log_file(port, old_name, hostname)
            break

    def _rename_log_file(self, port: int, old_name: str, new_name: str):
        """Rename the current log file when hostname is discovered."""
        if port not in self.files:
            return
        if old_name == new_name:
            return

        old_path = self.files[port]
        ts = self.file_timestamps.get(port)
        if not ts:
            return

        new_path = old_path.with_name(f"{new_name}_{port}_{ts}.log")
        if new_path == old_path:
            return

        try:
            if port in self.handles:
                try:
                    self.handles[port].close()
                except Exception:
                    pass
                self.handles.pop(port, None)

            old_path.rename(new_path)
            self.files[port] = new_path
            self.handles[port] = open(new_path, "a", encoding="utf-8")
            logger.info(f"Renamed log file: {old_path.name} -> {new_path.name}")
        except Exception as exc:
            logger.warning(f"Failed to rename log file for port {port}: {exc}")

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
        self.recent_lines.clear()
        self.file_timestamps.clear()


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
        self._streams: Dict[Tuple[int, int, int, str], TcpStreamState] = {}
        self._conn_server: Dict[Tuple[Tuple[str, int], Tuple[str, int]], Tuple[str, int]] = {}
        self._bytes_in = 0
        self._bytes_out = 0
        self._pkts_in = 0
        self._pkts_out = 0
        self._last_stats = time.time()
        self._port_stats: Dict[int, Dict[str, int]] = {}

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
        if preferred and preferred.lower() == "auto":
            return self._auto_detect_iface(ifaces)
        if preferred in ifaces:
            return preferred
        for iface in ifaces:
            if "loopback" in iface.lower():
                return iface
        raise ValueError(f"Interface '{preferred}' not found. Available: {', '.join(ifaces)}")

    def _auto_detect_iface(self, ifaces) -> str:
        if not sniff:
            raise ValueError("Auto-detect requires scapy sniff support.")
        counts: Dict[str, int] = {i: 0 for i in ifaces}
        logger.info("Auto-detecting capture interface for eNSP console traffic...")
        for iface in ifaces:
            try:
                sniff(
                    iface=iface,
                    filter=self._build_bpf_filter(),
                    timeout=1,
                    store=False,
                    prn=lambda _pkt, name=iface: counts.__setitem__(name, counts[name] + 1),
                )
            except Exception:
                continue
        best_iface = max(counts, key=counts.get)
        if counts[best_iface] == 0:
            # No traffic seen during probe window; fall back to loopback if present.
            for iface in ifaces:
                if "loopback" in iface.lower():
                    logger.warning(
                        "Auto-detect found no traffic on ports %s; falling back to %s",
                        sorted(self.console_ports),
                        iface,
                    )
                    return iface
            logger.warning(
                "Auto-detect found no traffic on ports %s; falling back to %s",
                sorted(self.console_ports),
                ifaces[0],
            )
            return ifaces[0]
        logger.info(f"Auto-detect selected interface: {best_iface} (packets={counts[best_iface]})")
        return best_iface

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

        state = self._streams.setdefault(stream_key, TcpStreamState())
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
            ip = None
            if IP is not None:
                ip = pkt.getlayer("IP")
            if ip is None and IPv6 is not None:
                ip = pkt.getlayer("IPv6")

            if ip is not None:
                src_ep = (str(ip.src), sport)
                dst_ep = (str(ip.dst), dport)
                conn_key = tuple(sorted([src_ep, dst_ep]))

                flags = int(getattr(tcp, "flags", 0))
                syn = (flags & 0x02) != 0
                ack = (flags & 0x10) != 0
                if syn and not ack:
                    # Client -> server SYN
                    if dport in self.console_ports:
                        self._conn_server[conn_key] = dst_ep
                elif syn and ack:
                    # Server -> client SYN-ACK
                    if sport in self.console_ports:
                        self._conn_server[conn_key] = src_ep

                server_ep = self._conn_server.get(conn_key)
                if server_ep is not None:
                    direction = INCOMING if src_ep == server_ep else OUTGOING
                    port = server_ep[1]
                else:
                    # Heuristic for already-established sessions where we missed SYN/SYN-ACK.
                    if sport in self.console_ports and dport in self.console_ports:
                        raw_payload = bytes(pkt[Raw].load)
                        if any(token in raw_payload for token in SERVER_HINT_PATTERNS):
                            self._conn_server[conn_key] = src_ep
                            direction = INCOMING
                            port = src_ep[1]
                        else:
                            self._conn_server[conn_key] = dst_ep
                            direction = OUTGOING
                            port = dst_ep[1]

            if direction is None:
                if dport in self.console_ports:
                    port = dport
                    direction = OUTGOING
                elif sport in self.console_ports:
                    port = sport
                    direction = INCOMING
            if port is None or direction is None:
                return

            raw_payload = bytes(pkt[Raw].load)
            if not raw_payload:
                return

            if direction == INCOMING:
                self._pkts_in += 1
                self._bytes_in += len(raw_payload)
            else:
                self._pkts_out += 1
                self._bytes_out += len(raw_payload)

            port_stat = self._port_stats.setdefault(
                port,
                {"in_pkts": 0, "in_bytes": 0, "out_pkts": 0, "out_bytes": 0},
            )
            if direction == INCOMING:
                port_stat["in_pkts"] += 1
                port_stat["in_bytes"] += len(raw_payload)
            else:
                port_stat["out_pkts"] += 1
                port_stat["out_bytes"] += len(raw_payload)

            stream_key = (port, sport, dport, direction)
            seq = int(getattr(tcp, "seq", 0))
            payload = self._reassemble_payload(stream_key, seq, raw_payload)
            if payload and self.session_logger:
                self.session_logger.write(port, direction, payload)

            now = time.time()
            if now - self._last_stats >= 5.0:
                per_port = ", ".join(
                    f"{p}:in={s['in_pkts']}/{s['in_bytes']} out={s['out_pkts']}/{s['out_bytes']}"
                    for p, s in sorted(self._port_stats.items())
                )
                logger.info(
                    "Sniffer stats: in=%d pkts/%d bytes, out=%d pkts/%d bytes, per-port: %s",
                    self._pkts_in,
                    self._bytes_in,
                    self._pkts_out,
                    self._bytes_out,
                    per_port or "-",
                )
                self._last_stats = now
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
            self._streams.clear()
            self._bytes_in = 0
            self._bytes_out = 0
            self._pkts_in = 0
            self._pkts_out = 0
            self._last_stats = time.time()
            self._port_stats.clear()

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

        self._streams.clear()
        self._running = False
        logger.info("Packet sniffer stopped")

    @property
    def is_running(self) -> bool:
        return self._running
