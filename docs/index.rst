.. notoc::
.. image:: _static/logo_long.png
   :align: center

**UltraPlot** is a succinct wrapper around `matplotlib <https://matplotlib.org/>`__
for creating **publication-quality graphics** with a small, familiar API.

Start with a finished figure
############################

The quickest way to get oriented is to make one complete figure, then explore
the concepts behind it. Follow the :doc:`first figure <first_figure>` walkthrough or browse
the :doc:`recipes` for focused examples.

.. admonition:: Coming from Matplotlib?
   :class: tip

   Compare the same figure side by side in the
   :doc:`Matplotlib comparison <why_ultraplot>` to see where UltraPlot adds
   convenience while keeping Matplotlib objects and conventions in view.

   :doc:`Make your first figure <first_figure>` ·
   :doc:`Compare with Matplotlib <why_ultraplot>`

Key features
############

Build polished figures with pragmatic defaults and familiar Matplotlib
objects. UltraPlot supports multi-panel layouts, Cartesian and geographic
plots, colorbars and legends, and data-aware plotting workflows.

**Get started** → :doc:`Installation guide <install>` |
:doc:`Why UltraPlot? <why_ultraplot>` | :doc:`Usage <usage>` |
:doc:`Gallery <gallery/index>`

Topics
######

.. grid:: 1 2 3 3
   :gutter: 2

   .. grid-item-card::
      :link: subplots.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Subplots & Layouts**
      ^^^

      .. image:: _static/example_plots/subplot_example.svg
         :align: center

      Create multi-panel layouts with shared axes and automatic spacing.

   .. grid-item-card::
      :link: cartesian.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Cartesian Plots**
      ^^^

      .. image:: _static/example_plots/cartesian_example.svg
         :align: center

      Format ordinary plots while retaining Matplotlib's plotting methods.

   .. grid-item-card::
      :link: colorbars_legends.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Colorbars & Legends**
      ^^^

      .. image:: _static/example_plots/colorbars_legends_example.svg
         :align: center

      Place and align guides across individual subplots or a whole figure.

   .. grid-item-card::
      :link: data_aware.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Data-aware plotting**
      ^^^

      .. image:: _static/example_plots/data_aware_example.svg
         :align: center

      Plot labelled pandas and xarray data with metadata-aware labels and
      coordinates.

   .. grid-item-card::
      :link: projections.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Projections & Maps**
      ^^^

      .. image:: _static/example_plots/projection_example.svg
         :align: center

      Explore geographic plotting when you need projections and map features.

   .. grid-item-card::
      :link: colormaps.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Colormaps & Styles**
      ^^^

      .. image:: _static/example_plots/colormaps_example.svg
         :align: center

      Choose and customize colormaps for clear, consistent visual encoding.

Reference & more
################

For details, see the full :doc:`User guide <usage>` and
:doc:`API Reference <api>`.

* :ref:`genindex`
* :ref:`modindex`
* :ref:`glossary`

.. toctree::
   :maxdepth: 1
   :caption: Getting started
   :hidden:

   install
   why_ultraplot
   first_figure
   usage
   recipes
   gallery/index

.. toctree::
   :maxdepth: 1
   :caption: Guides
   :hidden:

   basics
   subplots
   cartesian
   data_aware
   networks
   colorbars_legends
   colormaps
   1dplots
   2dplots

.. toctree::
   :maxdepth: 1
   :caption: Advanced guides
   :hidden:

   projections
   insets_panels
   stats
   configuration
   fonts
   cycles
   colors

.. toctree::
   :maxdepth: 1
   :caption: Reference
   :hidden:

   api
   keyword_aliases
   lazy_loading
   external-links
   faq
   whats_new
   contributing
   about

.. toctree::
   :maxdepth: 1
   :caption: Development
   :hidden:

   plot_comparison_results
