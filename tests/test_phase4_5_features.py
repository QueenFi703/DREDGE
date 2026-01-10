"""Tests for Phase IV & V features: time command, enhanced ID strategies, and plugin system."""
import json
import pytest
import re
from dredge.cli import main, discover_plugins


def test_time_command_human(capsys):
    """Test time command with human-readable format."""
    result = main(["time"])
    assert result == 0
    
    captured = capsys.readouterr()
    assert "Local:" in captured.out
    assert "UTC:" in captured.out
    assert "Unix:" in captured.out
    assert "Unix (ms):" in captured.out
    assert "Unix (ns):" in captured.out


def test_time_command_json(capsys):
    """Test time command with JSON format."""
    result = main(["time", "--format", "json"])
    assert result == 0
    
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    
    assert "local" in data
    assert "utc" in data
    assert "unix_seconds" in data
    assert "unix_milliseconds" in data
    assert "unix_nanoseconds" in data
    assert "monotonic" in data


def test_time_command_unix(capsys):
    """Test time command with unix format."""
    result = main(["time", "--format", "unix"])
    assert result == 0
    
    captured = capsys.readouterr()
    unix_time = int(captured.out.strip())
    # Unix timestamp should be reasonable (after 2020, before 2100)
    assert unix_time > 1577836800  # 2020-01-01
    assert unix_time < 4102444800  # 2100-01-01


def test_time_command_iso(capsys):
    """Test time command with ISO format."""
    result = main(["time", "--format", "iso"])
    assert result == 0
    
    captured = capsys.readouterr()
    # ISO format should look like a timestamp with timezone
    output = captured.out.strip()
    assert 'T' in output
    # Should have timezone info (+00:00 or Z)
    assert ('+00:00' in output or output.endswith('Z'))


def test_id_command_fast_strategy(capsys):
    """Test ID command with fast strategy (default)."""
    result = main(["id", "--count", "3", "--strategy", "fast"])
    assert result == 0
    
    captured = capsys.readouterr()
    ids = captured.out.strip().split('\n')
    
    assert len(ids) == 3
    # Fast strategy produces 16 hex characters
    for id_str in ids:
        assert re.fullmatch(r"[0-9a-f]{16}", id_str)


def test_id_command_infrastructure_strategy(capsys):
    """Test ID command with infrastructure strategy (128-bit)."""
    result = main(["id", "--count", "2", "--strategy", "infrastructure"])
    assert result == 0
    
    captured = capsys.readouterr()
    ids = captured.out.strip().split('\n')
    
    assert len(ids) == 2
    # Infrastructure strategy produces 32 hex characters (128-bit)
    for id_str in ids:
        assert re.fullmatch(r"[0-9a-f]{32}", id_str)


def test_id_command_timestamp_strategy(capsys):
    """Test ID command with timestamp strategy."""
    result = main(["id", "--count", "2", "--strategy", "timestamp"])
    assert result == 0
    
    captured = capsys.readouterr()
    ids = captured.out.strip().split('\n')
    
    assert len(ids) == 2
    # Timestamp strategy produces 20-digit numbers
    for id_str in ids:
        assert re.fullmatch(r"\d{20}", id_str)
        # Should be a valid timestamp in nanoseconds
        assert int(id_str) > 0


def test_id_command_uuid4_strategy(capsys):
    """Test ID command with UUID4 strategy."""
    result = main(["id", "--count", "2", "--strategy", "uuid4"])
    assert result == 0
    
    captured = capsys.readouterr()
    ids = captured.out.strip().split('\n')
    
    assert len(ids) == 2
    # UUID4 format: 8-4-4-4-12 hex digits
    for id_str in ids:
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", id_str)


def test_id_strategies_uniqueness(capsys):
    """Test that different strategies produce unique IDs."""
    result = main(["id", "--count", "10", "--strategy", "fast"])
    assert result == 0
    
    captured = capsys.readouterr()
    ids = captured.out.strip().split('\n')
    
    # All IDs should be unique
    assert len(set(ids)) == 10


def test_plugin_list_command(capsys):
    """Test plugin list command."""
    result = main(["plugin", "list"])
    assert result == 0
    
    captured = capsys.readouterr()
    # Should show message about plugins (installed or not)
    assert "plugin" in captured.out.lower()


def test_plugin_discover_function():
    """Test plugin discovery function."""
    plugins = discover_plugins()
    # Should return a dictionary (empty or with plugins)
    assert isinstance(plugins, dict)


def test_plugin_info_nonexistent(capsys):
    """Test plugin info for non-existent plugin."""
    result = main(["plugin", "info", "nonexistent-plugin"])
    
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower()


def test_time_formats_all_valid():
    """Test all time format options are valid."""
    formats = ["human", "json", "unix", "unix_ms", "unix_ns", "iso"]
    
    for fmt in formats:
        result = main(["time", "--format", fmt])
        assert result == 0


def test_id_with_format_and_strategy(capsys):
    """Test ID command with both format and strategy."""
    result = main(["id", "--format", "uuid", "--strategy", "uuid4", "--count", "2"])
    assert result == 0
    
    captured = capsys.readouterr()
    ids = captured.out.strip().split('\n')
    
    assert len(ids) == 2
    # Should produce UUIDs
    for id_str in ids:
        assert '-' in id_str
