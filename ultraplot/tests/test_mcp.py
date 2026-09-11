"""Exercise the optional MCP integration without modifying client configuration."""

import asyncio
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

sdk = pytest.importorskip("mcp.server")
if not hasattr(sdk, "MCPServer"):
    pytest.skip("MCP integration requires SDK 2.x", allow_module_level=True)
server = importlib.import_module("ultraplot.mcp")


@pytest.fixture
def docs(tmp_path, monkeypatch):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "colorbars.rst").write_text("Shared colorbars\nUse a shared colorbar.")
    (root / "example.py").write_text("# A colorbar example")
    (root / "unrelated.md").write_text("Geographic projections")
    (root / "whats_new.rst").write_text("Added shared colorbars in version 2.6.")
    (root / "changelog.rst").write_text("shared colorbars " * 100)
    monkeypatch.setattr(server, "DOCS", root)
    return root


def test_ping():
    assert server.ping() == "pong"


def test_search_ranks_relevant_docs_and_excludes_release_notes(docs):
    results = server.search_docs("  Shared colorbars  ")
    assert results[0]["path"] == "docs/colorbars.rst"
    assert "Shared colorbars" in results[0]["content"]
    assert all(item["score"] > 0 for item in results)
    assert not any(
        "changelog" in item["path"] or "whats_new" in item["path"] for item in results
    )
    assert server.search_docs("missingword") == []
    assert server.search_docs("   ") == []


@pytest.mark.parametrize("limit, expected", [(-1, 1), (2, 2), (100, 20)])
def test_search_limits_results(docs, limit, expected):
    for i in range(25):
        (docs / f"example{i}.md").write_text("colorbar")
    assert len(server.search_docs("colorbar", limit=limit)) == expected


def test_missing_documentation(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "DOCS", tmp_path / "missing")
    assert "not installed" in server.search_docs("colorbar")[0]["error"]
    assert server.search_release_notes("colorbar") == []
    assert list(server._text_files()) == []


def test_unreadable_documents_are_skipped(docs, monkeypatch):
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.suffix == ".rst":
            raise OSError("unreadable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    assert server.search_docs("colorbar")[0]["path"] == "docs/example.py"
    assert server.search_release_notes("colorbar") == []


def test_release_notes_search(docs):
    result = server.search_release_notes(" shared colorbars ")
    assert len(result) == 1
    assert result[0]["path"] == "docs/whats_new.rst"
    assert "version 2.6" in result[0]["content"]
    assert server.search_release_notes("missingword") == []
    assert server.search_release_notes(" ") == []


def test_search_returns_snippet_around_match(docs):
    (docs / "long.md").write_text("x " * 3000 + "needle" + " y" * 3000)
    result = server.search_docs("needle")[0]
    assert "needle" in result["content"]
    assert result["content"].startswith("...\n")
    assert result["content"].endswith("\n...")
    assert len(result["content"]) < 3100


def test_snippet_prefers_cluster_when_phrase_is_absent():
    text = "alpha " + "x " * 1500 + "beta alpha beta"
    snippet = server._snippet(
        text, "alpha beta gamma", ["alpha", "beta", "gamma"], before=5, after=30
    )
    assert "beta alpha beta" in snippet
    assert server._snippet("plain text", "missing", ["missing"]) == "plain text"


@pytest.mark.parametrize(
    "query, expected",
    [("How do I use Colorbars?", ["colorbars"]), ("a", ["a"]), ("", [])],
)
def test_query_normalization(query, expected):
    assert server._query_terms(query) == expected


@pytest.mark.parametrize("suffix", [".py", ".rst", ".md", ".txt"])
def test_read_doc_accepts_supported_files(docs, suffix):
    path = docs / ("sample" + suffix)
    path.write_text("Example π", encoding="utf-8")
    assert server.read_doc(path.name) == "Example π"
    assert server.read_doc(" docs/" + path.name + " ") == "Example π"


def test_read_doc_rejects_invalid_files(docs):
    with pytest.raises(FileNotFoundError):
        server.read_doc("missing.rst")
    (docs / "image.png").write_bytes(b"image")
    with pytest.raises(ValueError, match="Unsupported"):
        server.read_doc("image.png")


def test_read_doc_rejects_paths_outside_docs(docs):
    outside = docs.parent / "secret.txt"
    outside.write_text("private")
    (docs / "link.txt").symlink_to(outside)
    for path in ("../secret.txt", "docs/../secret.txt", str(outside), "link.txt"):
        with pytest.raises(ValueError, match="inside"):
            server.read_doc(path)


@pytest.mark.parametrize(
    "symbol",
    ["axes.Axes.format", "ultraplot.axes.Axes.format", " symbol: axes.Axes.format "],
)
def test_get_api_inspects_live_object(symbol):
    result = server.get_api(symbol)
    assert result["found"]
    assert result["symbol"] == "ultraplot.axes.Axes.format"
    assert result["signature"]
    assert "title" in result["docstring"]
    assert result["source_file"].endswith("base.py")
    assert result["source_line"] > 0


@pytest.mark.parametrize("tool", [server.get_api, server.get_source])
def test_unknown_symbol(tool):
    assert tool("_no_such_symbol_") == {
        "found": False,
        "symbol": "ultraplot._no_such_symbol_",
    }


def test_get_source_inspects_live_object():
    result = server.get_source("axes.Axes.format")
    assert result["found"]
    assert "def format(" in result["source"]
    assert result["source_file"].endswith("base.py")
    assert result["source_line"] > 0


@pytest.mark.parametrize("tool", [server.get_api, server.get_source])
def test_non_callable_object_has_no_source(tool):
    result = tool("__version__")
    assert result["found"]
    assert result["source_file"] is None
    assert result["source_line"] is None
    assert result.get("signature") is None
    assert result.get("source") is None


@pytest.mark.parametrize("tool", [server.get_api, server.get_source])
def test_inspection_handles_wrapper_cycle(tool, monkeypatch):
    def cyclic():
        """A callable with malformed wrapper metadata."""

    cyclic.__wrapped__ = cyclic
    monkeypatch.setattr(server.pydoc, "locate", lambda symbol: cyclic)
    result = tool("cyclic")
    assert result["found"]
    if tool is server.get_api:
        assert result["signature"] is None
    else:
        assert result["source"] is None


def test_get_api_handles_unavailable_docstring(monkeypatch):
    monkeypatch.setattr(
        server.inspect, "getdoc", Mock(side_effect=RuntimeError("unavailable"))
    )
    assert server.get_api("axes.Axes.format")["docstring"] is None


@pytest.mark.parametrize("args", [["--help"], ["-h"], ["help"]])
def test_cli_help(args, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["ultraplot-mcp", *args])
    server.main()
    assert "Usage:" in capsys.readouterr().out


def test_cli_rejects_unknown_command(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["ultraplot-mcp", "unknown"])
    with pytest.raises(SystemExit) as exc:
        server.main()
    assert exc.value.code == 2
    assert "Unknown command" in capsys.readouterr().err


def test_cli_runs_server(monkeypatch):
    run = Mock()
    monkeypatch.setattr(server.mcp, "run", run)
    monkeypatch.setattr(sys, "argv", ["ultraplot-mcp"])
    server.main()
    run.assert_called_once_with()


def test_cli_registers_codex(monkeypatch, capsys, tmp_path):
    codex = str(tmp_path / "codex")
    executable = str(tmp_path / "ultraplot-mcp")
    monkeypatch.setattr(
        server.shutil, "which", lambda name: codex if name == "codex" else executable
    )
    run = Mock()
    monkeypatch.setattr(server.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["ultraplot-mcp", "install", "codex"])
    server.main()
    run.assert_called_once_with(
        [codex, "mcp", "add", "ultraplot", "--", executable], check=True
    )
    assert "registered" in capsys.readouterr().out


def test_registration_requires_codex(monkeypatch):
    monkeypatch.setattr(server.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="not found"):
        server.install_codex()


def test_registration_reports_failure(monkeypatch):
    monkeypatch.setattr(server.shutil, "which", lambda name: "/bin/" + name)
    monkeypatch.setattr(
        server.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(1, ["codex"])),
    )
    with pytest.raises(RuntimeError, match="could not register"):
        server.install_codex()


def test_fallback_launch_command_works(monkeypatch):
    monkeypatch.setattr(server.shutil, "which", lambda name: None)
    result = subprocess.run(
        [*server._mcp_server_command(), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout


def test_stdio_client_can_discover_and_call_tools(docs):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "ultraplot.mcp"],
            env={**os.environ, "ULTRAPLOT_MCP_DOCS": str(docs)},
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {tool.name for tool in listed.tools} == {
                    "ping",
                    "search_docs",
                    "search_release_notes",
                    "read_doc",
                    "get_api",
                    "get_source",
                }
                for name, arguments, expected in [
                    ("ping", {}, "pong"),
                    (
                        "search_docs",
                        {"query": "shared colorbars"},
                        "docs/colorbars.rst",
                    ),
                    ("read_doc", {"path": "docs/colorbars.rst"}, "Shared colorbars"),
                    ("search_release_notes", {"query": "colorbars"}, "version 2.6"),
                    ("get_api", {"symbol": "axes.Axes.format"}, "title"),
                    ("get_source", {"symbol": "axes.Axes.format"}, "def format("),
                ]:
                    result = await session.call_tool(name, arguments)
                    assert not result.is_error, result
                    assert expected in json.dumps(result.model_dump())
                result = await session.call_tool("read_doc", {"path": "../outside.txt"})
                assert result.is_error

    asyncio.run(asyncio.wait_for(exercise(), timeout=45))
