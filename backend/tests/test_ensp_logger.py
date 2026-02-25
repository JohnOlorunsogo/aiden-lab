"""Tests for ENSP packet logger stream cleanup and reassembly."""

from app.services.ensp_logger import ENSPPacketSniffer, INCOMING, OUTGOING, SessionLogger


def _make_sniffer_without_init() -> ENSPPacketSniffer:
    sniffer = object.__new__(ENSPPacketSniffer)
    sniffer._streams = {}
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


def test_strip_telnet_controls_across_packet_boundary(tmp_path):
    logger = SessionLogger(tmp_path)
    key = (2000, INCOMING)

    chunk1 = b"hello\xff"
    chunk2 = b"\xfd\x18world"

    assert logger._strip_telnet_controls(key, chunk1) == b"hello"
    assert logger._strip_telnet_controls(key, chunk2) == b"world"


def test_apply_backspaces_removes_erased_characters():
    assert SessionLogger._apply_backspaces("abcd\b\bXY") == "abXY"


def test_reassemble_payload_trims_overlap_and_retransmit():
    sniffer = _make_sniffer_without_init()
    key = (2000, 50123, 2000, OUTGOING)

    first = sniffer._reassemble_payload(key, 100, b"abcdefghi")
    overlap = sniffer._reassemble_payload(key, 104, b"efghiXYZ\r\n")
    retransmit = sniffer._reassemble_payload(key, 104, b"efghiXYZ\r\n")

    assert first == b"abcdefghi"
    assert overlap == b"XYZ\r\n"
    assert retransmit == b""


def test_reassemble_payload_handles_short_out_of_order_window():
    sniffer = _make_sniffer_without_init()
    key = (2000, 50123, 2000, OUTGOING)

    start = sniffer._reassemble_payload(key, 100, b"abcde")
    out_of_order = sniffer._reassemble_payload(key, 110, b"klm\r\n")
    bridge = sniffer._reassemble_payload(key, 105, b"fghij")

    assert start == b"abcde"
    assert out_of_order == b""
    assert bridge == b"fghijklm\r\n"


def test_reassemble_payload_resyncs_on_large_gap():
    sniffer = _make_sniffer_without_init()
    key = (2000, 50123, 2000, OUTGOING)

    start = sniffer._reassemble_payload(key, 100, b"abcde")
    # Large gap should resync and emit payload instead of stalling.
    gap = sniffer._reassemble_payload(key, 100 + 9000, b"XYZ\r\n")

    assert start == b"abcde"
    assert gap == b"XYZ\r\n"


def test_write_captures_incoming_response_lines(tmp_path):
    """INCOMING response lines must appear in the log file."""
    sl = SessionLogger(tmp_path)

    # Simulate outgoing command
    sl.write(2000, OUTGOING, b"display ip routing-table\r\n")
    # Simulate incoming response (multi-line)
    sl.write(2000, INCOMING, b"Route Flags: R - relay\r\n")
    sl.write(2000, INCOMING, b"Destination/Mask  Proto  Pref\r\n")
    sl.write(2000, INCOMING, b"10.0.0.0/24       Direct 0\r\n")
    sl.write(2000, INCOMING, b"10.0.0.1/32       Direct 0\r\n")
    sl.write(2000, INCOMING, b"<R1>\r\n")

    sl.close()

    # Read what was written
    log_files = list(tmp_path.glob("*.log"))
    assert log_files, "Expected at least one log file"
    content = log_files[0].read_text(encoding="utf-8")

    # All response lines should be present
    assert INCOMING in content, "No INCOMING lines in log"
    assert "Route Flags" in content
    assert "Destination/Mask" in content
    assert "10.0.0.0/24" in content
    assert "10.0.0.1/32" in content


def test_repeated_incoming_lines_kept(tmp_path):
    """Device responses may contain legitimately repeated lines."""
    sl = SessionLogger(tmp_path)

    sl.write(2000, INCOMING, b"Interface GE0/0/0 is up\r\n")
    sl.write(2000, INCOMING, b"Interface GE0/0/0 is up\r\n")  # repeated
    sl.write(2000, INCOMING, b"<R1>\r\n")

    sl.close()

    log_files = list(tmp_path.glob("*.log"))
    assert log_files
    content = log_files[0].read_text(encoding="utf-8")

    # Both instances of the repeated line should be present
    count = content.count("Interface GE0/0/0 is up")
    assert count == 2, f"Expected 2 occurrences but got {count}"

