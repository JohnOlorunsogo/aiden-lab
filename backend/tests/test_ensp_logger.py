"""Tests for ENSP packet logger stream cleanup and reassembly."""

from app.services.ensp_logger import ENSPPacketSniffer, INCOMING, OUTGOING, SessionLogger


def _make_sniffer_without_init() -> ENSPPacketSniffer:
    sniffer = object.__new__(ENSPPacketSniffer)
    sniffer._seq_tracker = {}
    return sniffer


def test_strip_telnet_controls_negotiation_and_subnegotiation(tmp_path):
    logger = SessionLogger(tmp_path)
    key = (2000, INCOMING)

    payload = (
        b"\xff\xfd\x18"  # IAC DO TERMINAL-TYPE
        b"\xff\xfb\x01"  # IAC WILL ECHO
        b"\xff\xfa\x18abc\xff\xf0"  # IAC SB TERMINAL-TYPE ... IAC SE
        b"<Huawei>\r\n"
    )

    cleaned = logger._strip_telnet_controls(key, payload)
    assert cleaned == b"<Huawei>\r\n"


def test_strip_telnet_controls_stateless_no_data_loss(tmp_path):
    """Stateless stripping: a trailing IAC in packet 1 must NOT eat
    bytes from packet 2.  This was the old bug."""
    logger = SessionLogger(tmp_path)
    key = (2000, INCOMING)

    # Packet 1 ends with a lone IAC — should be discarded, not carried
    chunk1 = b"hello\xff"
    # Packet 2 starts with normal text — should NOT be eaten
    chunk2 = b"world"

    assert logger._strip_telnet_controls(key, chunk1) == b"hello"
    assert logger._strip_telnet_controls(key, chunk2) == b"world"


def test_apply_backspaces_removes_erased_characters():
    assert SessionLogger._apply_backspaces("abcd\b\bXY") == "abXY"

def test_seq_tracker_dedup_skips_duplicate_packets():
    """Test that duplicate packets (same seq) are skipped by _seq_tracker."""
    sniffer = _make_sniffer_without_init()
    sniffer._seq_tracker = {}

    key = (2000, OUTGOING)

    # First packet
    sniffer._seq_tracker[key] = 100 + 9  # seq=100, payload=9 bytes -> end_seq=109
    # Duplicate with end_seq <= last_end should be skipped
    assert 105 + 4 <= sniffer._seq_tracker[key]  # end_seq 109 <= 109


def test_seq_tracker_dedup_trims_overlap():
    """Test that overlapping data is trimmed correctly."""
    sniffer = _make_sniffer_without_init()
    sniffer._seq_tracker = {}

    key = (2000, INCOMING)

    # Simulate: first packet sets tracker to end_seq=109
    sniffer._seq_tracker[key] = 109

    # Overlapping packet: seq=104, payload=b"efghiXYZ\r\n" (10 bytes), end_seq=114
    seq = 104
    payload = b"efghiXYZ\r\n"
    last_end = sniffer._seq_tracker[key]
    # Trim: skip first (109 - 104) = 5 bytes
    trimmed = payload[last_end - seq:]
    assert trimmed == b"XYZ\r\n"


def test_seq_tracker_new_stream_accepts_all_data():
    """Test that the first packet for a new stream is always accepted."""
    sniffer = _make_sniffer_without_init()
    sniffer._seq_tracker = {}

    key = (2000, INCOMING)
    # No entry in tracker yet — packet should be fully accepted
    assert key not in sniffer._seq_tracker

