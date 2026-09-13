.. image:: https://raw.githubusercontent.com/Ultraplot/ultraplot/refs/heads/main/UltraPlotLogo.svg
    :alt: UltraPlot Logo
    :width: 100%

|downloads| |build-status| |coverage| |docs| |pypi| |code-style| |pre-commit| |pr-welcome| |license| |zenodo|

A succinct `matplotlib <https://matplotlib.org/>`__ wrapper for making beautiful,
publication-quality graphics. It builds upon ProPlot_ and transports it into the modern age (supporting mpl 3.9.0+).

.. _ProPlot: https://github.com/proplot-dev/

Why UltraPlot? | Write Less, Create More
=========================================
.. image:: https://raw.githubusercontent.com/Ultraplot/ultraplot/refs/heads/main/logo/whyUltraPlot.svg
    :width: 100%
    :alt: Comparison of ProPlot and UltraPlot
    :align: center

Checkout our examples
=====================

Below is a gallery showing random examples of what UltraPlot can do, for more examples checkout our extensive `docs <https://ultraplot.readthedocs.io>`_.
View the full gallery here: `Gallery <https://ultraplot.readthedocs.io/en/latest/gallery/index.html>`_.

.. list-table::
   :widths: 33 33 33
   :header-rows: 0

   * - .. image:: https://ultraplot.readthedocs.io/en/latest/_static/example_plots/subplot_example.svg
         :alt: Subplots & Layouts
         :target: https://ultraplot.readthedocs.io/en/latest/subplots.html
         :width: 100%
         :height: 200px

       **Subplots & Layouts**

       Create complex multi-panel layouts effortlessly.

     - .. image:: https://ultraplot.readthedocs.io/en/latest/_static/example_plots/cartesian_example.svg
         :alt: Cartesian Plots
         :target: https://ultraplot.readthedocs.io/en/latest/cartesian.html
         :width: 100%
         :height: 200px

       **Cartesian Plots**

       Easily generate clean, well-formatted plots.

     - .. image:: https://ultraplot.readthedocs.io/en/latest/_static/example_plots/projection_example.svg
         :alt: Projections & Maps
         :target: https://ultraplot.readthedocs.io/en/latest/projections.html
         :width: 100%
         :height: 200px

       **Projections & Maps**

       Built-in support for projections and geographic plots.

   * - .. image:: https://ultraplot.readthedocs.io/en/latest/_static/example_plots/colorbars_legends_example.svg
         :alt: Colorbars & Legends
         :target: https://ultraplot.readthedocs.io/en/latest/colorbars_legends.html
         :width: 100%
         :height: 200px

       **Colorbars & Legends**

       Customize legends and colorbars with ease.

     - .. image:: https://ultraplot.readthedocs.io/en/latest/_static/example_plots/panels_example.svg
         :alt: Insets & Panels
         :target: https://ultraplot.readthedocs.io/en/latest/insets_panels.html
         :width: 100%
         :height: 200px

       **Insets & Panels**

       Add inset plots and panel-based layouts.

     - .. image:: https://ultraplot.readthedocs.io/en/latest/_static/example_plots/colormaps_example.svg
         :alt: Colormaps & Cycles
         :target: https://ultraplot.readthedocs.io/en/latest/colormaps.html
         :width: 100%
         :height: 200px

       **Colormaps & Cycles**

       Visually appealing, perceptually uniform colormaps.


Documentation
=============

The documentation is `published on readthedocs <https://ultraplot.readthedocs.io>`__.

Installation
============

UltraPlot is published on `PyPi <https://pypi.org/project/ultraplot/>`__ and
`conda-forge <https://conda-forge.org>`__. It can be installed with ``pip`` or
``conda`` as follows:

.. code-block:: bash

   pip install ultraplot
   conda install -c conda-forge ultraplot

pyCirclize-based plots require the optional ``circos`` extra:

.. code-block:: bash

   pip install 'ultraplot[circos]'

The ``docs`` extra also includes pyCirclize for building the documentation.

To install the ``circos``, ``docs``, and ``stats`` dependency groups together:

.. code-block:: bash

   pip install 'ultraplot[all]'

Likewise, an existing installation of UltraPlot can be upgraded
to the latest version with:

.. code-block:: bash

   pip install --upgrade ultraplot
   conda upgrade ultraplot

To install a development version of UltraPlot, you can use
``pip install git+https://github.com/ultraplot/ultraplot.git``
or clone the repository and run ``pip install -e .``
inside the ``ultraplot`` folder.

MCP server
==========

UltraPlot includes a Model Context Protocol (MCP) server that lets AI assistants
search documentation and examples, inspect the live Python API, and read source
code and release notes.

Run directly with uvx
---------------------

With `uv <https://docs.astral.sh/uv/getting-started/installation/>`__ installed,
your MCP client can launch the server with ``uvx``. uv installs the package and
its dependencies in an isolated environment automatically, so you do not need
to create a virtual environment or install UltraPlot separately.

For a PyPI release containing the MCP server, the launch command is:

.. code-block:: bash

   uvx --from 'ultraplot[mcp]' ultraplot-mcp

For clients that use an ``mcpServers`` configuration, add:

.. code-block:: json

   {
     "mcpServers": {
       "ultraplot": {
         "command": "uvx",
         "args": ["--from", "ultraplot[mcp]", "ultraplot-mcp"]
       }
     }
   }

The client starts the server when needed and communicates with it over stdio.
Other clients may use a different configuration format; use the same command
and arguments. ``uvx`` is equivalent to ``uv tool run``.

Until the MCP server is released on PyPI, run it directly from the feature
branch instead:

.. code-block:: bash

   uvx --from 'ultraplot[mcp] @ git+https://github.com/ultraplot/ultraplot.git@feat/mcp' ultraplot-mcp

For this development version, replace ``ultraplot[mcp]`` in the client
configuration with
``ultraplot[mcp] @ git+https://github.com/ultraplot/ultraplot.git@feat/mcp``.

Install persistently with uv
----------------------------

Alternatively, keep the executable on your ``PATH`` by installing it as a uv
tool. For a PyPI release containing the MCP server:

.. code-block:: bash

   uv tool install 'ultraplot[mcp]'
   ultraplot-mcp --help

Before that release, install from the feature branch:

.. code-block:: bash

   uv tool install 'ultraplot[mcp] @ git+https://github.com/ultraplot/ultraplot.git@feat/mcp'

Then configure your client to launch ``ultraplot-mcp`` with no arguments.
If uv reports that its executable directory is missing from ``PATH``, run
``uv tool update-shell`` and restart your shell.

Install from a checkout
-----------------------

From a checkout containing the MCP implementation, install the optional ``mcp``
extra in the Python environment you want the server to use:

.. code-block:: bash

   pip install -e '.[mcp]'

Connect an MCP client
---------------------

After installing persistently with uv or pip, register the server with an
installed Codex CLI:

.. code-block:: bash

   ultraplot-mcp install codex

Restart Codex after registration. Try asking it to search the UltraPlot
examples for shared colorbars or inspect ``ultraplot.subplots``.

For other MCP clients, configure a stdio server with ``ultraplot-mcp`` as the
command and no arguments. Use the executable's absolute path if the client does
not inherit your Python environment's ``PATH``. Running ``ultraplot-mcp`` starts
the server; ``ultraplot-mcp --help`` lists the available commands.

Documentation tools read the checkout's ``docs`` directory. Direct uvx and uv
tool installations require a separate documentation checkout for these tools.
If documentation lives elsewhere, set ``ULTRAPLOT_MCP_DOCS`` to its absolute path in the MCP
client's server environment. Documentation is not currently bundled in the
Python package; API and source inspection use the installed UltraPlot version.

Citing UltraPlot
================

If you use UltraPlot in your research, please cite the latest release metadata in
``CITATION.cff``. GitHub can export this metadata as BibTeX from the
repository's "Cite this repository" panel, and the Zenodo badge below points to
the project DOI across releases.

.. |downloads| image:: https://static.pepy.tech/personalized-badge/UltraPlot?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads
    :target: https://pepy.tech/project/ultraplot
    :alt: Downloads

.. |build-status| image:: https://github.com/ultraplot/ultraplot/actions/workflows/test-map.yml/badge.svg
    :target: https://github.com/ultraplot/ultraplot/actions/workflows/test-map.yml
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/Ultraplot/ultraplot/graph/badge.svg?token=C6ZB7Q9II4&style=flat&color=53C334
    :target: https://codecov.io/gh/Ultraplot/ultraplot
    :alt: Coverage

.. |docs| image:: https://readthedocs.org/projects/ultraplot/badge/?version=latest&style=flat&color=4F5D95
    :target: https://ultraplot.readthedocs.io/en/latest/?badge=latest
    :alt: Docs

.. |pypi| image:: https://img.shields.io/pypi/v/ultraplot?style=flat&color=53C334&logo=pypi
    :target: https://pypi.org/project/ultraplot/
    :alt: PyPI

.. |code-style| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat&logo=python
    :alt: Code style: black

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/Ultraplot/ultraplot/main.svg
    :target: https://results.pre-commit.ci/latest/github/Ultraplot/ultraplot/main
    :alt: pre-commit.ci status

.. |pr-welcome| image:: https://img.shields.io/badge/PRs-welcome-f77f00?style=flat&logo=github
    :alt: PRs Welcome

.. |license| image:: https://img.shields.io/github/license/ultraplot/ultraplot.svg?style=flat&color=808080
    :target: LICENSE.txt
    :alt: License

.. |zenodo| image:: https://zenodo.org/badge/909651179.svg
    :target: https://doi.org/10.5281/zenodo.15733564
    :alt: DOI
