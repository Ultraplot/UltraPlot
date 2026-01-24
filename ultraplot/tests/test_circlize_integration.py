import sys
import types

import pytest

import ultraplot as uplt
from ultraplot import rc


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
    uplt.close(fig)


def test_radar_chart_defaults(fake_pycirclize):
    fig, ax = uplt.subplots(proj="polar")
    table = {"A": [1, 2], "B": [3, 4]}
    circos = ax.radar_chart(table, vmin=0, vmax=4, fill=False)
    assert circos.plot_called is True
    assert set(circos.kwargs["cmap"].keys()) == {"A", "B"}
    uplt.close(fig)


def test_phylogeny_defaults(fake_pycirclize):
    fig, ax = uplt.subplots(proj="polar")
    circos, treeviz = ax.phylogeny("((A,B),C);")
    assert circos.plot_called is True
    assert treeviz["treeviz"] is True
    assert circos.kwargs["leaf_label_size"] == rc["font.size"]
    uplt.close(fig)
