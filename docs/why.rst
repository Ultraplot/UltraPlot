.. _cartopy: https://cartopy.readthedocs.io/stable/

.. _basemap: https://matplotlib.org/basemap/index.html

.. _seaborn: https://seaborn.pydata.org

.. _pandas: https://pandas.pydata.org

.. _xarray: http://xarray.pydata.org/en/stable/

.. _rainbow: https://doi.org/10.1175/BAMS-D-13-00155.1

.. _xkcd: https://blog.xkcd.com/2010/05/03/color-survey-results/

.. _opencolor: https://yeun.github.io/open-color/

.. _cmocean: https://matplotlib.org/cmocean/

.. _fabio: http://www.fabiocrameri.ch/colourmaps.php

.. _brewer: http://colorbrewer2.org/

.. _sciviscolor: https://sciviscolor.org/home/colormoves/

.. _matplotlib: https://matplotlib.org/stable/tutorials/colors/colormaps.html

.. _seacolor: https://seaborn.pydata.org/tutorial/color_palettes.html

.. _texgyre: https://frommindtotype.wordpress.com/2018/04/23/the-tex-gyre-font-family/

.. _why:

===============
Why UltraPlot?
===============

Matplotlib is an extremely versatile plotting package, but it is cumbersome
and repetitive for users who make complex figures with many subplots, finely
tune their annotations, or need new figures nearly every day. UltraPlot's core
mission is to smooth out the plotting experience for matplotlib's most demanding
users. It does this by *expanding upon* matplotlib's :ref:`object-oriented
interface <usage_background>` with changes that would be hard to justify inside
matplotlib itself.

The sections below pair the "before" -- a plain matplotlib result -- with the
"after" -- the same plot made with UltraPlot -- so you can see the difference at
a glance. For the full user guide, see the :ref:`usage introduction <usage>`
and the :ref:`user guide <ug_basics>`.

.. _why_less_typing:

Less typing, more plotting
==========================

In matplotlib, changing many plot settings at once means calling a series of
one-liner setter methods -- and it is often unclear whether a property lives on
the :class:`~matplotlib.axes.Axes`, the :class:`~matplotlib.axis.XAxis`,
a :class:`~matplotlib.spines.Spine`, or :func:`~matplotlib.axes.Axes.tick_params`.
UltraPlot replaces all of this with the :func:`~ultraplot.axes.Axes.format`
command: an expanded, thoroughly documented version of
:func:`~matplotlib.artist.Artist.update` that can also apply :ref:`rc settings
<why_rc>` and integrate with the :ref:`constructor functions <why_constructor>`.
The figure-level :func:`~ultraplot.figure.Figure.format` and
:func:`~ultraplot.gridspec.SubplotGrid.format` commands format several subplots
at once.

.. code-block:: python

   import ultraplot as uplt
   fig, axs = uplt.subplots(ncols=2)
   axs.format(color='gray', linewidth=1)
   axs.format(xlim=(0, 100), xticks=10, xtickminor=True, xlabel='foo', ylabel='bar')

is much more succinct than...

.. code-block:: python

   import matplotlib.pyplot as plt
   import matplotlib.ticker as mticker
   import matplotlib as mpl
   with mpl.rc_context(rc={'axes.linewidth': 1, 'axes.edgecolor': 'gray'}):
       fig, axs = plt.subplots(ncols=2, sharey=True)
       axs[0].set_ylabel('bar', color='gray')
       for ax in axs:
           ax.set_xlim(0, 100)
           ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
           ax.tick_params(width=1, color='gray', labelcolor='gray')
           ax.tick_params(axis='x', which='minor', bottom=True)
           ax.set_xlabel('foo', color='gray')

Links
-----

* For an introduction, see :ref:`this page <ug_format>`.
* For :class:`~ultraplot.axes.CartesianAxes` formatting,
  see :ref:`this page <ug_cartesian>`.
* For :class:`~ultraplot.axes.PolarAxes` formatting,
  see :ref:`this page <ug_polar>`.
* For :class:`~ultraplot.axes.GeoAxes` formatting,
  see :ref:`this page <ug_geoformat>`.

.. _why_constructor:

Class constructor functions
===========================

Matplotlib and `cartopy`_ define verbose class names like
:class:`~matplotlib.ticker.MultipleLocator` and
:class:`~cartopy.crs.LambertAzimuthalEqualArea`, and keep them out of the
top-level namespace. UltraPlot instead "registers" tick locators, tick
formatters, axis scales, property cycles, colormaps, normalizers, and cartopy
projections, so you can refer to them with constructor functions and short
names:

* A scalar passed to :class:`~ultraplot.constructor.Locator` returns a
  :class:`~matplotlib.ticker.MultipleLocator`; a list of strings passed to
  :class:`~ultraplot.constructor.Formatter` returns a
  :class:`~matplotlib.ticker.FixedFormatter`.
* :class:`~ultraplot.constructor.Colormap` and
  :class:`~ultraplot.constructor.Cycle` accept registered names, individual
  colors, and lists of colors.
* Every registered class is also available directly in the top-level namespace,
  e.g. ``uplt.MultipleLocator(...)`` or ``uplt.LogNorm(...)``.

The table below lists the constructor functions and the keyword arguments
that use them.

===============================  ============================================================  ==============================================================================  ================================================================================================================================================================================================
Function                          Return type                                                   Used by                                                                         Keyword argument(s)
===============================  ============================================================  ==============================================================================  ================================================================================================================================================================================================
:class:`~ultraplot.constructor.Proj`       :class:`~cartopy.crs.Projection` or :class:`~mpl_toolkits.basemap.Basemap`  :func:`~ultraplot.figure.Figure.add_subplot` and :func:`~ultraplot.figure.Figure.add_subplots`  ``proj=``
:class:`~ultraplot.constructor.Locator`    :class:`~matplotlib.ticker.Locator`                                  :func:`~ultraplot.axes.Axes.format` and :func:`~ultraplot.axes.Axes.colorbar`                   ``locator=``, ``xlocator=``, ``ylocator=``, ``minorlocator=``, ``xminorlocator=``, ``yminorlocator=``, ``ticks=``, ``xticks=``, ``yticks=``, ``minorticks=``, ``xminorticks=``, ``yminorticks=``
:class:`~ultraplot.constructor.Formatter`  :class:`~matplotlib.ticker.Formatter`                                :func:`~ultraplot.axes.Axes.format` and :func:`~ultraplot.axes.Axes.colorbar`                   ``formatter=``, ``xformatter=``, ``yformatter=``, ``ticklabels=``, ``xticklabels=``, ``yticklabels=``
:class:`~ultraplot.constructor.Scale`      :class:`~matplotlib.scale.ScaleBase`                                 :func:`~ultraplot.axes.Axes.format`                                                     ``xscale=``, ``yscale=``
:class:`~ultraplot.constructor.Colormap`   :class:`~matplotlib.colors.Colormap`                                 2D :class:`~ultraplot.axes.PlotAxes` commands                                            ``cmap=``
:class:`~ultraplot.constructor.Norm`       :class:`~matplotlib.colors.Normalize`                                2D :class:`~ultraplot.axes.PlotAxes` commands                                            ``norm=``
:class:`~ultraplot.constructor.Cycle`      :class:`~cycler.Cycler`                                              1D :class:`~ultraplot.axes.PlotAxes` commands                                            ``cycle=``
===============================  ============================================================  ==============================================================================  ================================================================================================================================================================================================

Links
-----

* For more on axes projections,
  see :ref:`this page <ug_proj>`.
* For more on axis locators,
  see :ref:`this page <ug_locators>`.
* For more on axis formatters,
  see :ref:`this page <ug_formatters>`.
* For more on axis scales,
  see :ref:`this page <ug_scales>`.
* For more on datetime locators and formatters,
  see :ref:`this page <ug_datetime>`.
* For more on colormaps,
  see :ref:`this page <ug_apply_cmap>`.
* For more on normalizers,
  see :ref:`this page <ug_apply_norm>`.
* For more on color cycles, see
  :ref:`this page <ug_apply_cycle>`.

.. _why_spacing:

Automatic dimensions and spacing
================================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/spacing_mpl.svg
         :alt: A 2x2 matplotlib figure where the bottom-row titles overlap the top-row tick labels
         :width: 100%

      The figure size is fixed, the margins are tuned by hand, and the bottom-row
      titles collide with the tick labels above them. Add a subplot or change the
      font size and the whole thing needs retuning.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/spacing_uplt.svg
         :alt: The same 2x2 layout made with UltraPlot with clean, automatic spacing
         :width: 100%

      UltraPlot fixes the physical dimensions of a *reference subplot* (``refwidth``,
      ``refheight``, ``refaspect``) instead of the figure, so subplot size -- and the
      apparent size of text -- stays constant no matter how many subplots you add.
      Its own tight layout algorithm then handles the spacing.

Links
-----

* For more on figure sizing, see :ref:`this page <ug_autosize>`.
* For more on subplot spacing, see :ref:`this page <ug_tight>`.

.. _why_redundant:

Working with multiple subplots
==============================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/subplots_mpl.svg
         :alt: A 2x2 matplotlib figure with repeated tick labels on every subplot and no subplot labels
         :width: 100%

      Every subplot repeats its own tick labels and axis labels, wasting page
      space. Adding "a-b-c" labels -- required for most publications -- is
      entirely manual.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/subplots_uplt.svg
         :alt: The same 2x2 layout made with UltraPlot with shared tick labels and a-b-c labels
         :width: 100%

      Tick labels and axis labels are shared and aligned automatically (``sharex``,
      ``sharey``, ``spanx``, ``spany``), and a-b-c labels are added with a single
      :rcraw:`abc` setting, e.g. ``axs.format(abc='A.')``.

Links
-----

* For more on axis sharing, see :ref:`this page <ug_share>`.
* For more on panels, see :ref:`this page <ug_panels>`.
* For more on colorbars and legends, see :ref:`this page <ug_guides>`.
* For more on a-b-c labels, see :ref:`this page <ug_abc>`.
* For more on subplot grids,  see :ref:`this page <ug_subplotgrid>`.

.. _why_colorbars_legends:

Simpler colorbars and legends
=============================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/colorbars_mpl.svg
         :alt: Two matplotlib panels where the colorbar steals space from its parent subplot, making the panels unequal widths
         :width: 100%

      Drawing a colorbar with ``fig.colorbar(m, ax=ax)`` *steals space* from the
      parent subplot -- here the left panel is visibly narrower than the right
      one. Outer legends have to be positioned by hand and tweaked to fit.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/colorbars_uplt.svg
         :alt: The same two panels with outer colorbars drawn in dedicated space, keeping the panels equal width
         :width: 100%

      Colorbars and legends get their own space in the
      :class:`~ultraplot.gridspec.GridSpec` -- the subplots keep their exact
      dimensions. Outer (``loc='l'``) and inset (``loc='ur'``) locations work for
      both, and colorbar widths are specified in physical units.

Links
-----

* For more on single-subplot colorbars and legends,
  see :ref:`this page <ug_guides_loc>`.
* For more on multi-subplot colorbars and legends,
  see :ref:`this page <ug_guides_multi>`.
* For new colorbar features,
  see :ref:`this page <ug_colorbars>`.
* For new legend features,
  see :ref:`this page <ug_legends>`.

.. _why_plotting:

Improved plotting commands
==========================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/plotting_mpl.svg
         :alt: A matplotlib line plot where the fill under the curve uses a single color for both positive and negative regions
         :width: 100%

      Filling under a curve means writing :func:`~matplotlib.axes.Axes.fill_between`
      yourself, and the obvious call paints the positive and negative regions the
      same color. Differentiating the sign requires ``where=`` bookkeeping by hand.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/plotting_uplt.svg
         :alt: The same data made with UltraPlot's area command, which colors positive regions blue and negative regions red
         :width: 100%

      ``ax.area(x, y, negpos=True)`` colors the positive and negative regions
      automatically. The :class:`~ultraplot.axes.PlotAxes` commands bundle many
      such `seaborn`_- and `xarray`_-style conveniences, including
      :ref:`standardized data arguments <ug_1dstd>`,
      :ref:`on-the-fly colorbars and legends <ug_guides_plot>`, and
      :ref:`error bars and shading <ug_errorbars>`.

Links
-----

* For the 1D plotting features,
  see :ref:`this page <ug_1dplots>`.
* For the 2D plotting features,
  see :ref:`this page <ug_2dplots>`.
* For treatment of 1D data arguments,
  see :ref:`this page <ug_1dstd>`.
* For treatment of 2D data arguments,
  see :ref:`this page <ug_2dstd>`.

.. _why_cartopy_basemap:

Cartopy and basemap integration
===============================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/geo_mpl.svg
         :alt: A cartopy map built by hand, with default gridlines and overlapping edge labels
         :width: 100%

      Building a map with `cartopy`_ or `basemap`_ means importing a separate
      package, configuring the projection, and adding gridlines and labels line
      by line. Longitude-latitude ("Plate Carrée") data has to be converted to
      map coordinates by hand.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/geo_uplt.svg
         :alt: The same map made with UltraPlot's GeoAxes, with clean labeled gridlines
         :width: 100%

      A geographic plot is ``uplt.subplots(proj='pcarree')``. The
      :class:`~ultraplot.axes.GeoAxes` subclass unifies `cartopy`_ and `basemap`_,
      defaults to longitude-latitude coordinates, and exposes gridlines, labels,
      coastlines, and borders through the same :func:`~ultraplot.axes.GeoAxes.format`
      command used elsewhere.

Links
-----

* For an introduction,
  see :ref:`this page <ug_geo>`.
* For more on cartopy and basemap as backends,
  see :ref:`this page <ug_backends>`.
* For plotting in :class:`~ultraplot.axes.GeoAxes`,
  see :ref:`this page <ug_geoplot>`.
* For formatting :class:`~ultraplot.axes.GeoAxes`,
  see :ref:`this page <ug_geoformat>`.
* For changing the :class:`~ultraplot.axes.GeoAxes` bounds,
  see :ref:`this page <ug_zoom>`.

.. _why_xarray_pandas:

Pandas and xarray integration
=============================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/metadata_mpl.svg
         :alt: A matplotlib plot of an xarray DataArray with no legend and generic axis labels
         :width: 100%

      Matplotlib treats a :class:`~xarray.DataArray` or :class:`~pandas.DataFrame`
      as a plain array and ignores its metadata -- so no legend, no title, and
      generic axis labels. Getting the metadata into the figure means switching to
      the ``.plot`` methods and learning a second syntax.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/metadata_uplt.svg
         :alt: The same DataArray plotted with UltraPlot, automatically labeled with its title, coordinates, and legend
         :width: 100%

      The same data plotted with UltraPlot is labeled automatically: the axis
      labels, subplot title, and colorbar and legend labels are all taken from the
      metadata. :class:`~pint.Quantity` units are handled too. Disable with
      ``autoformat=False``.

Links
-----

* For integration with 1D :class:`~ultraplot.axes.PlotAxes` commands,
  see :ref:`this page <ug_1dintegration>`.
* For integration with 2D :class:`~ultraplot.axes.PlotAxes` commands,
  see :ref:`this page <ug_2dintegration>`.
* For bar and area plots,
  see :ref:`this page <ug_bar>`.
* For diverging datasets,
  see :ref:`this page <ug_autonorm>`.
* For on-the-fly colorbars and legends,
  see :ref:`this page <ug_guides_plot>`.

.. _why_aesthetics:

Aesthetic colors and fonts
==========================

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card::
      :class-card: uplt-why uplt-why-mpl
      :text-align: center

      **Matplotlib**

      .. image:: _static/why_plots/aesthetics_mpl.svg
         :alt: A jet-colored matplotlib plot with the default DejaVu font
         :width: 100%

      "Misleading" colormaps like ``'jet'`` have jarring jumps in hue,
      saturation, and luminance that can trick the eye into seeing patterns that
      are not there (`rainbow`_). The default DejaVu font is functional but not
      particularly elegant.

   .. grid-item-card::
      :class-card: uplt-why uplt-why-uplt
      :text-align: center

      **UltraPlot**

      .. image:: _static/why_plots/aesthetics_uplt.svg
         :alt: The same field plotted with a perceptually uniform batlow colormap and the TeX Gyre font
         :width: 100%

      UltraPlot ships "perceptually uniform" colormaps from the `seaborn <seacolor_>`_,
      `cmocean <cmocean_>`_, `SciVisColor <sciviscolor_>`_, and
      `Scientific Colour Maps <fabio_>`_ projects (here, ``'batlow'``), plus the
      `TeX Gyre <texgyre_>`_ font series, the `open color <opencolor_>`_ palette,
      and filtered `XKCD color survey <xkcd_>`_ names.

Links
-----

* For more on colormaps,
  see :ref:`this page <ug_cmaps>`.
* For more on color cycles,
  see :ref:`this page <ug_cycles>`.
* For more on fonts,
  see :ref:`this page <ug_fonts>`.
* For importing custom colormaps, colors, and fonts,
  see :ref:`this page <why_dotUltraPlot>`.

.. _why_colormaps_cycles:

Manipulating colormaps
======================

Matplotlib implements colormaps with
:class:`~matplotlib.colors.LinearSegmentedColormap` and
:class:`~matplotlib.colors.ListedColormap`, which are cumbersome to modify or
create from scratch. UltraPlot makes colormaps and property cycles easy to
work with:

* All colormaps are replaced with the :class:`~ultraplot.colors.ContinuousColormap`
  and :class:`~ultraplot.colors.DiscreteColormap` subclasses, adding the features
  used by the :class:`~ultraplot.constructor.Colormap` and
  :class:`~ultraplot.constructor.Cycle` :ref:`constructor functions <why_constructor>`.
* :class:`~ultraplot.constructor.Colormap` can merge, truncate, and modify existing
  colormaps, or generate brand-new ones -- including
  :class:`~ultraplot.colors.PerceptualColormap`\ s with linear transitions in
  hue, saturation, and luminance rather than red, green, and blue.
* :class:`~ultraplot.constructor.Cycle` can build property cycles from scratch,
  from registered :class:`~ultraplot.colors.DiscreteColormap` instances, or by
  splitting up the colors from continuous colormaps.
* Colormap and cycle names are case-insensitive, and appending ``'_r'`` or ``'_s'``
  reverses or cyclically shifts them.

Links
-----

* For making new colormaps,
  see :ref:`this page <ug_cmaps_new>`.
* For making new color cycles,
  see :ref:`this page <ug_cycles_new>`.
* For merging colormaps and cycles,
  see :ref:`this page <ug_cmaps_merge>`.
* For modifying colormaps and cycles,
  see :ref:`this page <ug_cmaps_mod>`.

.. _why_norm:

Physical units engine
=====================

Matplotlib expresses margins in figure-relative units and spacing in
axes-relative units, so changing the figure size forces you to re-tune the
numbers. UltraPlot instead uses physical units everywhere:

* The :class:`~ultraplot.gridspec.GridSpec` keywords `left`, `right`, `top`,
  `bottom`, `wspace`, `hspace`, `pad`, `outerpad`, and `innerpad` accept physical
  units, defaulting to `em-widths` -- plot text is a useful "ruler" for spacing.
* The :class:`~ultraplot.figure.Figure` keywords `figsize`, `figwidth`,
  `figheight`, `refwidth`, and `refheight` accept arbitrary string units such as
  inches, centimeters, millimeters, pixels, `points`, and `picas` (see the
  :ref:`units table <units_table>`).
* This is powered by the :func:`~ultraplot.utils.units` engine, which also
  translates rc settings assigned to :func:`~ultraplot.config.rc_matplotlib` and
  :obj:`~ultraplot.config.rc_UltraPlot`.

Links
-----

* For more on physical units,
  see :ref:`this page <ug_units>`.
* For more on :class:`~ultraplot.gridspec.GridSpec` spacing units,
  see :ref:`this page <ug_tight>`
* For more on colorbar width units,
  see :ref:`this page <ug_colorbars>`,
* For more on panel width units,
  see :ref:`this page <ug_panels>`

.. _why_rc:

Flexible global settings
========================

In matplotlib, several :obj:`~matplotlib.rcParams` are only useful if changed
all at once -- like spine and label colors -- and they cannot be changed for
individual subplots. UltraPlot provides a single :obj:`~ultraplot.config.rc`
object for both native matplotlib settings
(:obj:`~ultraplot.config.rc_matplotlib`) and UltraPlot's own settings
(:obj:`~ultraplot.config.rc_UltraPlot`):

* Assigned settings are always validated, and "meta" settings like
  ``meta.edgecolor`` and ``meta.linewidth`` update many settings at once.
* Settings can be changed with ``uplt.rc.key = value``, ``uplt.rc[key] = value``,
  ``uplt.rc.update(key=value)``, :func:`~ultraplot.axes.Axes.format`, or the
  :func:`~ultraplot.config.Configurator.context` context manager.
* Settings changed during a session can be saved with
  :func:`~ultraplot.config.Configurator.save` and loaded with
  :func:`~ultraplot.config.Configurator.load`.

Links
-----

* For an introduction,
  see :ref:`this page <ug_rc>`.
* For more on changing settings,
  see :ref:`this page <ug_config>`.
* For more on UltraPlot settings,
  see :ref:`this page <ug_rcUltraPlot>`.
* For more on meta settings,
  see :ref:`this page <ug_rcmeta>`.
* For a table of the new settings,
  see :ref:`this page <ug_rctable>`.

.. _why_dotUltraPlot:

Loading stuff
=============

Matplotlib makes persistent configuration awkward, and there is no built-in way
to register your own colormaps, color cycles, or fonts. UltraPlot turns this
into dropping files into folders:

* Edit the default ``ultraplotrc`` file (usually ``$HOME/.ultraplot/ultraplotrc``)
  or add loose ``ultraplotrc`` files to the current directory or a parent
  directory to change settings persistently.
* Colormaps, color cycles, colors, and fonts stored in subfolders named
  ``cmaps``, ``cycles``, ``colors``, and ``fonts`` inside
  :func:`~ultraplot.config.Configurator.user_folder` (usually
  ``$HOME/.ultraplot``) are registered automatically -- as are loose
  ``ultraplot_cmaps``, ``ultraplot_cycles``, ``ultraplot_colors``, and
  ``ultraplot_fonts`` folders in the current or a parent directory.
* Pass ``save=True`` to :class:`~ultraplot.constructor.Colormap` and
  :class:`~ultraplot.constructor.Cycle` to save new colormaps and cycles, or use
  :func:`~ultraplot.config.register_cmaps`,
  :func:`~ultraplot.config.register_cycles`,
  :func:`~ultraplot.config.register_colors`, and
  :func:`~ultraplot.config.register_fonts` to register arbitrary inputs during
  a session.

Links
-----

* For the ``ultraplotrc`` file,
  see :ref:`this page <ug_ultraplotrc>`.
* For registering colormaps,
  see :ref:`this page <ug_cmaps_dl>`.
* For registering color cycles,
  see :ref:`this page <ug_cycles_dl>`.
* For registering colors,
  see :ref:`this page <ug_colors_user>`.
* For registering fonts,
  see :ref:`this page <ug_fonts_user>`.
