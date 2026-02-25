"""Tests for the Telnet proxy logger."""
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.telnet_proxy import (
    ProxySessionLogger,
    TelnetProxy,
    INCOMING,
    OUTGOING,
)


class TestProxySessionLogger:
    """Tests for ProxySessionLogger."""

    def test_log_data_incoming_line(self, tmp_path):
        """Test logging a complete incoming line."""
        logger = ProxySessionLogger(tmp_path)
        logger.log_data(2000, INCOMING, b"<R1>\r\n")

        # Should have written to a log file
        assert 2000 in logger.handles
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

        content = log_files[0].read_text()
        assert INCOMING in content
        assert "<R1>" in content

    def test_log_data_outgoing_line(self, tmp_path):
        """Test logging a complete outgoing line."""
        logger = ProxySessionLogger(tmp_path)
        logger.log_data(2000, OUTGOING, b"display ip routing-table\r\n")

        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

        content = log_files[0].read_text()
        assert OUTGOING in content
        assert "display ip routing-table" in content

    def test_log_data_buffers_partial_lines(self, tmp_path):
        """Test that partial data is buffered until newline arrives."""
        logger = ProxySessionLogger(tmp_path)

        # Send partial data (no newline yet)
        logger.log_data(2000, INCOMING, b"partial dat")

        # No log file should be created yet (no complete line)
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 0

        # Complete the line
        logger.log_data(2000, INCOMING, b"a complete\r\n")

        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

        content = log_files[0].read_text()
        assert "partial data complete" in content

    def test_log_data_multiline_response(self, tmp_path):
        """Test logging a multi-line response (e.g., routing table output)."""
        logger = ProxySessionLogger(tmp_path)

        response = (
            b"Routing Table:\r\n"
            b"  10.0.0.0/24  via 192.168.1.1\r\n"
            b"  172.16.0.0/16  via 192.168.1.1\r\n"
            b"<R1>\r\n"
        )
        logger.log_data(2000, INCOMING, response)

        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

        content = log_files[0].read_text()
        assert "Routing Table:" in content
        assert "10.0.0.0/24" in content
        assert "172.16.0.0/16" in content
        assert "<R1>" in content

    def test_detects_device_name(self, tmp_path):
        """Test that device name is extracted from incoming prompts."""
        logger = ProxySessionLogger(tmp_path)
        logger.log_data(2000, INCOMING, b"<Router-1>\r\n")

        assert logger.device_names.get(2000) == "Router-1"

    def test_cleans_ansi_sequences(self, tmp_path):
        """Test that ANSI escape sequences are stripped."""
        logger = ProxySessionLogger(tmp_path)
        logger.log_data(2000, INCOMING, b"\x1b[0mclean text\x1b[A\r\n")

        log_files = list(tmp_path.glob("*.log"))
        content = log_files[0].read_text()
        assert "clean text" in content
        assert "\x1b" not in content

    def test_flush_all_writes_remaining_buffer(self, tmp_path):
        """Test that flush_all writes leftover buffered content."""
        logger = ProxySessionLogger(tmp_path)
        logger.log_data(2000, INCOMING, b"no newline yet")
        logger.flush_all()

        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "no newline yet" in content

    def test_close_cleans_up(self, tmp_path):
        """Test that close flushes and cleans up resources."""
        logger = ProxySessionLogger(tmp_path)
        logger.log_data(2000, INCOMING, b"test\r\n")

        logger.close()
        assert len(logger.handles) == 0
        assert len(logger.buffers) == 0


class TestTelnetProxy:
    """Tests for TelnetProxy configuration."""

    def test_proxy_ports_mapping(self, tmp_path):
        """Test that proxy port mapping is correct."""
        proxy = TelnetProxy(
            console_ports={2000, 2001, 2002},
            target_host="127.0.0.1",
            port_offset=1000,
            log_dir=tmp_path,
        )
        # Before start, no servers are active
        assert proxy.proxy_ports == {}
        assert not proxy.is_running

    def test_proxy_init(self, tmp_path):
        """Test proxy initialisation."""
        proxy = TelnetProxy(
            console_ports={2000, 2001},
            target_host="192.168.1.100",
            port_offset=500,
            log_dir=tmp_path,
        )
        assert proxy.console_ports == {2000, 2001}
        assert proxy.target_host == "192.168.1.100"
        assert proxy.port_offset == 500


class TestLogFormat:
    """Tests that logged output matches the expected format for the parser."""

    def test_log_line_format_matches_parser(self, tmp_path):
        """Verify the proxy logger writes lines parseable by LogParser."""
        from app.core.parser import LogParser

        logger = ProxySessionLogger(tmp_path)
        logger.device_names[2000] = "R1"
        logger.log_data(2000, INCOMING, b"Error: Unrecognized command\r\n")

        log_files = list(tmp_path.glob("*.log"))
        content = log_files[0].read_text()

        # Parse the logged line
        lines = LogParser.parse_file(content)
        assert len(lines) >= 1
        assert lines[0].device_id == "R1"
        assert "Unrecognized command" in lines[0].content
