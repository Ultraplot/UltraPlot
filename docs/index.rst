.. notoc::
.. image:: _static/logo_long.png
   :align: center

**UltraPlot** is a succinct wrapper around `matplotlib <https://matplotlib.org/>`__
for creating **beautiful, publication-quality graphics** with ease.

Key Features
############
Build polished figures quickly with pragmatic defaults.
**Simplified Subplot Management** – Create multi-panel plots effortlessly.

**Smart Aesthetics** – Optimized colormaps, fonts, and styles out of the box.

**Versatile Plot Types** – Cartesian plots, insets, colormaps, and more.

**Get Started** → :doc:`Installation guide <install>` | :doc:`Why UltraPlot? <why>` | :doc:`Usage <usage>` | :doc:`Gallery <gallery/index>`

--------------------------------------

User Guide
##########
A preview of what UltraPlot can do. For more see the sidebar!

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

        Create complex multi-panel layouts effortlessly.

   .. grid-item-card::
        :link: cartesian.html
        :shadow: md
        :class-card: card-with-bottom-text

        **Cartesian Plots**
        ^^^

        .. image:: _static/example_plots/cartesian_example.svg
            :align: center

        .. container:: bottom-aligned-text

        Easily generate clean, well-formatted plots.

   .. grid-item-card::
        :link: projections.html
        :shadow: md
        :class-card: card-with-bottom-text

        **Projections & Maps**
        ^^^

        .. image:: _static/example_plots/projection_example.svg
            :align: center

        .. container:: bottom-aligned-text
        Built-in support for projections and geographic plots.

   .. grid-item-card::
        :link: colorbars_legends.html
        :shadow: md
        :class-card: card-with-bottom-text

        **Colorbars & Legends**
        ^^^

        .. image:: _static/example_plots/colorbars_legends_example.svg
            :align: center

        Customize legends and colorbars with ease.

   .. grid-item-card::
        :link: insets_panels.html
        :shadow: md
        :class-card: card-with-bottom-text

        **Insets & Panels**
        ^^^

        .. image:: _static/example_plots/panels_example.svg
            :align: center

        Add inset plots and panel-based layouts.

   .. grid-item-card::
      :link: colormaps.html
      :shadow: md
      :class-card: card-with-bottom-text

      **Colormaps & Cycles**
      ^^^

      .. image:: _static/example_plots/colormaps_example.svg
        :align: center

      Use prebuilt colormaps and define your own color cycles.

Reference & More
################
For more details, check the full :doc:`User guide <usage>` and :doc:`API Reference <api>`.

* :ref:`genindex`
* :ref:`modindex`
* :ref:`glossary`
.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   install
   why
   usage
   gallery/index

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   basics
   subplots
   cartesian
   networks
   projections
   colorbars_legends
   insets_panels
   1dplots
   2dplots
   stats
   colormaps
   cycles
   colors
   fonts
   configuration

.. toctree::
   :maxdepth: 1
   :caption: Reference
   :hidden:

   api
   lazy_loading
   external-links
   whats_new
   contributing
   about

.. toctree::
   :maxdepth: 1
   :caption: Dev Zone
   :hidden:

   plot_comparison_results
