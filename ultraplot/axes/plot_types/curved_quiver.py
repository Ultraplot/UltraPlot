# The following helper classes and functions for curved_quiver are based on the
# work in the `dfm_tools` repository.
# Original file: https://github.com/Deltares/dfm_tools/blob/829e76f48ebc42460aae118cc190147a595a5f26/dfm_tools/modplot.py
# Special thanks to @veenstrajelmer for the initial implementation

__all__ = [
    "CurvedQuiverSolver",
    "CurvedQuiverSet",
]

from typing import Callable
from dataclasses import dataclass
from matplotlib.streamplot import StreamplotSet
import numpy as np


@dataclass
class CurvedQuiverSet(StreamplotSet):
    lines: object
    arrows: object


class _DomainMap(object):
    """Map representing different coordinate systems.

    Coordinate definitions:
    * axes-coordinates goes from 0 to 1 in the domain.
    * data-coordinates are specified by the input x-y coordinates.
    * grid-coordinates goes from 0 to N and 0 to M for an N x M grid,
        where N and M match the shape of the input data.
    * mask-coordinates goes from 0 to N and 0 to M for an N x M mask,
        where N and M are user-specified to control the density of
        streamlines.

    This class also has methods for adding trajectories to the
    StreamMask. Before adding a trajectory, run `start_trajectory` to
    keep track of regions crossed by a given trajectory. Later, if you
    decide the trajectory is bad (e.g., if the trajectory is very
    short) just call `undo_trajectory`.
    """

    def __init__(self, grid: "Grid", mask: "StreamMask") -> None:
        self.grid = grid
        self.mask = mask

        # Constants for conversion between grid- and mask-coordinates
        self.x_grid2mask = (mask.nx - 1) / grid.nx
        self.y_grid2mask = (mask.ny - 1) / grid.ny
        self.x_mask2grid = 1.0 / self.x_grid2mask
        self.y_mask2grid = 1.0 / self.y_grid2mask

        self.x_data2grid = 1.0 / grid.dx
        self.y_data2grid = 1.0 / grid.dy

    def grid2mask(self, xi: float, yi: float) -> tuple[int, int]:
        """Return nearest space in mask-coords from given grid-coords."""
        return (
            int((xi * self.x_grid2mask) + 0.5),
            int((yi * self.y_grid2mask) + 0.5),
        )

    def mask2grid(self, xm: int, ym: int) -> tuple[float, float]:
        return xm * self.x_mask2grid, ym * self.y_mask2grid

    def data2grid(self, xd: float, yd: float) -> tuple[float, float]:
        return xd * self.x_data2grid, yd * self.y_data2grid

    def grid2data(self, xg: float, yg: float) -> tuple[float, float]:
        return xg / self.x_data2grid, yg / self.y_data2grid

    def start_trajectory(self, xg: float, yg: float) -> None:
        xm, ym = self.grid2mask(xg, yg)
        self.mask._start_trajectory(xm, ym)

    def reset_start_point(self, xg: float, yg: float) -> None:
        xm, ym = self.grid2mask(xg, yg)
        self.mask._current_xy = (xm, ym)

    def update_trajectory(self, xg: float, yg: float) -> None:
        xm, ym = self.grid2mask(xg, yg)
        self.mask._update_trajectory(xm, ym)

    def undo_trajectory(self) -> None:
        self.mask._undo_trajectory()


class CurvedQuiverGrid(object):
    """Grid of data."""

    def __init__(self, x: np.ndarray, y: np.ndarray) -> None:
        if x.ndim == 1:
            pass
        elif x.ndim == 2:
            x_row = x[0, :]
            if not np.allclose(x_row, x):
                raise ValueError("The rows of 'x' must be equal")
            x = x_row
        else:
            raise ValueError("'x' can have at maximum 2 dimensions")

        if y.ndim == 1:
            pass
        elif y.ndim == 2:
            y_col = y[:, 0]
            if not np.allclose(y_col, y.T):
                raise ValueError("The columns of 'y' must be equal")
            y = y_col
        else:
            raise ValueError("'y' can have at maximum 2 dimensions")

        self.nx = len(x)
        self.ny = len(y)
        self.dx = x[1] - x[0]
        self.dy = y[1] - y[0]
        self.x_origin = x[0]
        self.y_origin = y[0]
        self.width = x[-1] - x[0]
        self.height = y[-1] - y[0]

    @property
    def shape(self) -> tuple[int, int]:
        return self.ny, self.nx

    def within_grid(self, xi: float, yi: float) -> bool:
        """Return True if point is a valid index of grid."""
        # Note that xi/yi can be floats; so, for example, we can't simply check
        # `xi < self.nx` since `xi` can be `self.nx - 1 < xi < self.nx`
        return xi >= 0 and xi <= self.nx - 1 and yi >= 0 and yi <= self.ny - 1


class StreamMask(object):
    """Mask to keep track of discrete regions crossed by streamlines.

    The resolution of this grid determines the approximate spacing
    between trajectories. Streamlines are only allowed to pass through
    zeroed cells: When a streamline enters a cell, that cell is set to
    1, and no new streamlines are allowed to enter.
    """

    def __init__(self, density: float | int):
        if np.isscalar(density):
            if density <= 0:
                raise ValueError("If a scalar, 'density' must be positive")
            self.nx = self.ny = int(30 * density)
        else:
            if len(density) != 2:
                raise ValueError("'density' can have at maximum 2 dimensions")
            self.nx = int(30 * density[0])
            self.ny = int(30 * density[1])

        self._mask = np.zeros((self.ny, self.nx))
        self.shape = self._mask.shape
        self._current_xy = None

    def __getitem__(self, *args):
        return self._mask.__getitem__(*args)

    def _start_trajectory(self, xm: int, ym: int):
        """Start recording streamline trajectory"""
        self._traj = []
        self._update_trajectory(xm, ym)

    def _undo_trajectory(self):
        """Remove current trajectory from mask"""
        for t in self._traj:
            self._mask.__setitem__(t, 0)

    def _update_trajectory(self, xm: int, ym: int) -> None:
        """Update current trajectory position in mask.

        If the new position has already been filled, raise
        `InvalidIndexError`.
        """

        self._traj.append((ym, xm))
        self._mask[ym, xm] = 1
        self._current_xy = (xm, ym)


class TerminateTrajectory(Exception):
    pass


class CurvedQuiverSolver:

    def __init__(
        self, x: np.ndarray, y: np.ndarray, density: float | tuple[float, float]
    ) -> None:
        self.grid = Grid(x, y)
        self.mask = StreamMask(density)
        self.domain_map = DomainMap(self.grid, self.mask)

    def get_integrator(
        self,
        u: np.ndarray,
        v: np.ndarray,
        minlength: float,
        resolution: float,
        magnitude: np.ndarray,
    ) -> Callable[[float, float], tuple[tuple[list[float], list[float]], bool] | None]:
        # rescale velocity onto grid-coordinates for integrations.
        u, v = self.domain_map.data2grid(u, v)

        # speed (path length) will be in axes-coordinates
        u_ax = u / self.domain_map.grid.nx
        v_ax = v / self.domain_map.grid.ny
        speed = np.ma.sqrt(u_ax**2 + v_ax**2)

        def forward_time(xi: float, yi: float) -> tuple[float, float]:
            ds_dt = self.interpgrid(speed, xi, yi)
            if ds_dt == 0:
                raise TerminateTrajectory()
            dt_ds = 1.0 / ds_dt
            ui = self.interpgrid(u, xi, yi)
            vi = self.interpgrid(v, xi, yi)
            return ui * dt_ds, vi * dt_ds

        def integrate(
            x0: float, y0: float
        ) -> tuple[tuple[list[float], list[float], bool]] | None:
            """Return x, y grid-coordinates of trajectory based on starting point.

            Integrate both forward and backward in time from starting point
            in grid coordinates. Integration is terminated when a trajectory
            reaches a domain boundary or when it crosses into an already
            occupied cell in the StreamMask. The resulting trajectory is
            None if it is shorter than `minlength`.
            """
            stotal, x_traj, y_traj = 0.0, [], []
            self.domain_map.start_trajectory(x0, y0)
            self.domain_map.reset_start_point(x0, y0)
            stotal, x_traj, y_traj, m_total, hit_edge = self.integrate_rk12(
                x0, y0, forward_time, resolution, magnitude
            )

            if len(x_traj) > 1:
                return (x_traj, y_traj), hit_edge
            else:
                # reject short trajectories
                self.domain_map.undo_trajectory()
                return None

        return integrate

    def integrate_rk12(
        self,
        x0: float,
        y0: float,
        f: Callable[[float, float], tuple[float, float]],
        resolution: float,
        magnitude: np.ndarray,
    ) -> tuple[float, list[float], list[float], list[float], bool]:
        """2nd-order Runge-Kutta algorithm with adaptive step size.

        This method is also referred to as the improved Euler's method, or
        Heun's method. This method is favored over higher-order methods
        because:

        1. To get decent looking trajectories and to sample every mask cell
        on the trajectory we need a small timestep, so a lower order
        solver doesn't hurt us unless the data is *very* high
        resolution. In fact, for cases where the user inputs data
        smaller or of similar grid size to the mask grid, the higher
        order corrections are negligible because of the very fast linear
        interpolation used in `interpgrid`.

        2. For high resolution input data (i.e. beyond the mask
        resolution), we must reduce the timestep. Therefore, an
        adaptive timestep is more suited to the problem as this would be
        very hard to judge automatically otherwise.

        This integrator is about 1.5 - 2x as fast as both the RK4 and RK45
        solvers in most setups on my machine. I would recommend removing
        the other two to keep things simple.
        """
        # This error is below that needed to match the RK4 integrator. It
        # is set for visual reasons -- too low and corners start
        # appearing ugly and jagged. Can be tuned.
        maxerror = 0.003

        # This limit is important (for all integrators) to avoid the
        # trajectory skipping some mask cells. We could relax this
        # condition if we use the code which is commented out below to
        # increment the location gradually. However, due to the efficient
        # nature of the interpolation, this doesn't boost speed by much
        # for quite a bit of complexity.
        maxds = min(1.0 / self.domain_map.mask.nx, 1.0 / self.domain_map.mask.ny, 0.1)
        ds = maxds

        stotal = 0
        xi = x0
        yi = y0
        xf_traj = []
        yf_traj = []
        m_total = []
        hit_edge = False

        while self.domain_map.grid.within_grid(xi, yi):
            xf_traj.append(xi)
            yf_traj.append(yi)
            m_total.append(self.interpgrid(magnitude, xi, yi))

            try:
                k1x, k1y = f(xi, yi)
                k2x, k2y = f(xi + ds * k1x, yi + ds * k1y)
            except IndexError:
                # Out of the domain on one of the intermediate integration steps.
                # Take an Euler step to the boundary to improve neatness.
                ds, xf_traj, yf_traj = self.euler_step(xf_traj, yf_traj, f)
                stotal += ds
                hit_edge = True
                break
            except TerminateTrajectory:
                break

            dx1 = ds * k1x
            dy1 = ds * k1y
            dx2 = ds * 0.5 * (k1x + k2x)
            dy2 = ds * 0.5 * (k1y + k2y)

            nx, ny = self.domain_map.grid.shape
            # Error is normalized to the axes coordinates
            error = np.sqrt(((dx2 - dx1) / nx) ** 2 + ((dy2 - dy1) / ny) ** 2)

            # Only save step if within error tolerance
            if error < maxerror:
                xi += dx2
                yi += dy2
                self.domain_map.update_trajectory(xi, yi)
                if not self.domain_map.grid.within_grid(xi, yi):
                    hit_edge = True
                if (stotal + ds) > resolution * np.mean(m_total):
                    break
                stotal += ds

            # recalculate stepsize based on step error
            if error == 0:
                ds = maxds
            else:
                ds = min(maxds, 0.85 * ds * (maxerror / error) ** 0.5)

        return stotal, xf_traj, yf_traj, m_total, hit_edge

    def euler_step(self, xf_traj, yf_traj, f):
        """Simple Euler integration step that extends streamline to boundary."""
        ny, nx = self.domain_map.grid.shape
        xi = xf_traj[-1]
        yi = yf_traj[-1]
        cx, cy = f(xi, yi)

        if cx == 0:
            dsx = np.inf
        elif cx < 0:
            dsx = xi / -cx
        else:
            dsx = (nx - 1 - xi) / cx

        if cy == 0:
            dsy = np.inf
        elif cy < 0:
            dsy = yi / -cy
        else:
            dsy = (ny - 1 - yi) / cy

        ds = min(dsx, dsy)

        xf_traj.append(xi + cx * ds)
        yf_traj.append(yi + cy * ds)

        return ds, xf_traj, yf_traj

    def interpgrid(self, a, xi, yi):
        """Fast 2D, linear interpolation on an integer grid"""
        Ny, Nx = np.shape(a)

        if isinstance(xi, np.ndarray):
            x = xi.astype(int)
            y = yi.astype(int)

            # Check that xn, yn don't exceed max index
            xn = np.clip(x + 1, 0, Nx - 1)
            yn = np.clip(y + 1, 0, Ny - 1)
        else:
            x = int(xi)
            y = int(yi)
            xn = min(x + 1, Nx - 1)
            yn = min(y + 1, Ny - 1)

        a00 = a[y, x]
        a01 = a[y, xn]
        a10 = a[yn, x]
        a11 = a[yn, xn]

        xt = xi - x
        yt = yi - y

        a0 = a00 * (1 - xt) + a01 * xt
        a1 = a10 * (1 - xt) + a11 * xt
        ai = a0 * (1 - yt) + a1 * yt

        if not isinstance(xi, np.ndarray):
            if np.ma.is_masked(ai):
                raise TerminateTrajectory
        return ai

    def gen_starting_points(self, x, y, grains):
        eps = np.finfo(np.float32).eps
        tmp_x = np.linspace(x.min() + eps, x.max() - eps, grains)
        tmp_y = np.linspace(y.min() + eps, y.max() - eps, grains)
        xs = np.tile(tmp_x, grains)
        ys = np.repeat(tmp_y, grains)
        seed_points = np.array([list(xs), list(ys)])
        return seed_points.T
