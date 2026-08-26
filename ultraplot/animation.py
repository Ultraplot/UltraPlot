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
from contextlib import ExitStack, contextmanager, suppress
from tempfile import TemporaryFile
from pathlib import Path

import matplotlib as mpl
import matplotlib.animation as manimation
import numpy as np
from matplotlib import cbook

__all__ = [
    "FuncAnimation",
    "ArtistAnimation",
]

#: Containers written frame-by-frame by piping raw RGBA to ``ffmpeg``.
_FFMPEG_SUFFIXES = frozenset(
    (".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".ogv", ".ogg")
    + (".gif", ".webp", ".apng", ".avif")
)

#: Containers assembled in memory by Pillow.
_PILLOW_SUFFIXES = frozenset((".gif", ".webp", ".apng"))

#: Containers whose codec is implied by the extension, as in Matplotlib's
#: `~matplotlib.animation.FFMpegWriter.output_args`.
_SUFFIX_CODECS = frozenset((".gif", ".webp", ".apng", ".avif"))

#: Writer names whose behavior the fast path reproduces exactly. Anything else,
#: ``imagemagick`` included, is handed back to Matplotlib.
_FAST_WRITERS = frozenset(("ffmpeg", "pillow"))


def _suffix(filename):
    """
    Return the lowercase suffix of a path-like filename.
    """
    return Path(os.fspath(filename)).suffix.lower()


class _RawWriter:
    """
    Base class for writers that consume raw ``RGBA`` frames.

    Subclasses implement `write`, `_close`, and `_discard`. The output file is
    deleted unless `finish` completed, so an animation that fails halfway
    through never leaves a truncated movie that looks like a whole one.
    """

    def __init__(self, filename, fps):
        self.filename = os.fspath(filename)
        self.fps = fps
        self.width = self.height = None
        self._started = False
        self._finished = False

    def setup(self, width, height):
        self.width, self.height = width, height
        self._started = True

    def write(self, buffer):  # pragma: no cover - abstract
        raise NotImplementedError

    def _close(self):  # pragma: no cover - abstract
        raise NotImplementedError

    def _discard(self):
        pass

    def finish(self):
        """
        Complete the file. Anything short of this counts as a failed save.
        """
        self._close()
        self._finished = True

    def cleanup(self):
        """
        Release resources, and remove the output of an unfinished save.
        """
        self._discard()
        if self._started and not self._finished:
            with suppress(OSError):
                os.remove(self.filename)


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
        super().__init__(filename, fps)
        self.metadata = metadata or {}
        self.codec = codec or mpl.rcParams["animation.codec"]
        self.bitrate = mpl.rcParams["animation.bitrate"] if bitrate is None else bitrate
        self.extra_args = extra_args
        self._proc = None
        self._stderr = None

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
        extra = self.extra_args
        if extra is None:
            extra = mpl.rcParams["animation.ffmpeg_args"]
        extra = list(extra or ())

        # Codec selection mirrors matplotlib's FFMpegWriter: animated-image
        # containers take the codec implied by their extension, and only h264
        # and gif get the extra treatment they need to play back correctly.
        suffix = _suffix(self.filename)
        codec = suffix[1:] if suffix in _SUFFIX_CODECS else self.codec
        if suffix not in _SUFFIX_CODECS and codec:
            args += ["-vcodec", codec]
        if codec == "h264" and "-pix_fmt" not in extra:
            # Most players need 4:2:0 chroma and even dimensions. The scale is a
            # no-op when the frame is already even-sized.
            args += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-pix_fmt", "yuv420p"]
        elif codec == "gif" and "-filter_complex" not in extra:
            args += [
                "-filter_complex",
                "split [a][b];[a] palettegen [p];[b][p] paletteuse",
            ]
        if self.bitrate is not None and self.bitrate > 0:
            args += ["-b:v", f"{int(self.bitrate)}k"]
        for key, value in self.metadata.items():
            args += ["-metadata", f"{key}={value}"]
        args += extra
        args += [self.filename]
        return args

    def setup(self, width, height):
        super().setup(width, height)
        # NOTE: stderr goes to a file, not a pipe. Nothing reads the pipe while
        # frames are being written, so a chatty encoder would fill it and block.
        self._stderr = TemporaryFile()
        self._proc = subprocess.Popen(
            self._command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=self._stderr,
        )

    def _stderr_text(self):
        self._stderr.seek(0)
        return self._stderr.read().decode("utf-8", "replace")

    def write(self, buffer):
        try:
            self._proc.stdin.write(buffer)
        except BrokenPipeError as err:
            self._proc.wait()
            raise RuntimeError(
                "ffmpeg exited while frames were being written:\n" + self._stderr_text()
            ) from err

    def _close(self):
        self._proc.stdin.close()
        self._proc.wait()
        if self._proc.returncode:
            raise RuntimeError(
                f"ffmpeg exited with code {self._proc.returncode}:\n"
                + self._stderr_text()
            )

    def _discard(self):
        proc = self._proc
        if proc is not None and proc.returncode is None:
            try:
                if proc.stdin is not None and not proc.stdin.closed:
                    proc.stdin.close()
            finally:
                proc.kill()
                proc.wait()
        if self._stderr is not None:
            self._stderr.close()
            self._stderr = None


class _RawPillowWriter(_RawWriter):
    """
    Collect raw ``RGBA`` frames and write an animated image with Pillow.
    """

    def __init__(self, filename, fps):
        super().__init__(filename, fps)
        self._frames = []

    def write(self, buffer):
        from PIL import Image

        # Copy: the canvas hands back the same buffer for every frame.
        self._frames.append(
            Image.frombuffer(
                "RGBA", (self.width, self.height), bytes(buffer), "raw", "RGBA", 0, 1
            )
        )

    def _close(self):
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

    def _discard(self):
        self._frames.clear()


class _FastSaveMixin:
    """
    The fast `save` path, shared by the animation classes.

    Subclasses supply the three frame hooks below; everything else here is the
    machinery that renders those frames into a movie file.
    """

    # Frame hooks

    def _fast_frame_seq(self):  # pragma: no cover - abstract
        raise NotImplementedError

    def _fast_frame_artists(self, frame):  # pragma: no cover - abstract
        raise NotImplementedError

    def _fast_init_artists(self, frame):  # pragma: no cover - abstract
        raise NotImplementedError

    @contextmanager
    def _frozen_layout(self):
        """
        Run the UltraPlot layout solver once instead of once per frame.

        UltraPlot recomputes tight layout whenever the figure is marked dirty.
        During an animation the geometry must stay fixed anyway, or frames
        would jitter, so the solver is switched off after the first draw. Yields
        a function that marks the current layout as final.
        """
        fig = self._fig
        state = (
            getattr(fig, "_layout_initialized", False),
            getattr(fig, "_layout_dirty", False),
            getattr(fig, "_skip_autolayout", False),
        )

        def freeze():
            fig._layout_initialized = True
            fig._layout_dirty = False
            fig._skip_autolayout = True

        try:
            yield freeze
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
    def _suspended_figure_blitting(self):
        """
        Stand down the figure's own retained-draw machinery while saving.

        `~ultraplot.figure.Figure.savefig` does the same before printing. A live
        `~ultraplot._animation._BlitManager` keeps its artists flagged animated
        and repaints them from a ``draw_event`` handler, which would fight the
        frames drawn here.
        """
        fig = self._fig
        with ExitStack() as stack:
            selective = getattr(fig, "_selective_draw_manager", None)
            if selective is not None:
                stack.enter_context(selective.save_context())
            for manager in tuple(getattr(fig, "_blit_managers", ())):
                stack.enter_context(manager._save_context())
            yield

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

    def _resolve_writer(self, filename, writer, savefig_kwargs, extra_anim):
        """
        Return the name of the fast writer to use, or ``None`` for none.

        The fast path must pick the same writer Matplotlib would, or the same
        call would produce a differently encoded file than before.
        """
        if extra_anim:
            return None
        if writer is not None and not isinstance(writer, str):
            return None  # a configured writer instance must be honored
        if savefig_kwargs:
            # Any styling override (facecolor, transparency, bbox_inches, ...)
            # belongs to the savefig pipeline the fast path skips.
            return None
        # Matplotlib falls back to the rc setting when no writer is named.
        writer = writer or mpl.rcParams["animation.writer"]
        if writer not in _FAST_WRITERS:
            return None
        suffix = _suffix(filename)
        if writer == "ffmpeg":
            if suffix in _FFMPEG_SUFFIXES and _RawFFMpegWriter.available():
                return "ffmpeg"
            return None
        if suffix not in _PILLOW_SUFFIXES:
            return None
        try:
            import PIL  # noqa: F401
        except ImportError:
            return None
        return "pillow"

    def _make_raw_writer(
        self, filename, writer, fps, codec, bitrate, extra_args, metadata
    ):
        """
        Return the raw-frame writer for the resolved writer name.
        """
        if writer == "ffmpeg":
            return _RawFFMpegWriter(
                filename,
                fps,
                codec=codec,
                bitrate=bitrate,
                extra_args=extra_args,
                metadata=metadata,
            )
        return _RawPillowWriter(filename, fps)

    def _fast_save(
        self,
        filename,
        writer,
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
        raw = self._make_raw_writer(
            filename, writer, fps, codec, bitrate, extra_args, metadata
        )
        total = getattr(self, "_save_count", None)

        with ExitStack() as stack:
            # NOTE: `cleanup` is the only unconditional callback. `finish` runs
            # after the loop instead, so a failing update function does not
            # leave a truncated movie behind looking like a complete one.
            stack.callback(raw.cleanup)
            # The event source is suspended before the canvas is swapped, so
            # that its reconnect on the way out lands on the original canvas.
            stack.enter_context(self._suspended_event_source())
            canvas = stack.enter_context(self._agg_canvas())
            # NOTE: Matplotlib's own save sets canvas._is_saving, but that makes
            # `Axes.draw` include animated artists so that savefig captures
            # them. That would bake the first frame into the blitting
            # background. Suppress the timer-starting draw callback instead.
            stack.enter_context(cbook._setattr_cm(canvas, manager=None))
            stack.enter_context(self._suspended_figure_blitting())
            if dpi is not None and dpi != fig.dpi:
                stack.callback(fig.set_dpi, fig.dpi)
                fig.set_dpi(dpi)

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

            # The first draw runs tight layout; every later one reuses it.
            freeze_layout = stack.enter_context(self._frozen_layout())
            canvas.draw()
            freeze_layout()
            background = canvas.copy_from_bbox(fig.bbox) if blit else None

            height, width = np.asarray(canvas.buffer_rgba()).shape[:2]
            raw.setup(width, height)

            for count, frame in enumerate(frames):
                artists = self._fast_frame_artists(frame)
                if blit:
                    artists = sorted(
                        artists or init_artists, key=lambda a: a.get_zorder()
                    )
                    mark_animated(artists)
                    canvas.restore_region(background)
                    for artist in artists:
                        fig.draw_artist(artist)
                else:
                    freeze_layout()
                    canvas.draw()
                raw.write(memoryview(canvas.buffer_rgba()))
                if progress_callback is not None:
                    progress_callback(count, total)

            raw.finish()

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
        resolved = self._resolve_writer(filename, writer, savefig_kwargs, extra_anim)
        if fast and resolved is None:
            raise ValueError(
                f"Cannot use the fast animation writer for {filename!r} with "
                f"writer={writer!r}. Pass fast=False to use matplotlib instead."
            )
        if resolved is None or fast is False:
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
            resolved,
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
        **kwargs,
    ):
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
    **kwargs
        Passed to `matplotlib.animation.TimedAnimation`.

    See also
    --------
    matplotlib.animation.ArtistAnimation
    ultraplot.animation.FuncAnimation
    """

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
