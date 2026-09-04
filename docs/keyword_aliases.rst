Keyword vocabulary
==================

UltraPlot accepts a broad set of keyword spellings so existing Matplotlib and
older UltraPlot code continues to work. New users only need a small canonical
front door. The table below is the vocabulary used throughout the beginner
recipes; aliases remain supported, but we do not teach every alias in every
example.

Canonical names and supported aliases
-------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 22 34 44

   * - Area
     - Canonical
     - Also supported
   * - Layout
     - ``refwidth``, ``refheight``, ``refaspect``
     - ``axwidth``, ``axheight``, ``aspect``
   * - Layout
     - ``figwidth``, ``figheight``, ``wratios``, ``hratios``
     - ``width``, ``height``, ``width_ratios``, ``height_ratios``
   * - Plot styling
     - ``linewidth``, ``color``
     - ``lw``, ``linewidths``, ``c``, ``colors``
   * - Panel geometry
     - ``span``
     - ``row``, ``rows``, ``col``, ``cols``
   * - Shared axes
     - ``sharex``, ``sharey``
     - ``share`` (sets both)
   * - Figure
     - ``suptitle``
     - ``figtitle``
   * - Guides
     - ``loc``, ``ncols``
     - ``location``, ``ncol``
   * - Export
     - ``fig.save(...)``
     - ``fig.savefig(...)``

Prefer the canonical column when starting new code. This is a documentation
choice only: this page does not change runtime behavior or deprecate aliases.

See :doc:`recipes` for short, copyable figures using this vocabulary and the
full API reference for the complete keyword signatures.
