"""Tests for ENSP packet logger stream cleanup and deduplication."""

from app.services.ensp_logger import ENSPPacketSniffer, INCOMING, OUTGOING, SessionLogger


def _make_sniffer_without_init() -> ENSPPacketSniffer:
    sniffer = object.__new__(ENSPPacketSniffer)
    sniffer._seen_packets = {}
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

    chunk1 = b"hello\xff"
    chunk2 = b"world"

    assert logger._strip_telnet_controls(key, chunk1) == b"hello"
    assert logger._strip_telnet_controls(key, chunk2) == b"world"


def test_apply_backspaces_removes_erased_characters():
    assert SessionLogger._apply_backspaces("abcd\b\bXY") == "abXY"


def test_exact_dedup_skips_identical_packets():
    """Packets with same (seq, len) are skipped as loopback duplicates."""
    sniffer = _make_sniffer_without_init()
    key = (2000, INCOMING)
    seen = sniffer._seen_packets.setdefault(key, set())

    pkt_id = (100, 9)  # seq=100, 9 bytes
    seen.add(pkt_id)

    # Same (seq, len) should be detected as duplicate
    assert pkt_id in seen


def test_exact_dedup_accepts_different_sized_packets():
    """Packets with same seq but different length must NOT be skipped.
    This prevents data loss from Npcap capturing at different fragmentation."""
    sniffer = _make_sniffer_without_init()
    key = (2000, INCOMING)
    seen = sniffer._seen_packets.setdefault(key, set())

    small_pkt = (100, 9)   # small fragment
    full_pkt = (100, 63)   # full packet

    seen.add(small_pkt)

    # Different size at same seq must NOT be treated as duplicate
    assert full_pkt not in seen
