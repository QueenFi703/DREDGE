"""Tests for Phase II CLI features: output formats and verbosity."""
import json
import pytest
from dredge.cli import main


def test_inspect_json_format(capsys):
    """Test inspect command with JSON output format."""
    result = main(["inspect", "--format", "json"])
    assert result == 0
    
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    
    assert "version" in data
    assert "configuration" in data
    assert "engine" in data
    assert data["version"] == "0.1.0"


def test_inspect_yaml_format(capsys):
    """Test inspect command with YAML output format."""
    result = main(["inspect", "--format", "yaml"])
    assert result == 0
    
    captured = capsys.readouterr()
    assert "version: 0.1.0" in captured.out
    assert "configuration:" in captured.out
    assert "engine:" in captured.out


def test_doctor_json_format(capsys):
    """Test doctor command with JSON output format."""
    result = main(["doctor", "--format", "json"])
    
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    
    assert "status" in data
    assert "checks" in data
    assert "summary" in data
    assert data["status"] in ["healthy", "degraded"]


def test_doctor_verbose_mode(capsys):
    """Test doctor command with verbose flag."""
    result = main(["doctor", "--verbose"])
    
    captured = capsys.readouterr()
    assert "DREDGE Doctor" in captured.out
    # Verbose mode shows all output
    assert "Python version" in captured.out


def test_print_json_format(capsys):
    """Test print command with JSON output format."""
    result = main(["print", "test message", "--format", "json"])
    assert result == 0
    
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    
    assert data["text"] == "test message"


def test_print_yaml_format(capsys):
    """Test print command with YAML output format."""
    result = main(["print", "hello", "--format", "yaml"])
    assert result == 0
    
    captured = capsys.readouterr()
    assert "text: hello" in captured.out


def test_print_ndjson_format(capsys):
    """Test print command with NDJSON output format."""
    result = main(["print", "data", "--format", "ndjson"])
    assert result == 0
    
    captured = capsys.readouterr()
    # NDJSON is compact JSON on one line
    data = json.loads(captured.out.strip())
    assert data["text"] == "data"


def test_inspect_ndjson_format(capsys):
    """Test inspect command with NDJSON output format."""
    result = main(["inspect", "--format", "ndjson"])
    assert result == 0
    
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert "version" in data
