#!/usr/bin/env python3
"""
Fast drop-in replacements for the `matplotlib.animation` classes.

The classes here subclass their Matplotlib counterparts, so the constructor
signatures, the attributes, and the notebook representations are unchanged.
What differs is how frames are rendered:

* `~ultraplot.animation.FuncAnimation.save` bypasses the per-frame
  `~matplotlib.figure.Figure.savefig` call used by Matplotlib's writers and
  instead renders straight into the Agg buffer, piping raw ``RGBA`` bytes to
  the encoder. No PNG round-trip, no ``print_figure`` machinery.
* The expensive UltraPlot tight-layout pass runs once, for the first frame,
  rather than on every frame.
* Blitting is used while saving, not just interactively, so only the artists
  the update function returns are redrawn per frame.

Everything falls back to Matplotlib's own implementation when the fast path
cannot be used (custom writer instances, ``bbox_inches``, vector output, and
so on), so the output is never silently wrong.
"""

from __future__ import annotations

import itertools
import os
import subprocess
from contextlib import ExitStack, contextmanager
from pathlib import Path

import matplotlib as mpl
import matplotlib.animation as manimation
import numpy as np
from matplotlib import cbook

from .internals import warnings

__all__ = [
    "FuncAnimation",
    "ArtistAnimation",
    "animate",
]

#: Containers written frame-by-frame by piping raw RGBA to ``ffmpeg``.
_FFMPEG_SUFFIXES = frozenset(
    (".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".ogv", ".ogg")
)

#: Containers assembled in memory by Pillow.
_PILLOW_SUFFIXES = frozenset((".gif", ".webp", ".apng", ".png", ".tiff", ".tif"))

#: Writer names whose behavior the fast path reproduces exactly. Anything else,
#: ``imagemagick`` included, is handed back to Matplotlib.
_FAST_WRITERS = frozenset(("ffmpeg", "pillow"))


def _suffix(filename):
    """
    Return the lowercase suffix of a path-like filename.
    """
    return Path(os.fspath(filename)).suffix.lower()


def _zsorted(artists):
    """
    Return the artists in ascending z-order, matching a normal draw.
    """
    return sorted(artists, key=lambda artist: artist.get_zorder())


class _RawWriter:
    """
    Base class for writers that consume raw ``RGBA`` frames.
    """

    def __init__(self, filename, fps, metadata=None):
        self.filename = os.fspath(filename)
        self.fps = fps
        self.metadata = metadata or {}
        self.width = self.height = None

    def setup(self, width, height):
        self.width, self.height = width, height

    def write(self, buffer):  # pragma: no cover - abstract
        raise NotImplementedError

    def finish(self):  # pragma: no cover - abstract
        raise NotImplementedError

    def cleanup(self):
        pass


class _RawFFMpegWriter(_RawWriter):
    """
    Pipe raw ``RGBA`` frames into ``ffmpeg`` with no intermediate encoding.
    """

    def __init__(
        self,
        filename,
        fps,
        *,
        codec=None,
        bitrate=None,
        extra_args=None,
        metadata=None,
    ):
        super().__init__(filename, fps, metadata)
        self.codec = codec or mpl.rcParams["animation.codec"]
        self.bitrate = mpl.rcParams["animation.bitrate"] if bitrate is None else bitrate
        self.extra_args = extra_args
        self._proc = None

    @staticmethod
    def available():
        """
        Return whether the configured ``ffmpeg`` binary can be executed.
        """
        try:
            manimation.FFMpegWriter.bin_path()
        except Exception:
            return False
        return bool(manimation.FFMpegWriter.isAvailable())

    def _command(self):
        args = [
            manimation.FFMpegWriter.bin_path(),
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{self.width}x{self.height}",
            "-pix_fmt",
            "rgba",
            "-framerate",
            str(self.fps),
            "-i",
            "pipe:0",
            "-an",
        ]
        if self.codec:
            args += ["-vcodec", self.codec]
        # Most players require even dimensions and 4:2:0 chroma for h264-family
        # codecs. Scaling is a no-op when the frame is already even-sized.
        if self.codec in ("h264", "libx264", "libx265", "hevc", "mpeg4"):
            args += [
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-pix_fmt",
                "yuv420p",
            ]
        if self.bitrate is not None and self.bitrate > 0:
            args += ["-b:v", f"{int(self.bitrate)}k"]
        for key, value in self.metadata.items():
            args += ["-metadata", f"{key}={value}"]
        extra = self.extra_args
        if extra is None:
            extra = mpl.rcParams["animation.ffmpeg_args"]
        args += list(extra or ())
        args += [self.filename]
        return args

    def setup(self, width, height):
        super().setup(width, height)
        self._proc = subprocess.Popen(
            self._command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def write(self, buffer):
        try:
            self._proc.stdin.write(buffer)
        except BrokenPipeError as err:
            _, stderr = self._proc.communicate()
            raise RuntimeError(
                "ffmpeg exited while frames were being written:\n"
                + stderr.decode("utf-8", "replace")
            ) from err

    def finish(self):
        # communicate() closes stdin itself, which signals end-of-stream.
        _, stderr = self._proc.communicate()
        if self._proc.returncode:
            raise RuntimeError(
                f"ffmpeg exited with code {self._proc.returncode}:\n"
                + stderr.decode("utf-8", "replace")
            )

    def cleanup(self):
        proc = self._proc
        if proc is None or proc.returncode is not None:
            return
        try:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
        finally:
            proc.kill()
            proc.wait()


class _RawPillowWriter(_RawWriter):
    """
    Collect raw ``RGBA`` frames and write an animated image with Pillow.
    """

    def __init__(self, filename, fps, *, metadata=None):
        super().__init__(filename, fps, metadata)
        self._frames = []

    def write(self, buffer):
        from PIL import Image

        # Copy: the canvas hands back the same buffer for every frame.
        self._frames.append(
            Image.frombuffer(
                "RGBA", (self.width, self.height), bytes(buffer), "raw", "RGBA", 0, 1
            )
        )

    def finish(self):
        if not self._frames:
            raise RuntimeError("No frames were rendered for the animation.")
        first, *rest = self._frames
        first.save(
            self.filename,
            save_all=True,
            append_images=rest,
            duration=int(1000 / self.fps),
            loop=0,
        )

    def cleanup(self):
        self._frames.clear()


class _FastAnimationBase:
    """
    Mixin implementing the fast save path shared by the animation classes.

    Subclasses must implement `_fast_frame_artists`, returning the artists a
    given frame changed, and `_fast_frame_seq`, returning the frames to save.
    """

    #: Set by the subclass constructors.
    _freeze_layout = True

    # Fast-path hooks

    def _fast_frame_seq(self):  # pragma: no cover - abstract
        raise NotImplementedError

    def _fast_frame_artists(self, frame):  # pragma: no cover - abstract
        raise NotImplementedError

    def _fast_init_artists(self, frame):  # pragma: no cover - abstract
        raise NotImplementedError

    # Layout freezing

    @contextmanager
    def _frozen_layout(self):
        """
        Run the UltraPlot layout solver once instead of once per frame.

        UltraPlot recomputes tight layout whenever the figure is marked dirty.
        During an animation the geometry must stay fixed anyway, or frames
        would jitter, so the solver is disabled after the first draw.
        """
        fig = self._fig
        if not self._freeze_layout:
            yield
            return
        state = (
            getattr(fig, "_layout_initialized", False),
            getattr(fig, "_layout_dirty", False),
            getattr(fig, "_skip_autolayout", False),
        )
        try:
            yield _LayoutFreezer(fig)
        finally:
            fig._layout_initialized, fig._layout_dirty, fig._skip_autolayout = state

    @contextmanager
    def _animated_artists(self, artists=()):
        """
        Temporarily mark artists as animated so full draws skip them.

        Yields a function that marks further artists, for update functions that
        return a different set of artists as the animation goes on.
        """
        previous = {}

        def mark(artists):
            for artist in artists:
                previous.setdefault(artist, artist.get_animated())
                artist.set_animated(True)

        mark(artists)
        try:
            yield mark
        finally:
            for artist, animated in previous.items():
                artist.set_animated(animated)

    @contextmanager
    def _suspended_event_source(self):
        """
        Keep the interactive timer from starting on the frames drawn here.

        `matplotlib.animation.Animation` starts itself from the figure's first
        ``draw_event``. The draws below are for the movie file, not the screen.
        """
        cid = getattr(self, "_first_draw_id", None)
        canvas = self._fig.canvas
        if cid is not None:
            canvas.mpl_disconnect(cid)
        try:
            yield
        finally:
            if cid is not None:
                self._first_draw_id = self._fig.canvas.mpl_connect(
                    "draw_event", self._start
                )

    @contextmanager
    def _agg_canvas(self):
        """
        Ensure the figure has a canvas that can blit and expose an RGBA buffer.
        """
        fig = self._fig
        canvas = fig.canvas
        if all(
            callable(getattr(canvas, name, None))
            for name in ("buffer_rgba", "copy_from_bbox", "restore_region")
        ):
            yield canvas
            return
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        original = canvas
        try:
            yield FigureCanvasAgg(fig)
        finally:
            fig.set_canvas(original)

    def _can_fast_save(self, filename, writer, savefig_kwargs, extra_anim):
        """
        Return whether the fast path reproduces the requested output exactly.
        """
        if extra_anim:
            return False
        if writer is not None and not isinstance(writer, str):
            return False  # a configured writer instance must be honored
        if isinstance(writer, str) and writer not in _FAST_WRITERS:
            return False
        if savefig_kwargs:
            # Any styling override (facecolor, transparency, bbox_inches, ...)
            # belongs to the savefig pipeline the fast path skips.
            return False
        suffix = _suffix(filename)
        if suffix in _FFMPEG_SUFFIXES:
            return writer in (None, "ffmpeg") and _RawFFMpegWriter.available()
        if suffix in _PILLOW_SUFFIXES:
            if writer == "ffmpeg":
                return False
            try:
                import PIL  # noqa: F401
            except ImportError:
                return False
            return True
        return False

    def _make_raw_writer(self, filename, fps, codec, bitrate, extra_args, metadata):
        """
        Return the raw-frame writer matching the output file extension.
        """
        if _suffix(filename) in _FFMPEG_SUFFIXES:
            return _RawFFMpegWriter(
                filename,
                fps,
                codec=codec,
                bitrate=bitrate,
                extra_args=extra_args,
                metadata=metadata,
            )
        return _RawPillowWriter(filename, fps, metadata=metadata)

    def _fast_save(
        self,
        filename,
        fps,
        dpi,
        codec,
        bitrate,
        extra_args,
        metadata,
        progress_callback,
        blit,
    ):
        """
        Render every frame straight into the Agg buffer and pipe it out.
        """
        fig = self._fig
        self._draw_was_started = True
        raw = self._make_raw_writer(filename, fps, codec, bitrate, extra_args, metadata)
        total = getattr(self, "_save_count", None)

        with ExitStack() as stack:
            stack.callback(raw.cleanup)
            canvas = stack.enter_context(self._agg_canvas())
            # NOTE: Matplotlib's own save sets canvas._is_saving, but that makes
            # `Axes.draw` include animated artists so that savefig captures
            # them. That would bake the first frame into the blitting
            # background. Suppress the timer-starting draw callback instead.
            stack.enter_context(cbook._setattr_cm(canvas, manager=None))
            stack.enter_context(self._suspended_event_source())
            if dpi is not None and dpi != fig.dpi:
                original_dpi = fig.dpi
                stack.callback(fig.set_dpi, original_dpi)
                fig.set_dpi(dpi)

            # The first draw runs tight layout; every later one reuses it.
            freezer = stack.enter_context(self._frozen_layout())
            frames = self._fast_frame_seq()
            try:
                first = next(frames)
            except StopIteration:
                raise ValueError("The animation has no frames to save.") from None
            frames = itertools.chain((first,), frames)
            init_artists = list(self._fast_init_artists(first) or ())
            if blit and not init_artists:
                blit = False  # nothing was returned, so nothing can be blitted
            mark_animated = None
            if blit:
                mark_animated = stack.enter_context(
                    self._animated_artists(init_artists)
                )

            canvas.draw()
            if freezer is not None:
                freezer.freeze()
            background = canvas.copy_from_bbox(fig.bbox) if blit else None

            height, width = np.asarray(canvas.buffer_rgba()).shape[:2]
            raw.setup(width, height)
            stack.callback(raw.finish)

            for count, frame in enumerate(frames):
                artists = self._fast_frame_artists(frame)
                if blit:
                    artists = _zsorted(artists or init_artists)
                    mark_animated(artists)
                    canvas.restore_region(background)
                    for artist in artists:
                        fig.draw_artist(artist)
                else:
                    if freezer is not None:
                        freezer.skip_next_layout()
                    canvas.draw()
                raw.write(memoryview(canvas.buffer_rgba()))
                if progress_callback is not None:
                    progress_callback(count, total)


class _LayoutFreezer:
    """
    Hold an UltraPlot figure's layout fixed between animation frames.
    """

    def __init__(self, fig):
        self._fig = fig
        self._frozen = False

    def freeze(self):
        """
        Mark the current layout as final.
        """
        self._fig._layout_initialized = True
        self._fig._layout_dirty = False
        self._frozen = True
        self.skip_next_layout()

    def skip_next_layout(self):
        """
        Skip the layout solver on the next draw of the figure.
        """
        if self._frozen:
            self._fig._layout_dirty = False
            self._fig._skip_autolayout = True


class _FastSaveMixin(_FastAnimationBase):
    """
    Adds the fast `save` override to a Matplotlib animation class.
    """

    def save(
        self,
        filename,
        writer=None,
        fps=None,
        dpi=None,
        codec=None,
        bitrate=None,
        extra_args=None,
        metadata=None,
        extra_anim=None,
        savefig_kwargs=None,
        *,
        progress_callback=None,
        fast=None,
        blit=None,
    ):
        """
        Save the animation to a movie file.

        Parameters
        ----------
        filename : path-like
            The output file, e.g. ``'movie.mp4'`` or ``'movie.gif'``.
        writer : str or `~matplotlib.animation.AbstractMovieWriter`, optional
            Same meaning as in `matplotlib.animation.Animation.save`. Passing a
            writer *instance*, or a writer the fast path does not implement,
            transparently falls back to Matplotlib's implementation.
        fps : int, optional
            Frames per second. Defaults to the animation interval.
        dpi : float, optional
            Resolution of the saved frames. Unlike Matplotlib, which uses
            :rc:`savefig.dpi`, this defaults to the figure's own dpi. UltraPlot
            sets ``savefig.dpi`` to 1000 for publication-quality stills, which
            for a movie means hundredfold larger frames and a hundredfold
            slower encode.
        codec, bitrate, extra_args, metadata : optional
            Passed to the encoder, as in Matplotlib.
        extra_anim : list, optional
            Additional animations to composite. Forces the Matplotlib path.
        savefig_kwargs : dict, optional
            Extra `~matplotlib.figure.Figure.savefig` arguments. Any value here
            forces the Matplotlib path, since the fast path skips ``savefig``.
        progress_callback : callable, optional
            Called as ``progress_callback(current_frame, total_frames)``.
        fast : bool, optional
            Whether to use the fast renderer. The default, ``None``, uses it
            whenever it can reproduce the requested output exactly. Passing
            ``True`` raises if the fast path is unavailable.
        blit : bool, optional
            Whether to blit while saving. Defaults to the animation's own
            ``blit`` setting. Blitting only redraws the artists returned by the
            update function, so anything else changed per frame (titles, ticks,
            axes limits) will not appear. Pass ``False`` to redraw everything.

        Other Parameters
        ----------------
        See `matplotlib.animation.Animation.save`.

        See also
        --------
        matplotlib.animation.Animation.save
        """
        savefig_kwargs = savefig_kwargs or {}
        usable = self._can_fast_save(filename, writer, savefig_kwargs, extra_anim)
        if fast and not usable:
            raise ValueError(
                f"Cannot use the fast animation writer for {filename!r} with "
                f"writer={writer!r}. Pass fast=False to use matplotlib instead."
            )
        if not usable or fast is False:
            return super().save(
                filename,
                writer=writer,
                fps=fps,
                dpi=dpi,
                codec=codec,
                bitrate=bitrate,
                extra_args=extra_args,
                metadata=metadata,
                extra_anim=extra_anim,
                savefig_kwargs=savefig_kwargs or None,
                progress_callback=progress_callback,
            )

        if fps is None:
            fps = 1000.0 / getattr(self, "_interval", 200)
        # NOTE: Matplotlib defaults to rc['savefig.dpi'], but UltraPlot raises
        # that to 1000 for publication-quality stills. On a movie that means a
        # hundredfold more pixels in every frame, so default to the figure's
        # own dpi and let the caller ask for more.
        if dpi is None or dpi == "figure":
            dpi = self._fig.dpi
        if blit is None:
            blit = bool(getattr(self, "_blit", False))
        return self._fast_save(
            filename,
            fps,
            dpi,
            codec,
            bitrate,
            extra_args,
            metadata,
            progress_callback,
            blit,
        )


class FuncAnimation(_FastSaveMixin, manimation.FuncAnimation):
    """
    A faster drop-in replacement for `matplotlib.animation.FuncAnimation`.

    The signature matches Matplotlib's, with two differences: `blit` defaults
    to ``True`` instead of ``False``, and `freeze_layout` is added. Saving
    renders frames directly into the Agg buffer instead of calling
    `~matplotlib.figure.Figure.savefig` once per frame, which removes the
    per-frame PNG round-trip and the repeated UltraPlot tight-layout pass.

    Parameters
    ----------
    fig : `~ultraplot.figure.Figure`
        The figure to animate.
    func : callable
        The update function, called as ``func(frame, *fargs)``. It should
        return an iterable of the artists it modified. This is required when
        `blit` is ``True``, and lets the fast path skip untouched artists.
    frames : int, iterable, generator, or None, optional
        Source of frame data, as in Matplotlib.
    init_func : callable, optional
        Function drawing the clear frame. Should return the animated artists.
    fargs : tuple, optional
        Extra positional arguments for `func` and `init_func`.
    save_count : int, optional
        Number of frames to cache from a generator.
    blit : bool, default: True
        Whether to redraw only the artists returned by `func`. This is the main
        source of the speedup, but it means changes to artists that are *not*
        returned, such as titles or tick labels, will not show up. Pass
        ``False`` to redraw the whole figure each frame, which is still faster
        than Matplotlib because the layout solver is frozen.
    freeze_layout : bool, default: True
        Whether to run UltraPlot's tight-layout solver only for the first
        frame. Keeping it on avoids frames whose geometry jitters as labels
        change size.
    cache_frame_data : bool, default: True
        Whether to cache frame data, as in Matplotlib.
    **kwargs
        Passed to `matplotlib.animation.TimedAnimation`, e.g. `interval`,
        `repeat`, and `repeat_delay`.

    Examples
    --------
    >>> import ultraplot as uplt
    >>> import numpy as np
    >>> fig, ax = uplt.subplots()
    >>> x = np.linspace(0, 2 * np.pi, 200)
    >>> (line,) = ax.plot(x, np.sin(x))
    >>> def update(frame):
    ...     line.set_ydata(np.sin(x + frame / 10))
    ...     return (line,)
    ...
    >>> ani = uplt.FuncAnimation(fig, update, frames=100)
    >>> ani.save('waves.mp4')

    See also
    --------
    matplotlib.animation.FuncAnimation
    ultraplot.animation.ArtistAnimation
    ultraplot.animation.animate
    """

    def __init__(
        self,
        fig,
        func,
        frames=None,
        init_func=None,
        fargs=None,
        save_count=None,
        *,
        blit=True,
        freeze_layout=True,
        **kwargs,
    ):
        self._freeze_layout = bool(freeze_layout)
        super().__init__(
            fig,
            func,
            frames=frames,
            init_func=init_func,
            fargs=fargs,
            save_count=save_count,
            blit=blit,
            **kwargs,
        )

    def _fast_frame_seq(self):
        return self.new_saved_frame_seq()

    def _fast_init_artists(self, frame):
        if self._init_func is None:
            return self._func(frame, *self._args)
        return self._init_func()

    def _fast_frame_artists(self, frame):
        return self._func(frame, *self._args)


class ArtistAnimation(_FastSaveMixin, manimation.ArtistAnimation):
    """
    A faster drop-in replacement for `matplotlib.animation.ArtistAnimation`.

    Frames are lists of artists that are made visible in turn. Saving uses the
    same direct-to-buffer renderer as `FuncAnimation`.

    Parameters
    ----------
    fig : `~ultraplot.figure.Figure`
        The figure to animate.
    artists : list of list of `~matplotlib.artist.Artist`
        Each entry is the collection of artists making up one frame.
    freeze_layout : bool, default: True
        Whether to run UltraPlot's tight-layout solver only for the first
        frame.
    **kwargs
        Passed to `matplotlib.animation.TimedAnimation`.

    See also
    --------
    matplotlib.animation.ArtistAnimation
    ultraplot.animation.FuncAnimation
    """

    def __init__(self, fig, artists, *args, freeze_layout=True, **kwargs):
        self._freeze_layout = bool(freeze_layout)
        super().__init__(fig, artists, *args, **kwargs)

    def _fast_frame_seq(self):
        return iter(self._framedata)

    def _fast_init_artists(self, frame):
        # Hide every frame, then show the first one, exactly as the parent
        # class does when it initializes the animation.
        for other in self._framedata:
            for artist in other:
                artist.set_visible(False)
        return self._fast_frame_artists(frame)

    def _fast_frame_artists(self, frame):
        for other in self._framedata:
            for artist in other:
                artist.set_visible(False)
        for artist in frame:
            artist.set_visible(True)
        return list(frame)


def animate(fig, func, frames=None, /, *, save=None, **kwargs):
    """
    Build a `FuncAnimation`, optionally saving it in one call.

    This is a thin convenience wrapper. Everything it does can be done with
    `FuncAnimation` directly.

    Parameters
    ----------
    fig : `~ultraplot.figure.Figure`
        The figure to animate.
    func : callable
        The update function, called as ``func(frame)``. It should return the
        artists it changed.
    frames : int, iterable, generator, or None, optional
        Source of frame data.
    save : path-like, optional
        If given, the animation is saved here before being returned.
    **kwargs
        Passed to `FuncAnimation`, or to `FuncAnimation.save` for the
        save-specific keywords `fps`, `dpi`, `codec`, `bitrate`, `metadata`,
        and `progress_callback`.

    Returns
    -------
    FuncAnimation
        The animation. Keep a reference to it, or it will be garbage collected
        and stop updating.

    Examples
    --------
    >>> uplt.animate(fig, update, 100, save='movie.mp4', fps=30)

    See also
    --------
    ultraplot.animation.FuncAnimation
    """
    save_keys = ("fps", "dpi", "codec", "bitrate", "metadata", "progress_callback")
    save_kwargs = {key: kwargs.pop(key) for key in save_keys if key in kwargs}
    if save_kwargs and save is None:
        warnings._warn_ultraplot(
            f"Ignoring save keyword arguments {tuple(save_kwargs)} because no "
            "save location was passed."
        )
    ani = FuncAnimation(fig, func, frames, **kwargs)
    if save is not None:
        ani.save(save, **save_kwargs)
    return ani
