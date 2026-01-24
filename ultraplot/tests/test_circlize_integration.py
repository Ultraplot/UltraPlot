import builtins
import sys
import types
from pathlib import Path

import pytest

import ultraplot as uplt
from ultraplot import rc
from ultraplot.axes.plot_types import circlize as circlize_mod


@pytest.fixture()
def fake_pycirclize(monkeypatch):
    class DummyCircos:
        def __init__(self, sectors=None, **kwargs):
            self.sectors = sectors
            self.kwargs = kwargs
            self.plot_called = False
            self.plot_kwargs = None

        def plotfig(self, *args, **kwargs):
            self.plot_called = True
            self.plot_kwargs = kwargs

        @classmethod
        def chord_diagram(cls, matrix_obj, **kwargs):
            obj = cls({"matrix": True})
            obj.matrix_obj = matrix_obj
            obj.kwargs = kwargs
            return obj

        @classmethod
        def radar_chart(cls, table_obj, **kwargs):
            obj = cls({"table": True})
            obj.table_obj = table_obj
            obj.kwargs = kwargs
            return obj

        @classmethod
        def initialize_from_tree(cls, *args, **kwargs):
            obj = cls({"tree": True})
            obj.kwargs = kwargs
            return obj, {"treeviz": True}

        @classmethod
        def initialize_from_bed(cls, *args, **kwargs):
            obj = cls({"bed": True})
            obj.kwargs = kwargs
            return obj

    class DummyMatrix:
        def __init__(self, data):
            self.data = data
            if isinstance(data, dict):
                self.all_names = list(data.keys())
            else:
                self.all_names = ["A", "B"]

    class DummyRadarTable:
        def __init__(self, data):
            self.data = data
            if isinstance(data, dict):
                self.row_names = list(data.keys())
            else:
                self.row_names = ["A", "B"]

    pycirclize = types.ModuleType("pycirclize")
    pycirclize.__path__ = []
    pycirclize.Circos = DummyCircos
    parser = types.ModuleType("pycirclize.parser")
    parser.__path__ = []
    matrix = types.ModuleType("pycirclize.parser.matrix")
    table = types.ModuleType("pycirclize.parser.table")
    matrix.Matrix = DummyMatrix
    table.RadarTable = DummyRadarTable
    parser.matrix = matrix
    parser.table = table
    pycirclize.parser = parser

    monkeypatch.setitem(sys.modules, "pycirclize", pycirclize)
    monkeypatch.setitem(sys.modules, "pycirclize.parser", parser)
    monkeypatch.setitem(sys.modules, "pycirclize.parser.matrix", matrix)
    monkeypatch.setitem(sys.modules, "pycirclize.parser.table", table)

    yield pycirclize

    for name in (
        "pycirclize",
        "pycirclize.parser",
        "pycirclize.parser.matrix",
        "pycirclize.parser.table",
    ):
        sys.modules.pop(name, None)


def test_circos_requires_polar_axes():
    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match="requires a polar axes"):
        ax.circos({"A": 1})
    uplt.close(fig)


def test_circos_delegates_grid(fake_pycirclize):
    fig, axs = uplt.subplots(ncols=2, proj="polar")
    result = axs.circos({"A": 1}, plot=False)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(hasattr(circos, "sectors") for circos in result)
    uplt.close(fig)


def test_chord_diagram_defaults(fake_pycirclize):
    fig, ax = uplt.subplots(proj="polar")
    matrix = {"A": {"B": 1}, "B": {"A": 2}}
    circos = ax.chord_diagram(matrix)
    assert circos.plot_called is True
    assert set(circos.kwargs["cmap"].keys()) == {"A", "B"}
    label_kws = circos.kwargs["label_kws"]
    ticks_kws = circos.kwargs["ticks_kws"]
    assert label_kws["color"] == rc["meta.color"]
    assert label_kws["size"] == rc["font.size"]
    assert ticks_kws["label_size"] == rc["font.size"]
    assert ticks_kws["text_kws"]["color"] == rc["meta.color"]
    uplt.close(fig)


def test_radar_chart_defaults(fake_pycirclize):
    fig, ax = uplt.subplots(proj="polar")
    table = {"A": [1, 2], "B": [3, 4]}
    circos = ax.radar_chart(table, vmin=0, vmax=4, fill=False)
    assert circos.plot_called is True
    assert set(circos.kwargs["cmap"].keys()) == {"A", "B"}
    assert circos.kwargs["grid_line_kws"]["color"] == rc["grid.color"]
    assert circos.kwargs["grid_label_kws"]["color"] == rc["meta.color"]
    assert circos.kwargs["grid_label_kws"]["size"] == rc["font.size"]
    uplt.close(fig)


def test_phylogeny_defaults(fake_pycirclize):
    fig, ax = uplt.subplots(proj="polar")
    circos, treeviz = ax.phylogeny("((A,B),C);")
    assert circos.plot_called is True
    assert treeviz["treeviz"] is True
    assert circos.kwargs["leaf_label_size"] == rc["font.size"]
    uplt.close(fig)


def test_circos_plot_and_tooltip(fake_pycirclize):
    fig, ax = uplt.subplots(proj="polar")
    circos = ax.circos({"A": 1, "B": 2}, plot=True, tooltip=True)
    assert circos.plot_called is True
    assert circos.plot_kwargs["tooltip"] is True
    uplt.close(fig)


def test_circos_bed_plot_toggle(fake_pycirclize, tmp_path):
    bed_path = tmp_path / "tiny.bed"
    bed_path.write_text("chr1\t0\t10\n", encoding="utf-8")
    fig, ax = uplt.subplots(proj="polar")
    circos = ax.circos_bed(bed_path, plot=False)
    assert circos.plot_called is False
    circos = ax.circos_bed(bed_path, plot=True, tooltip=True)
    assert circos.plot_called is True
    assert circos.plot_kwargs["tooltip"] is True
    uplt.close(fig)


def test_import_pycirclize_error_message(monkeypatch):
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pycirclize":
            raise ImportError("boom")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(Path, "is_dir", lambda self: False)
    sys.modules.pop("pycirclize", None)
    with pytest.raises(ImportError, match="pycirclize is required for circos plots"):
        circlize_mod._import_pycirclize()


def test_resolve_defaults_with_existing_objects(fake_pycirclize):
    matrix_mod = sys.modules["pycirclize.parser.matrix"]
    table_mod = sys.modules["pycirclize.parser.table"]
    matrix = matrix_mod.Matrix({"A": {"B": 1}, "B": {"A": 2}})
    table = table_mod.RadarTable({"A": [1, 2], "B": [3, 4]})

    _, matrix_obj, cmap = circlize_mod._resolve_chord_defaults(matrix, cmap=None)
    assert matrix_obj is matrix
    assert set(cmap.keys()) == {"A", "B"}

    _, table_obj, cmap = circlize_mod._resolve_radar_defaults(table, cmap=None)
    assert table_obj is table
    assert set(cmap.keys()) == {"A", "B"}


def test_alias_methods(fake_pycirclize, tmp_path):
    fig, ax = uplt.subplots(proj="polar")
    matrix = {"A": {"B": 1}, "B": {"A": 2}}
    circos = ax.chord(matrix)
    assert circos.plot_called is True

    table = {"A": [1, 2], "B": [3, 4]}
    circos = ax.radar(table, vmin=0, vmax=4, fill=False)
    assert circos.plot_called is True

    bed_path = tmp_path / "mini.bed"
    bed_path.write_text("chr1\t0\t10\n", encoding="utf-8")
    circos = ax.bed(bed_path, plot=False)
    assert hasattr(circos, "sectors")
    uplt.close(fig)
