#!/usr/bin/env python3
"""
Projection parsing and subplot creation helpers used by Figure.
"""

from numbers import Integral

import matplotlib.axes as maxes
import matplotlib.gridspec as mgridspec
import matplotlib.projections as mproj
import numpy as np

from .. import axes as paxes
from .. import constructor
from .. import gridspec as pgridspec
from . import _not_none, _pop_params, warnings


class FigureFactory:
    """
    Projection parsing and subplot creation coordinator.
    """

    def __init__(self, figure):
        self.figure = figure

    def parse_proj(
        self,
        proj=None,
        projection=None,
        proj_kw=None,
        projection_kw=None,
        backend=None,
        basemap=None,
        **kwargs,
    ):
        """
        Translate the user-input projection into a registered matplotlib
        axes class.
        """
        figure = self.figure
        proj = _not_none(proj=proj, projection=projection, default="cartesian")
        proj_kw = _not_none(proj_kw=proj_kw, projection_kw=projection_kw, default={})
        backend = figure._parse_backend(backend, basemap)
        if isinstance(proj, str):
            proj = proj.lower()
        if isinstance(figure, paxes.Axes):
            proj = figure._name
        elif isinstance(figure, maxes.Axes):
            raise ValueError("Matplotlib axes cannot be added to ultraplot figures.")

        name = self._resolve_projection_name(proj, proj_kw, backend, kwargs)
        if name is None and isinstance(proj, str):
            raise ValueError(
                f"Invalid projection name {proj!r}. If you are trying to generate a "
                "GeoAxes with a cartopy.crs.Projection or mpl_toolkits.basemap.Basemap "
                "then cartopy or basemap must be installed. Otherwise the known axes "
                f"subclasses are:\n{paxes._cls_table}"
            )
        if name is not None:
            kwargs["projection"] = name
        return kwargs

    def _resolve_projection_name(self, proj, proj_kw, backend, kwargs):
        name = None

        if not isinstance(proj, str):
            if constructor.Projection is not object and isinstance(
                proj, constructor.Projection
            ):
                name = "ultraplot_cartopy"
                kwargs["map_projection"] = proj
            elif constructor.Basemap is not object and isinstance(
                proj, constructor.Basemap
            ):
                name = "ultraplot_basemap"
                kwargs["map_projection"] = proj

        if name is None and isinstance(proj, str):
            try:
                mproj.get_projection_class("ultraplot_" + proj)
            except (KeyError, ValueError):
                pass
            else:
                name = "ultraplot_" + proj

        if name is None and isinstance(proj, str):
            if (
                constructor.Projection is not object
                or constructor.Basemap is not object
            ):
                try:
                    proj_obj = constructor.Proj(
                        proj, backend=backend, include_axes=True, **proj_kw
                    )
                    name = "ultraplot_" + proj_obj._proj_backend
                    kwargs["map_projection"] = proj_obj
                except ValueError:
                    pass
            if name is None and proj in mproj.get_projection_names():
                name = proj
        return name

    def add_subplot(self, *args, **kwargs):
        """
        Driver for adding a single subplot.
        """
        figure = self.figure
        figure._layout_dirty = True
        kwargs = self.parse_proj(**kwargs)

        gs, ss = self._resolve_subplotspec(args or (1, 1, 1), figure.gridspec)
        figure.gridspec = gs
        figure._subplot_counter += 1
        kwargs.setdefault("label", f"subplot_{figure._subplot_counter}")
        kwargs.setdefault("number", 1 + max(figure._subplot_dict, default=0))
        kwargs.pop("refwidth", None)
        kwargs = self._wrap_external_projection(kwargs)
        kwargs.pop("_subplot_spec", None)

        ax = super(type(figure), figure).add_subplot(ss, **kwargs)
        if ax.number:
            figure._subplot_dict[ax.number] = ax
        return ax

    def _resolve_subplotspec(self, args, gs):
        args = self._normalize_subplot_args(args)
        if len(args) == 1 and isinstance(
            args[0], (maxes.SubplotBase, mgridspec.SubplotSpec)
        ):
            return self._subplot_spec_from_input(args[0], gs)
        if (
            len(args) == 3
            and all(isinstance(arg, Integral) for arg in args[:2])
            and all(isinstance(arg, Integral) for arg in np.atleast_1d(args[2]))
        ):
            return self._subplot_spec_from_geometry(args, gs)
        raise ValueError(f"Invalid add_subplot positional arguments {args!r}.")

    def _normalize_subplot_args(self, args):
        if len(args) == 1 and isinstance(args[0], Integral):
            if not 111 <= args[0] <= 999:
                raise ValueError(f"Input {args[0]} must fall between 111 and 999.")
            return tuple(map(int, str(args[0])))
        return args

    def _subplot_spec_from_input(self, ss, gs):
        if isinstance(ss, maxes.SubplotBase):
            ss = ss.get_subplotspec()
        if gs is None:
            gs = ss.get_topmost_subplotspec().get_gridspec()
        if not isinstance(gs, pgridspec.GridSpec):
            raise ValueError(
                "Input subplotspec must be derived from a ultraplot.GridSpec."
            )
        if ss.get_topmost_subplotspec().get_gridspec() is not gs:
            raise ValueError(
                "Input subplotspec must be derived from the active figure gridspec."
            )
        return gs, ss

    def _subplot_spec_from_geometry(self, args, gs):
        nrows, ncols, num = args
        i, j = np.resize(num, 2)
        if gs is None:
            gs = pgridspec.GridSpec(nrows, ncols)
        orows, ocols = gs.get_geometry()
        if orows % nrows:
            raise ValueError(
                f"The input number of rows {nrows} does not divide the "
                f"figure gridspec number of rows {orows}."
            )
        if ocols % ncols:
            raise ValueError(
                f"The input number of columns {ncols} does not divide the "
                f"figure gridspec number of columns {ocols}."
            )
        if any(_ < 1 or _ > nrows * ncols for _ in (i, j)):
            raise ValueError(
                "The input subplot indices must fall between "
                f"1 and {nrows * ncols}. Instead got {i} and {j}."
            )
        rowfact, colfact = orows // nrows, ocols // ncols
        irow, icol = divmod(i - 1, ncols)
        jrow, jcol = divmod(j - 1, ncols)
        irow, icol = irow * rowfact, icol * colfact
        jrow, jcol = (jrow + 1) * rowfact - 1, (jcol + 1) * colfact - 1
        ss = gs[irow : jrow + 1, icol : jcol + 1]
        return gs, ss

    def _wrap_external_projection(self, kwargs):
        projection_name = kwargs.get("projection")
        if not (projection_name and isinstance(projection_name, str)):
            return kwargs
        if projection_name.startswith("ultraplot_"):
            return kwargs
        try:
            proj_class = mproj.get_projection_class(projection_name)
        except (KeyError, ValueError):
            return kwargs
        if issubclass(proj_class, paxes.Axes):
            return kwargs

        external_axes_kwargs = {"projection": projection_name}
        from ..axes.container import create_external_axes_container

        container_name = f"_ultraplot_container_{projection_name}"
        if container_name not in mproj.get_projection_names():
            container_class = create_external_axes_container(
                proj_class, projection_name=container_name
            )
            mproj.register_projection(container_class)
        kwargs["projection"] = container_name
        kwargs["external_axes_class"] = proj_class
        kwargs["external_axes_kwargs"] = external_axes_kwargs
        return kwargs

    def add_subplots(
        self,
        array=None,
        nrows=1,
        ncols=1,
        order="C",
        proj=None,
        projection=None,
        proj_kw=None,
        projection_kw=None,
        backend=None,
        basemap=None,
        **kwargs,
    ):
        """
        Driver for adding multiple subplots.
        """
        figure = self.figure
        if order not in ("C", "F"):
            raise ValueError(f"Invalid order={order!r}. Options are 'C' or 'F'.")
        gs, array, nrows, ncols = self._normalize_subplot_array(
            array,
            nrows,
            ncols,
            order,
        )

        nums = np.unique(array[array != 0])
        naxs = len(nums)
        if any(num < 0 or not isinstance(num, Integral) for num in nums.flat):
            raise ValueError(f"Expected array of positive integers. Got {array}.")

        proj = _not_none(projection=projection, proj=proj)
        proj = self._axes_dict(naxs, proj, kw=False, default="cartesian")
        proj_kw = _not_none(projection_kw=projection_kw, proj_kw=proj_kw) or {}
        proj_kw = self._axes_dict(naxs, proj_kw, kw=True)
        backend = figure._parse_backend(backend, basemap)
        backend = self._axes_dict(naxs, backend, kw=False)
        axes_kw = {
            num: {"proj": proj[num], "proj_kw": proj_kw[num], "backend": backend[num]}
            for num in proj
        }

        for key in ("gridspec_kw", "subplot_kw"):
            kw = kwargs.pop(key, None)
            if not kw:
                continue
            warnings._warn_ultraplot(
                f"{key!r} is not necessary in ultraplot. Pass the "
                "parameters as keyword arguments instead."
            )
            kwargs.update(kw or {})
        figure_kw = _pop_params(kwargs, figure._format_signature)
        gridspec_kw = _pop_params(kwargs, pgridspec.GridSpec._update_params)

        if gs is None:
            if "layout_array" not in gridspec_kw:
                gridspec_kw = {**gridspec_kw, "layout_array": array}
            gs = pgridspec.GridSpec(*array.shape, **gridspec_kw)
        else:
            gs.update(**gridspec_kw)

        axs = naxs * [None]
        axids = [np.where(array == i) for i in np.sort(np.unique(array)) if i > 0]
        axcols = np.array([[x.min(), x.max()] for _, x in axids])
        axrows = np.array([[y.min(), y.max()] for y, _ in axids])
        for idx in range(naxs):
            num = idx + 1
            x0, x1 = axcols[idx, 0], axcols[idx, 1]
            y0, y1 = axrows[idx, 0], axrows[idx, 1]
            ss = gs[y0 : y1 + 1, x0 : x1 + 1]
            kw = {**kwargs, **axes_kw[num], "number": num}
            axs[idx] = figure.add_subplot(ss, **kw)
        figure.format(skip_axes=True, **figure_kw)
        return pgridspec.SubplotGrid(axs)

    def _normalize_subplot_array(self, array, nrows, ncols, order):
        gs = None
        if array is None or isinstance(array, mgridspec.GridSpec):
            if array is not None:
                gs, nrows, ncols = array, array.nrows, array.ncols
            array = np.arange(1, nrows * ncols + 1)[..., None]
            array = array.reshape((nrows, ncols), order=order)
            return gs, array, nrows, ncols

        array = np.atleast_1d(array)
        array[array == None] = 0  # noqa: E711
        array = array.astype(int)
        if array.ndim == 1:
            array = array[None, :] if order == "C" else array[:, None]
        elif array.ndim != 2:
            raise ValueError(f"Expected 1D or 2D array of integers. Got {array}.")
        return gs, array, nrows, ncols

    def _axes_dict(self, naxs, input_value, *, kw=False, default=None):
        if not kw:
            if np.iterable(input_value) and not isinstance(input_value, (str, dict)):
                input_value = {num + 1: item for num, item in enumerate(input_value)}
            elif not isinstance(input_value, dict):
                input_value = {range(1, naxs + 1): input_value}
        else:
            nested = [isinstance(_, dict) for _ in input_value.values()]
            if not any(nested):
                input_value = {range(1, naxs + 1): input_value.copy()}
            elif not all(nested):
                raise ValueError(f"Invalid input {input_value!r}.")

        output = {}
        for nums, item in input_value.items():
            nums = np.atleast_1d(nums)
            for num in nums.flat:
                output[num] = item.copy() if kw else item
        for num in range(1, naxs + 1):
            if num not in output:
                output[num] = {} if kw else default
        if output.keys() != set(range(1, naxs + 1)):
            raise ValueError(
                f"Have {naxs} axes, but {input_value!r} includes props for the axes: "
                + ", ".join(map(repr, sorted(output)))
                + "."
            )
        return output
