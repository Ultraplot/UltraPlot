"""
Subplot creation and management for ultraplot figures.
"""

import inspect
from numbers import Integral

try:
    from typing import Optional, Tuple, Union
except ImportError:
    from typing_extensions import Optional, Tuple, Union

import matplotlib.axes as maxes
import matplotlib.figure as mfigure
import matplotlib.gridspec as mgridspec
import matplotlib.projections as mproj
import numpy as np

from . import axes as paxes
from . import constructor
from . import gridspec as pgridspec
from .internals import _not_none, _pop_params, warnings


class SubplotManager:
    """
    Manages subplot creation, gridspec ownership, and projection parsing
    for a Figure instance.

    Parameters
    ----------
    figure : `~ultraplot.figure.Figure`
        The parent figure.
    """

    def __init__(self, figure: "Figure"):
        self.figure = figure
        self.subplot_dict: dict = {}
        self.counter: int = 0
        self._gridspec = None

    @property
    def gridspec(self):
        """The single GridSpec used for all subplots in the figure."""
        return self._gridspec

    @gridspec.setter
    def gridspec(self, gs):
        if not isinstance(gs, pgridspec.GridSpec):
            raise ValueError("Gridspec must be a ultraplot.GridSpec instance.")
        self._gridspec = gs
        gs.figure = self.figure  # gridspec.figure should reference the real Figure

    @staticmethod
    def parse_backend(backend=None, basemap=None):
        """
        Handle deprecation of basemap and cartopy package.
        """
        if backend == "basemap":
            warnings._warn_ultraplot(
                f"{backend=} will be deprecated in next major release (v2.0). "
                "See https://github.com/Ultraplot/ultraplot/pull/243"
            )
        return backend

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
        Translate user-input projection into a registered matplotlib axes class.
        """
        # Parse arguments
        proj = _not_none(proj=proj, projection=projection, default="cartesian")
        proj_kw = _not_none(proj_kw=proj_kw, projection_kw=projection_kw, default={})
        backend = self.parse_backend(backend, basemap)
        if isinstance(proj, str):
            proj = proj.lower()
        if isinstance(self.figure, paxes.Axes):
            proj = self.figure._name
        elif isinstance(self.figure, maxes.Axes):
            raise ValueError("Matplotlib axes cannot be added to ultraplot figures.")

        # Search axes projections
        name = None

        # Handle cartopy/basemap Projection objects directly
        # These should be converted to Ultraplot GeoAxes
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
            # Try geographic projections first if cartopy/basemap available
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
                    pass  # not a geographic projection, try matplotlib registry below

            # If not geographic, check if registered globally in matplotlib
            # (e.g., 'ternary', 'polar', '3d')
            if name is None and proj in mproj.get_projection_names():
                name = proj

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

    def add_subplot(self, *args, **kwargs):
        """
        The driver function for adding single subplots.
        """
        fig = self.figure
        fig._layout_dirty = True
        kwargs = self.parse_proj(**kwargs)

        args = args or (1, 1, 1)
        gs = self.gridspec

        # Integer arg
        if len(args) == 1 and isinstance(args[0], Integral):
            if not 111 <= args[0] <= 999:
                raise ValueError(f"Input {args[0]} must fall between 111 and 999.")
            args = tuple(map(int, str(args[0])))

        # Subplot spec
        if len(args) == 1 and isinstance(
            args[0], (maxes.SubplotBase, mgridspec.SubplotSpec)
        ):
            ss = args[0]
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

        # Row and column spec
        elif (
            len(args) == 3
            and all(isinstance(arg, Integral) for arg in args[:2])
            and all(isinstance(arg, Integral) for arg in np.atleast_1d(args[2]))
        ):
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
            irow, icol = divmod(i - 1, ncols)  # convert to zero-based
            jrow, jcol = divmod(j - 1, ncols)
            irow, icol = irow * rowfact, icol * colfact
            jrow, jcol = (jrow + 1) * rowfact - 1, (jcol + 1) * colfact - 1
            ss = gs[irow : jrow + 1, icol : jcol + 1]

        else:
            raise ValueError(f"Invalid add_subplot positional arguments {args!r}.")

        # Add the subplot
        # NOTE: Must assign unique label to each subplot or else subsequent calls
        # to add_subplot() in mpl < 3.4 may return an already-drawn subplot in the
        # wrong location due to gridspec override.
        self.gridspec = gs  # trigger layout adjustment
        self.counter += 1
        kwargs.setdefault("label", f"subplot_{self.counter}")
        kwargs.setdefault("number", 1 + max(self.subplot_dict, default=0))
        kwargs.pop("refwidth", None)  # TODO: remove this

        # Use container approach for external projections to make them
        # ultraplot-compatible. Skip projections that start with "ultraplot_"
        # as these are already Ultraplot axes classes.
        projection_name = kwargs.get("projection")
        external_axes_class = None
        external_axes_kwargs = {}

        if projection_name and isinstance(projection_name, str):
            if not projection_name.startswith("ultraplot_"):
                try:
                    proj_class = mproj.get_projection_class(projection_name)
                    if not issubclass(proj_class, paxes.Axes):
                        external_axes_class = proj_class
                        external_axes_kwargs["projection"] = projection_name

                        from .axes.container import create_external_axes_container

                        container_name = f"_ultraplot_container_{projection_name}"
                        if container_name not in mproj.get_projection_names():
                            container_class = create_external_axes_container(
                                proj_class, projection_name=container_name
                            )
                            mproj.register_projection(container_class)

                        kwargs["projection"] = container_name
                        kwargs["external_axes_class"] = external_axes_class
                        kwargs["external_axes_kwargs"] = external_axes_kwargs
                except (KeyError, ValueError):
                    pass

        kwargs.pop("_subplot_spec", None)

        # NOTE: We call mfigure.Figure.add_subplot directly (unbound) rather
        # than fig.add_subplot because SubplotManager is not a Figure subclass
        # and cannot use super(). This bypasses any Figure.add_subplot override,
        # which is acceptable because Figure._add_subplot is the real entry point.
        ax = mfigure.Figure.add_subplot(fig, ss, **kwargs)
        if ax.number:
            self.subplot_dict[ax.number] = ax
        return ax

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
        The driver function for adding multiple subplots.
        """
        fig = self.figure

        # Helper to normalize per-axes arguments into {num: value} dicts.
        # Accepts 'string', {1: 'string1', (2, 3): 'string2'}, or lists.
        def _axes_dict(naxs, input, kw=False, default=None):
            if not kw:  # 'string' or {1: 'string1', (2, 3): 'string2'}
                if np.iterable(input) and not isinstance(input, (str, dict)):
                    input = {num + 1: item for num, item in enumerate(input)}
                elif not isinstance(input, dict):
                    input = {range(1, naxs + 1): input}
            else:  # {key: value} or {1: {key: value1}, (2, 3): {key: value2}}
                nested = [isinstance(_, dict) for _ in input.values()]
                if not any(nested):  # any([]) == False
                    input = {range(1, naxs + 1): input.copy()}
                elif not all(nested):
                    raise ValueError(f"Invalid input {input!r}.")
            # Unfurl keys that contain multiple axes numbers
            output = {}
            for nums, item in input.items():
                nums = np.atleast_1d(nums)
                for num in nums.flat:
                    output[num] = item.copy() if kw else item
            # Fill with default values
            for num in range(1, naxs + 1):
                if num not in output:
                    output[num] = {} if kw else default
            if output.keys() != set(range(1, naxs + 1)):
                raise ValueError(
                    f"Have {naxs} axes, but {input!r} includes props for the axes: "
                    + ", ".join(map(repr, sorted(output)))
                    + "."
                )
            return output

        # Build the subplot array
        # NOTE: Currently this may ignore user-input nrows/ncols without warning
        if order not in ("C", "F"):  # better error message
            raise ValueError(f"Invalid order={order!r}. Options are 'C' or 'F'.")
        gs = None
        if array is None or isinstance(array, mgridspec.GridSpec):
            if array is not None:
                gs, nrows, ncols = array, array.nrows, array.ncols
            array = np.arange(1, nrows * ncols + 1)[..., None]
            array = array.reshape((nrows, ncols), order=order)
        else:
            array = np.atleast_1d(array)
            array[array == None] = 0  # None or 0 both valid placeholders  # noqa: E711
            array = array.astype(int)
            if array.ndim == 1:  # interpret as single row or column
                array = array[None, :] if order == "C" else array[:, None]
            elif array.ndim != 2:
                raise ValueError(f"Expected 1D or 2D array of integers. Got {array}.")

        # Parse input format, gridspec, and projection arguments
        # NOTE: Permit figure format keywords for e.g. 'collabels' (more intuitive)
        nums = np.unique(array[array != 0])
        naxs = len(nums)
        if any(num < 0 or not isinstance(num, Integral) for num in nums.flat):
            raise ValueError(f"Expected array of positive integers. Got {array}.")
        proj = _not_none(projection=projection, proj=proj)
        proj = _axes_dict(naxs, proj, kw=False, default="cartesian")
        proj_kw = _not_none(projection_kw=projection_kw, proj_kw=proj_kw) or {}
        proj_kw = _axes_dict(naxs, proj_kw, kw=True)
        backend = self.parse_backend(backend, basemap)
        backend = _axes_dict(naxs, backend, kw=False)
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
        figure_kw = _pop_params(kwargs, fig._format_signature)
        gridspec_kw = _pop_params(kwargs, pgridspec.GridSpec._update_params)

        # Create or update the gridspec and add subplots with subplotspecs
        # NOTE: The gridspec is added to the figure when we pass the subplotspec
        if gs is None:
            if "layout_array" not in gridspec_kw:
                gridspec_kw = {**gridspec_kw, "layout_array": array}
            gs = pgridspec.GridSpec(*array.shape, **gridspec_kw)
        else:
            gs.update(**gridspec_kw)
        axs = naxs * [None]  # list of axes
        axids = [np.where(array == i) for i in np.sort(np.unique(array)) if i > 0]
        axcols = np.array([[x.min(), x.max()] for _, x in axids])
        axrows = np.array([[y.min(), y.max()] for y, _ in axids])
        for idx in range(naxs):
            num = idx + 1
            x0, x1 = axcols[idx, 0], axcols[idx, 1]
            y0, y1 = axrows[idx, 0], axrows[idx, 1]
            ss = gs[y0 : y1 + 1, x0 : x1 + 1]
            kw = {**kwargs, **axes_kw[num], "number": num}
            axs[idx] = fig.add_subplot(ss, **kw)
        fig.format(skip_axes=True, **figure_kw)
        return pgridspec.SubplotGrid(axs)

    @property
    def subplotgrid(self):
        """A SubplotGrid of numbered subplots sorted by number."""
        return pgridspec.SubplotGrid([s for _, s in sorted(self.subplot_dict.items())])
