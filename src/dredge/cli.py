import argparse
import sys
import socket
import json
import os
from . import __version__


# Plugin discovery and management
def discover_plugins():
    """Discover installed DREDGE plugins via entry points.
    
    Uses importlib.metadata to find plugins registered via entry_points.
    Returns a dict of plugin_name -> entry_point.
    """
    try:
        from importlib.metadata import entry_points
        
        # Look for 'dredge.plugins' entry point group
        if hasattr(entry_points(), 'select'):
            # Python 3.10+ API
            plugins = entry_points().select(group='dredge.plugins')
        else:
            # Python 3.9 API
            plugins = entry_points().get('dredge.plugins', [])
        
        return {ep.name: ep for ep in plugins}
    except ImportError:
        # Fallback for older Python versions
        return {}


def cmd_plugin(action, plugin_name=None):
    """Manage DREDGE plugins."""
    if action == "list":
        plugins = discover_plugins()
        if not plugins:
            print("No plugins installed.")
            print()
            print("To create a plugin, add an entry point in your package's setup.py:")
            print("  entry_points={")
            print("      'dredge.plugins': [")
            print("          'myplugin = mypackage.plugin:main',")
            print("      ]")
            print("  }")
        else:
            print(f"Installed plugins ({len(plugins)}):")
            for name, ep in plugins.items():
                print(f"  • {name}")
                print(f"    Entry: {ep.value}")
    elif action == "info" and plugin_name:
        plugins = discover_plugins()
        if plugin_name not in plugins:
            print(f"Plugin '{plugin_name}' not found.")
            return 1
        
        ep = plugins[plugin_name]
        print(f"Plugin: {plugin_name}")
        print(f"Entry point: {ep.value}")
        print(f"Module: {ep.module if hasattr(ep, 'module') else 'N/A'}")
    else:
        print("Usage: dredge plugin {list|info <name>}")
        return 1
    
    return 0


# Output formatting functions
def format_output(data, format_type="text"):
    """Format output in various formats (text, json, yaml, ndjson)."""
    if format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "yaml":
        # Simple YAML output without external dependency
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    elif format_type == "ndjson":
        return json.dumps(data)
    else:  # text (default)
        return str(data)


def cmd_inspect(format_type="text"):
    """Inspect DREDGE configuration and status."""
    data = {
        "version": __version__,
        "build": "stable",
        "configuration": {
            "default_host": "0.0.0.0",
            "default_port": 3001,
            "debug_mode": False
        },
        "engine": {
            "json_provider": "CompactJSONProvider",
            "hash_strategy": "64-bit polynomial (31-bit rolling)",
            "performance_mode": "compact"
        },
        "identity_contract": {
            "id_type": "content-derived labels (not proofs)",
            "collision_behavior": "last write wins",
            "scale": "suitable for <5e9 items"
        }
    }
    
    if format_type == "text":
        print("═" * 60)
        print("DREDGE Inspector — Status & Philosophy")
        print("═" * 60)
        print()
        print(f"📦 Version: {data['version']}")
        print(f"🔧 Build: {data['build']}")
        print()
        print("⚙️  Active Configuration:")
        for k, v in data['configuration'].items():
            print(f"  • {k.replace('_', ' ').title()}: {v}")
        print()
        print("🎯 Engine Details:")
        for k, v in data['engine'].items():
            print(f"  • {k.replace('_', ' ').title()}: {v}")
        print()
        print("💡 Identity Contract:")
        for k, v in data['identity_contract'].items():
            print(f"  • {k.replace('_', ' ').title()}: {v}")
        print()
        print("═" * 60)
    else:
        print(format_output(data, format_type))
    
    return 0


def cmd_doctor(format_type="text", verbose=False):
    """Run diagnostics on DREDGE installation."""
    checks_passed = 0
    checks_total = 0
    results = {
        "status": "unknown",
        "checks": []
    }
    
    if format_type == "text":
        print("═" * 60)
        print("DREDGE Doctor — System Diagnostics")
        print("═" * 60)
        print()
    
    # Check Python version
    checks_total += 1
    py_version = sys.version_info
    check_result = {
        "name": "Python version",
        "status": "pass" if py_version >= (3, 10) and py_version < (3, 13) else "fail",
        "details": f"{py_version.major}.{py_version.minor}.{py_version.micro}"
    }
    results["checks"].append(check_result)
    
    if check_result["status"] == "pass":
        if format_type == "text":
            print("✓ Python version compatible:", check_result["details"])
        checks_passed += 1
    else:
        if format_type == "text":
            print("✗ Python version incompatible:", check_result["details"])
            print("  Expected: 3.10 <= version < 3.13")
    
    # Check port availability
    checks_total += 1
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 3001))
        sock.close()
        if result != 0:
            check_result = {"name": "Port 3001", "status": "available", "details": "Port is free"}
            if format_type == "text":
                print("✓ Default port 3001 is available")
            checks_passed += 1
        else:
            check_result = {"name": "Port 3001", "status": "in_use", "details": "Port is occupied"}
            if format_type == "text":
                print("⚠ Default port 3001 is in use")
                if verbose:
                    print("  (This is OK if DREDGE server is running)")
            checks_passed += 1  # Not a failure
        results["checks"].append(check_result)
    except Exception as e:
        check_result = {"name": "Port 3001", "status": "error", "details": str(e)}
        results["checks"].append(check_result)
        if format_type == "text" and verbose:
            print(f"⚠ Could not check port availability: {e}")
    
    # Check dependencies
    checks_total += 1
    try:
        import flask
        check_result = {"name": "Flask dependency", "status": "pass", "details": "installed"}
        if format_type == "text":
            print("✓ Flask dependency available")
        checks_passed += 1
    except ImportError:
        check_result = {"name": "Flask dependency", "status": "fail", "details": "missing"}
        if format_type == "text":
            print("✗ Flask dependency missing")
            if verbose:
                print("  Run: pip install flask")
    results["checks"].append(check_result)
    
    # Check performance mode
    checks_total += 1
    try:
        from .server import CompactJSONProvider
        check_result = {"name": "CompactJSONProvider", "status": "pass", "details": "configured"}
        if format_type == "text":
            print("✓ CompactJSONProvider configured")
        checks_passed += 1
    except Exception as e:
        check_result = {"name": "CompactJSONProvider", "status": "fail", "details": str(e)}
        if format_type == "text":
            print(f"✗ CompactJSONProvider check failed: {e}")
    results["checks"].append(check_result)
    
    # Set overall status
    results["status"] = "healthy" if checks_passed == checks_total else "degraded"
    results["summary"] = {
        "checks_passed": checks_passed,
        "checks_total": checks_total
    }
    
    if format_type == "text":
        print()
        print("─" * 60)
        if checks_passed == checks_total:
            print("🎉 Everything looks good! System is healthy.")
        else:
            print(f"⚠️  {checks_total - checks_passed} issue(s) detected. Review above.")
        print("═" * 60)
    else:
        print(format_output(results, format_type))
    
    return 0 if checks_passed == checks_total else 1


def cmd_echo():
    """The signature touch."""
    print("alive")
    return 0


def cmd_time(format_type="human"):
    """Display current time in various formats.
    
    Time is slippery. This makes it speak clearly.
    """
    import time
    import datetime
    
    now = time.time()
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    local_now = datetime.datetime.now()
    
    if format_type == "human":
        print(f"Local:     {local_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"UTC:       {utc_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"Unix:      {int(now)}")
        print(f"Unix (ms): {int(now * 1000)}")
        print(f"Unix (ns): {time.time_ns()}")
    elif format_type == "json":
        import json
        data = {
            "local": local_now.isoformat(),
            "utc": utc_now.isoformat(),
            "unix_seconds": int(now),
            "unix_milliseconds": int(now * 1000),
            "unix_nanoseconds": time.time_ns(),
            "monotonic": time.monotonic()
        }
        print(json.dumps(data, indent=2))
    elif format_type == "unix":
        print(int(now))
    elif format_type == "unix_ms":
        print(int(now * 1000))
    elif format_type == "unix_ns":
        print(time.time_ns())
    elif format_type == "iso":
        print(utc_now.isoformat())
    
    return 0


def cmd_id(count=1, format_type="hex", strategy="fast"):
    """Generate unique IDs using various strategies.
    
    Note: IDs are unique per call but not deterministic across runs.
    The 'hex' format uses the same 64-bit polynomial hash as the server.
    
    Strategies:
    - fast: 64-bit rolling hash (default)
    - uuid4: Random UUID
    - timestamp: Time-based ID with microseconds
    - infrastructure: 128-bit hash for high-scale
    """
    import uuid
    import time
    import hashlib
    
    for i in range(count):
        if strategy == "fast" and format_type == "hex":
            # Use 64-bit rolling hash (matching server strategy)
            # Generate unique input for each ID
            text = f"dredge-id-{uuid.uuid4()}-{time.time_ns()}"
            hash_value = 0
            for char in text:
                hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFFFFFFFFFFFF
            id_str = format(hash_value, '016x')
            print(id_str)
        elif strategy == "infrastructure" and format_type == "hex":
            # 128-bit hash for high-scale infrastructure
            text = f"dredge-infra-{uuid.uuid4()}-{time.time_ns()}"
            hash_obj = hashlib.blake2b(text.encode(), digest_size=16)
            print(hash_obj.hexdigest())
        elif strategy == "timestamp":
            # Timestamp-based ID
            ts = time.time_ns()
            print(f"{ts:020d}")
        elif format_type == "uuid" or strategy == "uuid4":
            # UUIDv4 (random)
            print(str(uuid.uuid4()))
        else:
            # Fallback to hex fast
            text = f"dredge-id-{uuid.uuid4()}-{time.time_ns()}"
            hash_value = 0
            for char in text:
                hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFFFFFFFFFFFF
            id_str = format(hash_value, '016x')
            print(id_str)
    
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dredge", 
        description="DREDGE x Dolly - GPU-CPU Lifter · Save · Files · Print"
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("serve", help="Start the DREDGE x Dolly web server")
    server_parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    server_parser.add_argument(
        "--port", 
        type=int, 
        default=3001, 
        help="Port to listen on (default: 3001)"
    )
    server_parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    server_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode: only fatal errors"
    )
    server_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose mode: timings, decisions, chosen paths"
    )
    server_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable hot reload (watches source files for changes)"
    )
    
    # Print command
    print_parser = subparsers.add_parser("print", help="Print a message or newline")
    print_parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to print (if omitted, prints a clean newline)"
    )
    print_parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "ndjson"],
        default="text",
        help="Output format (default: text)"
    )
    
    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect DREDGE configuration and status")
    inspect_parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "ndjson"],
        default="text",
        help="Output format (default: text)"
    )
    
    # Doctor command
    doctor_parser = subparsers.add_parser("doctor", help="Run system diagnostics")
    doctor_parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "ndjson"],
        default="text",
        help="Output format (default: text)"
    )
    doctor_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output with additional details"
    )
    
    # Echo command (signature touch)
    echo_parser = subparsers.add_parser("echo", help="Verify DREDGE is alive")
    
    # Time command
    time_parser = subparsers.add_parser("time", help="Display current time in various formats")
    time_parser.add_argument(
        "--format",
        choices=["human", "json", "unix", "unix_ms", "unix_ns", "iso"],
        default="human",
        help="Time format (default: human-readable)"
    )
    
    # ID command
    id_parser = subparsers.add_parser("id", help="Generate unique IDs")
    id_parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of IDs to generate (default: 1)"
    )
    id_parser.add_argument(
        "--format",
        choices=["hex", "uuid"],
        default="hex",
        help="ID format: hex (hash), uuid (UUIDv4)"
    )
    id_parser.add_argument(
        "--strategy",
        choices=["fast", "uuid4", "timestamp", "infrastructure"],
        default="fast",
        help="ID generation strategy: fast (64-bit), infrastructure (128-bit), timestamp, uuid4"
    )
    
    # Plugin command (simple implementation)
    plugin_parser = subparsers.add_parser("plugin", help="Manage DREDGE plugins")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_action", help="Plugin actions")
    
    list_plugins = plugin_subparsers.add_parser("list", help="List installed plugins")
    info_plugin = plugin_subparsers.add_parser("info", help="Show plugin information")
    info_plugin.add_argument("plugin_name", help="Plugin name")
    
    args = parser.parse_args(argv)
    
    if args.version:
        print(__version__)
        return 0
    
    if args.command == "serve":
        from .server import run_server
        # Handle verbosity modes
        if args.quiet:
            # Quiet mode - minimal output
            import logging
            logging.basicConfig(level=logging.ERROR)
        elif args.verbose:
            # Verbose mode - detailed output
            import logging
            logging.basicConfig(level=logging.INFO)
            if not args.reload:  # Don't print twice if reload prints it
                print(f"🔧 Starting in verbose mode")
                print(f"   Host: {args.host}")
                print(f"   Port: {args.port}")
                print(f"   Debug: {args.debug}")
                if args.reload:
                    print(f"   Reload: {args.reload}")
        
        run_server(
            host=args.host, 
            port=args.port, 
            debug=args.debug,
            reload=args.reload,
            quiet=args.quiet,
            verbose=args.verbose
        )
        return 0
    
    if args.command == "print":
        if args.format != "text":
            # For non-text formats, output as structured data
            data = {"text": args.text if args.text else ""}
            print(format_output(data, args.format))
        else:
            if args.text is None:
                # Print just a newline - "a quiet pause in the program"
                print()
            else:
                # Print the message
                print(args.text)
        return 0
    
    if args.command == "inspect":
        return cmd_inspect(format_type=args.format)
    
    if args.command == "doctor":
        return cmd_doctor(format_type=args.format, verbose=args.verbose)
    
    if args.command == "echo":
        return cmd_echo()
    
    if args.command == "time":
        return cmd_time(format_type=args.format)
    
    if args.command == "id":
        return cmd_id(count=args.count, format_type=args.format, strategy=args.strategy)
    
    if args.command == "plugin":
        if args.plugin_action:
            plugin_name = args.plugin_name if args.plugin_action == "info" else None
            return cmd_plugin(action=args.plugin_action, plugin_name=plugin_name)
        else:
            print("Usage: dredge plugin {list|info <name>}")
            return 1
    
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
