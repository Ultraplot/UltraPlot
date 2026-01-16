.. _whats_new:

What's new?
===========

v1.70.0: 🚀 UltraPlot v1.70.0: Smart Layouts, Better Maps, and Scientific Publishing Support (2026-01-04)
--------------------------------------------------------------------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html


**High-Level Overview:** This release focuses on intelligent layout management, geographic plotting enhancements, and publication-ready features.  Geographic plots receive improved boundary label handling and rotation capabilities, while new Copernicus Publications standard widths support scientific publishing workflows. Various bug fixes and documentation improvements round out this release.

Major Changes:
""""""""""""""

1. **Geographic Plot Enhancements**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:raw-html-m2r:`<img width="581" height="358" alt="image" src="https://github.com/user-attachments/assets/66636042-6e76-44b7-8e61-c846e66e2365" />`

.. code-block:: python

   # Improved boundary labels and rotation
   fig, ax = uplt.subplots(projection="cyl")
   ax.format(
       lonlim=(-180, 180),
       latlim=(-90, 90),
       lonlabelrotation=45, # new parameter
       labels=True,
       land=True,
   )
   # Boundary labels now remain visible and can be rotated

2. **Copernicus Publications Support**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # New standard figure widths for scientific publishing
   fig = uplt.figure(journal = "cop1")
   # Automatically sets appropriate width for Copernicus Publications

3. **Legend Placement Improvements**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:raw-html-m2r:`<img width="5633" height="6087" alt="test" src="https://github.com/user-attachments/assets/f5dba560-85e7-421d-9dc4-edba97974dc7" />`

.. code-block:: python

   import numpy as np

   import ultraplot as uplt

   np.random.seed(0)
   fig, ax = uplt.subplots(ncols=2, nrows=2)
   handles = []
   for idx, axi in enumerate(ax):
       noise = np.random.randn(100) * idx
       angle = np.random.rand() * 2 * np.pi
       t = np.linspace(0, 2 * np.pi, noise.size)
       y = np.sin(t * angle) + noise[1]
       (h,) = axi.plot(t, y, label=f"$f_{idx}$")
       handles.append(h)

   # New: spanning legends
   fig.legend(handles=handles, ax=ax[0, :], span=(1, 2), loc="b")
   fig.show()

What's Changed
~~~~~~~~~~~~~~


* Bump actions/checkout from 5 to 6 in the github-actions group by @dependabot[bot] in https://github.com/Ultraplot/UltraPlot/pull/415
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/Ultraplot/UltraPlot/pull/416
* Add placement of legend to axes within a figure (https://github.com/Ultraplot/UltraPlot/pull/418)
* There's a typo about zerotrim in doc. (https://github.com/Ultraplot/UltraPlot/pull/420)
* Fix references in documentation for clarity (https://github.com/Ultraplot/UltraPlot/pull/421)
* fix links to apply_norm (https://github.com/Ultraplot/UltraPlot/pull/423)
* [Feature] add lon lat labelrotation (https://github.com/Ultraplot/UltraPlot/pull/426)
* Fix: Boundary labels now visible when setting lonlim/latlim (https://github.com/Ultraplot/UltraPlot/pull/429)
* Add Copernicus Publications figure standard widths (https://github.com/Ultraplot/UltraPlot/pull/433)
* Fix 2D indexing for gridpec (https://github.com/Ultraplot/UltraPlot/pull/435)
* Fix GeoAxes panel alignment with aspect-constrained projections (https://github.com/Ultraplot/UltraPlot/pull/432)
* Bump the github-actions group with 2 updates by @dependabot[bot] in https://github.com/Ultraplot/UltraPlot/pull/444
* Fix dualx alignment on log axes (https://github.com/Ultraplot/UltraPlot/pull/443)
* Subset label sharing and implicit slice labels for axis groups (https://github.com/Ultraplot/UltraPlot/pull/440)
* Preserve log formatter when setting log scales (https://github.com/Ultraplot/UltraPlot/pull/437)
* Feature: added inference of labels for spanning legends (https://github.com/Ultraplot/UltraPlot/pull/447)

New Contributors
~~~~~~~~~~~~~~~~


* @gepcel made their first contribution in https://github.com/Ultraplot/UltraPlot/pull/420
* @Holmgren825 made their first contribution in https://github.com/Ultraplot/UltraPlot/pull/433

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.66.0...v1.70.0

v1.66.0: New feature: External Contexts, and bug splats 🐛 (2025-11-22)
----------------------------------------------------------------------

Release Notes
-------------

This release introduces two key improvements to enhance compatibility and consistency.

External Contexts
~~~~~~~~~~~~~~~~~

UltraPlot provides sensible defaults by controlling matplotlib's internal mechanics and applying overrides when needed. While this approach works well in isolation, it can create conflicts when integrating with external libraries.

We've introduced a new ``external`` context that disables UltraPlot-specific features when working with third-party libraries. Currently, this context prevents conflicts with internally generated labels in Seaborn plots. We plan to extend this functionality to support broader library compatibility in future releases.

**Example usage with Seaborn:**

.. code-block:: python

   import seaborn as sns
   import ultraplot as uplt

   # Load example dataset
   tips = sns.load_dataset("tips")

   # Use external context to avoid label conflicts
   fig, ax = uplt.subplots()
   with ax.external():
       sns.lineplot(data=tips, x="size", y="total_bill", hue="day", ax = ax)

Standardized Binning Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We've standardized the default aggregation function across all binning operations to use ``sum``. This change affects ``hexbin``\ , which previously defaulted to averaging values. All binning functions now consistently use ``sum`` as the default, though you can specify any custom aggregation function via the ``reduce_C_function`` parameter.

What's Changed
~~~~~~~~~~~~~~


* Hotfix: unsharing causes excessive draw in jupyter (https://github.com/Ultraplot/UltraPlot/pull/411)
* Hotfix: bar labels cause limit to reset for unaffected axis. (https://github.com/Ultraplot/UltraPlot/pull/413)
* fix: change default ``reduce_C_function`` to ``np.sum`` for ``hexbin`` (https://github.com/Ultraplot/UltraPlot/pull/408)
* Add external context mode for axes (https://github.com/Ultraplot/UltraPlot/pull/406)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.65.1...v1.66.0

v1.65.1: Hot-fix: add minor issue where boxpct was not parsed properly (2025-11-02)
-----------------------------------------------------------------------------------

What's Changed
~~~~~~~~~~~~~~


* Bump the github-actions group with 2 updates by @dependabot[bot] in https://github.com/Ultraplot/UltraPlot/pull/398
* Fix missing s on input parsing for boxpercentiles (https://github.com/Ultraplot/UltraPlot/pull/400)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.65.0...v1.65.1

v1.65.0: Enhanced Grid Layouts and Multi-Span Colorbars (2025-10-31)
--------------------------------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html


:art: UltraPlot v1.65 release notes
-----------------------------------

This release introduces substantial improvements to subplot layout flexibility and configuration management for scientific visualization.

Key Features
~~~~~~~~~~~~

**Non-Rectangular Grid Layouts with Side Labels** (\ `#376 <https://github.com/Ultraplot/UltraPlot/pull/376>`_\ )\ :raw-html-m2r:`<br>`
Asymmetric subplot arrangements now support proper axis labeling, enabling complex multi-panel figures without manual positioning workarounds.

**Multi-Span Colorbars** (\ `#394 <https://github.com/Ultraplot/UltraPlot/pull/394>`_\ )\ :raw-html-m2r:`<br>`
Colorbars can span multiple subplots, eliminating redundant color scales in comparative visualizations.

**RC-Configurable Color Cycles** (\ `#378 <https://github.com/Ultraplot/UltraPlot/pull/378>`_\ )\ :raw-html-m2r:`<br>`
Cycle objects can be set via rc configuration, enabling consistent color schemes across figures and projects.

**Improved Label Sharing** (\ `#372 <https://github.com/Ultraplot/UltraPlot/pull/372>`_\ , `#387 <https://github.com/Ultraplot/UltraPlot/pull/387>`_\ )\ :raw-html-m2r:`<br>`
Enhanced logic for axis label sharing in complex grid configurations with expanded test coverage.

Infrastructure
~~~~~~~~~~~~~~


* Automatic version checking (\ `#377 <https://github.com/Ultraplot/UltraPlot/pull/377>`_\ ). Users can now get informed when a new version is available by setting ``uplt.rc["ultraplot.check_for_latest_version"] = True`` which will drop a warning if a newer version is available.
* Demo gallery unit tests (\ `#386 <https://github.com/Ultraplot/UltraPlot/pull/386>`_\ )
* Optimized CI/CD workflow (\ `#388 <https://github.com/Ultraplot/UltraPlot/pull/388>`_\ , `#389 <https://github.com/Ultraplot/UltraPlot/pull/389>`_\ , `#390 <https://github.com/Ultraplot/UltraPlot/pull/390>`_\ , `#391 <https://github.com/Ultraplot/UltraPlot/pull/391>`_\ )

Impact
~~~~~~

These changes address common pain points in creating publication-quality multi-panel figures, particularly for comparative analyses requiring consistent styling and efficient use of figure space.

What's Changed
~~~~~~~~~~~~~~


* Allow non-rectangular grids to use side labels (https://github.com/Ultraplot/UltraPlot/pull/376)
* Test/update label sharing tests (https://github.com/Ultraplot/UltraPlot/pull/372)
* Add version checker for UltraPlot (https://github.com/Ultraplot/UltraPlot/pull/377)
* Feature: allow cycle objects to be set on rc (https://github.com/Ultraplot/UltraPlot/pull/378)
* Add unittest for demos (https://github.com/Ultraplot/UltraPlot/pull/386)
* Increase timeout on GHA (https://github.com/Ultraplot/UltraPlot/pull/388)
* bump to 60 minutes (https://github.com/Ultraplot/UltraPlot/pull/389)
* Skip test_demos on gha (https://github.com/Ultraplot/UltraPlot/pull/391)
* Hotfix: minor update in sharing logic (https://github.com/Ultraplot/UltraPlot/pull/387)
* Housekeeping for ``ultraplot-build.yml`` (https://github.com/Ultraplot/UltraPlot/pull/390)
* Feature: Allow multi-span colorbars (https://github.com/Ultraplot/UltraPlot/pull/394)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.63.0...v1.65.0

v1.63.0: 🌀  New Feature: Curved Quiver (2025-10-14)
---------------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html


This release introduces ``curved_quiver``\ , a new plotting primitive that renders compact, curved arrows following the local direction of a vector field. It’s designed to bridge the gap between ``quiver`` (straight, local glyphs) and ``streamplot`` (continuous, global trajectories): you retain the discrete arrow semantics of ``quiver``\ , but you gain local curvature that more faithfully communicates directional change.

:raw-html-m2r:`<img width="7204" height="2554" alt="streamplot_quiver_curvedquiver" src="https://github.com/user-attachments/assets/6a5bf04a-6fe7-48bc-8f83-b12fd0490ed3" />`

What it does
------------

Under the hood, the implementation follows the same robust foundations as ``matplotlib``\ ’s streamplot, adapted to generate short, curved arrow segments instead of full streamlines.  As such it can be seen as in between ``streamplot`` and ``quiver`` plots, see figure below and above.

:raw-html-m2r:`<img width="7204" height="5335" alt="curved_quiver_comparison" src="https://github.com/user-attachments/assets/0e6d3ac3-d229-45de-a0e4-b3b31393e876" />`

The core types live in ``ultraplot/axes/plot_types/curved_quiver.py`` and are centered on ``CurvedQuiverSolver``\ , which coordinates grid/coordinate mapping, seed point generation, trajectory integration, and spacing control:


* 
  ``_CurvedQuiverGrid`` validates and models the input grid. It ensures the x grid is rectilinear with equal rows and the y grid with equal columns, computes ``dx``\ /\ ``dy``\ , and exposes grid shape and extent. This means ``curved_quiver`` is designed for rectilinear grids where rows/columns of ``x``\ /\ ``y`` are consistent, matching the expectations of stream/line-based vector plotting.

* 
  ``_DomainMap`` maintains transformations among data-, grid-, and mask-coordinates. Velocity components are rescaled into grid-coordinates for integration, and speed is normalized to axes-coordinates so that step sizes and error metrics align with the visual output (this is important for smooth curves at different figure sizes and grid densities). It also owns bookkeeping for the spacing mask.

* 
  ``_StreamMask`` enforces spacing between trajectories at a coarse mask resolution, much like ``streamplot`` spacing. As a trajectory advances, the mask is filled where the curve passes, preventing new trajectories from entering already-occupied cells. This avoids over-plotting and stabilizes density in a way that feels consistent with ``streamplot`` output while still generating discrete arrows.

* 
  Integration is handled by a second-order *Runge–Kutta* method with adaptive step sizing, implemented in ``CurvedQuiverSolver.integrate_rk12``. This “improved Euler” approach is chosen for a balance of speed and visual smoothness. It uses an error metric in axes-coordinates to adapt the step size ``ds``. A maximum step (\ ``maxds``\ ) is also enforced to prevent skipping mask cells. The integration proceeds forward from each seed point, terminating when any of the following hold: the curve exits the domain, an intermediate integration step would go out of bounds (in which case a single Euler step to the boundary is taken for neatness), a local zero-speed region is detected, or the path reaches the target arc length set by the visual resolution. Internally, that arc length is bounded by a threshold proportional to the mean of the sampled magnitudes along the curve, which is how ``scale`` effectively maps to a “how far to bend” control in physical units.

* 
  Seed points are generated uniformly over the data extent via ``CurvedQuiverSolver.gen_starting_points``\ , using ``grains × grains`` positions. Increasing ``grains`` increases the number of potential arrow locations and produces smoother paths because more micro-steps are used to sample curvature. During integration, the solver marks the mask progressively via ``_DomainMap.update_trajectory``\ , and very short trajectories are rejected with ``_DomainMap.undo_trajectory()`` to avoid clutter.

* 
  The final artist returned to you is a ``CurvedQuiverSet`` (a small dataclass aligned with ``matplotlib.streamplot.StreamplotSet``\ ) exposing ``lines`` (the curved paths) and ``arrows`` (the arrowheads). This mirrors familiar ``streamplot`` ergonomics. For example, you can attach a colorbar to ``.lines``\ , as shown in the figures.

From a user perspective, you call ``ax.curved_quiver(X, Y, U, V, ...)`` just as you would ``quiver``\ , optionally passing ``color`` as a scalar field to map magnitude, ``cmap`` for color mapping, ``arrow_at_end=True`` and ``arrowsize`` to emphasize direction, and the two most impactful shape controls: ``grains`` and ``scale``. Use ``curved_quiver`` when you want to reveal local turning behavior—vortices, shear zones, near saddles, or flow deflection around obstacles—without committing to global streamlines. If your field is highly curved in localized pockets where straight arrows are misleading but ``streamplot`` feels too continuous or dense, ``curved_quiver`` is the right middle ground.

Performance
-----------

Performance-wise, runtime scales with the number of glyphs and the micro-steps (\ ``grains``\ ). The default values are a good balance for most grids; for very dense fields, you can either reduce ``grains`` or down-sample the input grid. The API is fully additive and doesn’t introduce any breaking changes, and it integrates with existing colorbar and colormap workflows.

Parameters
----------

There are two main parameters that affect the plots visually. The ``grains``\ parameters controls the density of the grid by interpolating between the input grid. Setting a higher grid will fill the space with more streams. See for a full function description the `documentation <https://ultraplot.readthedocs.io/en/latest/api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.curved_quiver>`_.

:raw-html-m2r:`<img width="7204" height="2801" alt="curved_quiver_grains" src="https://github.com/user-attachments/assets/e25c3ade-304b-4146-95a7-e5715e4823fc" />`

The ``size`` parameter will multiply the magnitude of the stream. Setting this value higher will make it look more similar to ``streamplot``.

:raw-html-m2r:`<img width="7204" height="2801" alt="curved_quiver_sizes" src="https://github.com/user-attachments/assets/19b952c9-503f-4c8f-b83a-b8ea98737200" />`

Acknowledgements
----------------

Special thanks to @veenstrajelmer for his implementation (https://github.com/Deltares/dfm_tools) and @Yefee for his suggestion to add this to UltraPlot! And as always @beckermr  for his review.

What's Changed
~~~~~~~~~~~~~~


* Add ``curved_quiver`` — Curved Vector Field Arrows for 2D Plots (https://github.com/Ultraplot/UltraPlot/pull/361)
* Add Colormap parsing to curved-quiver (https://github.com/Ultraplot/UltraPlot/pull/369)

Suggestions or feedback
-----------------------

Do you have suggestion or feedback? Checkout our `discussion <https://github.com/Ultraplot/UltraPlot/discussions>`_ on this release.

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.62.0...v1.63.0

v1.62.0: 🚀 New Release: Configurator Handler Registration (2025-10-13)
----------------------------------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html


This release introduces a powerful **extension point** to the configuration system — ``Configurator.register_handler()`` — enabling dynamic responses to configuration changes.

✨ New Feature: ``register_handler``
""""""""""""""""""""""""""""""""""""""""

You can now register custom handlers that execute automatically when specific settings are modified.\ :raw-html-m2r:`<br>`
This is particularly useful for settings that require **derived logic or side-effects**\ , such as updating related Matplotlib parameters.

.. code-block:: python

   register_handler(name: str, func: Callable[[Any], Dict[str, Any]]) -> None
   `

**Example (enabled by default):**

.. code-block:: python

   def _cycle_handler(value):
       # Custom logic to create a cycler object from the value
       return {'axes.prop_cycle': new_cycler}

   rc.register_handler('cycle', _cycle_handler)

Each handler function receives the **new value** of the setting and must return a **dictionary** mapping valid Matplotlib rc keys to their corresponding values. These updates are applied automatically to the runtime configuration.

----

🧩 Why It Matters
"""""""""""""""""

This addition:


* Fixes an issue where ``cycle:`` entries in ``ultraplotrc`` were not properly applied.
* Decouples configuration logic from Matplotlib internals.
* Provides a clean mechanism for extending the configuration system with custom logic — without circular imports or hard-coded dependencies.

----

🔧 Internal Improvements
""""""""""""""""""""""""


* Refactored configuration update flow to support handler callbacks.
* Simplified ``rc`` management by delegating side-effectful updates to registered handlers.

----

💡 Developer Note
"""""""""""""""""

This API is designed to be extensible. Future handlers may include dynamic color normalization, font synchronization, or interactive theme updates — all powered through the same mechanism.

v1.61.1: 🚀 Release: CFTime Support and Integration (2025-10-08)
---------------------------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html


Highlights
""""""""""

**CFTime Axis Support:**\ :raw-html-m2r:`<br>`
We’ve added robust support for CFTime objects throughout ``ultraplot``. This enables accurate plotting and formatting of time axes using non-standard calendars (e.g., ``noleap``\ , ``gregorian``\ , ``standard``\ ), which are common in climate and geoscience datasets.

**Automatic Formatter and Locator Selection:**\ :raw-html-m2r:`<br>`
``ultraplot`` now automatically detects CFTime axes and applies the appropriate formatters and locators, ensuring correct tick placement and labeling for all supported calendar types.

**Seamless Integration with xarray:**\ :raw-html-m2r:`<br>`
These features are designed for direct use with ``xarray`` datasets and dataarrays. When plotting data with CFTime indexes, ``ultraplot`` will handle all time axis formatting and tick generation automatically—no manual configuration required.

----

Intended Use
""""""""""""

This release is aimed at users working with climate, weather, and geoscience data, where time coordinates may use non-standard calendars. The new CFTime functionality ensures that plots generated from ``xarray`` and other scientific libraries display time axes correctly, regardless of calendar type.

----

Example Usage
"""""""""""""

.. code-block:: python

   import xarray as xr
   import numpy as np
   import cftime
   import ultraplot as uplt

   # Create a sample xarray DataArray with CFTime index
   times = [cftime.DatetimeNoLeap(2001, 1, i+1) for i in range(10)]
   data = xr.DataArray(np.random.rand(10), coords=[times], dims=["time"])

   fig, ax = uplt.subplots()
   data.plot(ax=ax)

   # CFTime axes are automatically formatted and labeled
   ax.set_title("CFTime-aware plotting with ultraplot")
   uplt.show()

----

Migration and Compatibility
"""""""""""""""""""""""""""


* No changes are required for existing code using standard datetime axes.
* For datasets with CFTime indexes (e.g., from ``xarray``\ ), simply plot as usual—\ ``ultraplot`` will handle the rest.

----

**We welcome feedback and bug reports as you explore these new capabilities!**

What's Changed
~~~~~~~~~~~~~~


* Fix edgecolor not set on scatter plots with single-row DataFrame data (https://github.com/Ultraplot/UltraPlot/pull/325)
* Add suptitle_kw alignment support to UltraPlot (https://github.com/Ultraplot/UltraPlot/pull/327)
* Update Documentation for ``abc`` Parameter in Subplots and Format Command (https://github.com/Ultraplot/UltraPlot/pull/328)
* Fix subplots docs  (https://github.com/Ultraplot/UltraPlot/pull/330)
* Add members to api (https://github.com/Ultraplot/UltraPlot/pull/332)
* rm show from tests (https://github.com/Ultraplot/UltraPlot/pull/335)
* Revert "Fix edge case where vcenter is not properly set for diverging norms" (https://github.com/Ultraplot/UltraPlot/pull/337)
* Bump the github-actions group with 2 updates by @dependabot[bot] in https://github.com/Ultraplot/UltraPlot/pull/339
* Extra tests for geobackends (https://github.com/Ultraplot/UltraPlot/pull/334)
* Fix some links for docs (https://github.com/Ultraplot/UltraPlot/pull/341)
* Fix links docs (https://github.com/Ultraplot/UltraPlot/pull/342)
* Lazy loading colormaps (https://github.com/Ultraplot/UltraPlot/pull/343)
* Set warning level for mpl to error (https://github.com/Ultraplot/UltraPlot/pull/350)
* Sanitize pad and len formatters on Cartesian Axes (https://github.com/Ultraplot/UltraPlot/pull/346)
* Fix order of label transfer (https://github.com/Ultraplot/UltraPlot/pull/353)
* Bump the github-actions group with 2 updates by @dependabot[bot] in https://github.com/Ultraplot/UltraPlot/pull/354
* Add cftime support for non-standard calendars (https://github.com/Ultraplot/UltraPlot/pull/344)

New Contributors
~~~~~~~~~~~~~~~~


* @Copilot made their first contribution in https://github.com/Ultraplot/UltraPlot/pull/325

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.60.2...v1.61.0

Note: v1.61.0 is yanked from pypi as it contained a debug statement. This merely removes the debug.

v1.60.2: Hotfix: double depth decorator that affected geoplots (2025-08-18)
---------------------------------------------------------------------------

What's Changed
~~~~~~~~~~~~~~


* Handle non homogeneous arrays  (https://github.com/Ultraplot/UltraPlot/pull/318)
* Update Cartopy references (https://github.com/Ultraplot/UltraPlot/pull/322)
* Fix inhomogeneous violin test (https://github.com/Ultraplot/UltraPlot/pull/323)
* Fix issue where double decorator does not parse function name (https://github.com/Ultraplot/UltraPlot/pull/320)

New Contributors
~~~~~~~~~~~~~~~~


* @rcomer made their first contribution in https://github.com/Ultraplot/UltraPlot/pull/322

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.60.1...v1.60.2

v1.60.1: Hotfixes for colors and colormaps (2025-08-08)
-------------------------------------------------------

Minor bug fixes

What's Changed
~~~~~~~~~~~~~~


* Fix edge case where vcenter is not properly set for diverging norms (https://github.com/Ultraplot/UltraPlot/pull/314)
* Fix color parsing when  color is not string (https://github.com/Ultraplot/UltraPlot/pull/315)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.60.0...v1.60.1

v1.60.0: It's better to share! (2025-08-05)
-------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html


UltraPlot extends its sharing capabilities by redefining how sharing works. As of this release, sharing will operate by looking at the subplotgrid and extending label sharing when plots are adjacent. Labels will be turned on for those subplots that


* Face and edge of the plot
* or face an empty plot space

In the past, sharing top and right labels would erroneously be turned off and could only be managed by turning the sharing feature off. 

For example, consider a simple 2x2 layout. Turning on the top and right labels now looks like:
:raw-html-m2r:`<img width="5701" height="5508" alt="layout=0" src="https://github.com/user-attachments/assets/c160296f-b52a-48a0-a9f7-70d9ecea6f50" />`

Similarly for more complex layouts the plots facing an edge will turn on their labels. Note that the limits are still shared for these subplots:

:raw-html-m2r:`<img width="8020" height="7828" alt="layout=1" src="https://github.com/user-attachments/assets/770d4cfd-da11-46af-ad5d-7bd1b991d65b" />`

Vertical inset colorbars
------------------------

UltraPlot now also supports vertical inset colorbars such as

:raw-html-m2r:`<img width="5000" height="5000" alt="pcolormesh" src="https://github.com/user-attachments/assets/d7183d3b-7aca-44ed-a3c2-7371aa34e2b9" />`

What's Changed
~~~~~~~~~~~~~~


* Feat vert inset cbars (https://github.com/Ultraplot/UltraPlot/pull/301)
* Refactor colorbar loc handling (https://github.com/Ultraplot/UltraPlot/pull/304)
* Sync ``_legend_dict`` on legend location change (https://github.com/Ultraplot/UltraPlot/pull/310)
* fix color being parsed for none (https://github.com/Ultraplot/UltraPlot/pull/312)
* feat: advanced axis sharing refactor + enhancements (https://github.com/Ultraplot/UltraPlot/pull/256)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.57.2...v1.60.0

v1.57.2: Bug fixes for Geo dms coordinates and reverse colors/colormaps (2025-07-02)
------------------------------------------------------------------------------------

What's Changed
~~~~~~~~~~~~~~


* Add citation metadata (CITATION.cff, .zenodo.json) to support scholarly use (https://github.com/Ultraplot/UltraPlot/pull/284)
* Update CITATON.cff (https://github.com/Ultraplot/UltraPlot/pull/286)
* Add citation links to README. (https://github.com/Ultraplot/UltraPlot/pull/287)
* Mv dynamic function to the subplotgrid (https://github.com/Ultraplot/UltraPlot/pull/281)
* add downloads badge (https://github.com/Ultraplot/UltraPlot/pull/290)
* replace color to orange (https://github.com/Ultraplot/UltraPlot/pull/291)
* Hotfix add all locations to colorbar label (https://github.com/Ultraplot/UltraPlot/pull/295)
* Fix DMS not set on some projections (https://github.com/Ultraplot/UltraPlot/pull/293)
* Bump mamba-org/setup-micromamba from 2.0.4 to 2.0.5 in the github-actions group (https://github.com/Ultraplot/UltraPlot/pull/299)
* fix late binding and proper reversal for funcs (https://github.com/Ultraplot/UltraPlot/pull/296)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.57.1...v1.57.2

v1.57.1: Zenodo release (2025-06-24)
------------------------------------

This PR integrates Zenodo with the UltraPlot repository to enable citation via DOI.

From now on, every GitHub release will be archived by Zenodo and assigned a unique DOI, allowing researchers and users to cite UltraPlot in a standardized, persistent way.

We’ve also added a citation file and BibTeX entry for convenience. Please refer to the GitHub “Cite this repository” section or use the provided BibTeX in your work.

This marks an important step in making UltraPlot more visible and citable in academic and scientific publications.

🔗 DOI: `https://doi.org/10.5281/zenodo.15733565 <https://doi.org/10.5281/zenodo.15733565>`_  

Cite as

.. code-block:: bibtex

   @software{vanElteren2025,
     author       = {Casper van Elteren and Matthew R. Becker},
     title        = {UltraPlot: A succinct wrapper for Matplotlib},
     year         = {2025},
     version      = {1.57.1},
     publisher    = {GitHub},
     url          = {https://github.com/Ultraplot/UltraPlot}
   }

What's Changed
~~~~~~~~~~~~~~


* Fix a few tests (https://github.com/Ultraplot/UltraPlot/pull/267)
* set rng per test (https://github.com/Ultraplot/UltraPlot/pull/268)
* Add xdist to image compare (https://github.com/Ultraplot/UltraPlot/pull/266)
* Fix issue where view is reset on setting ticklen (https://github.com/Ultraplot/UltraPlot/pull/272)
* Racing condition xdist fix (https://github.com/Ultraplot/UltraPlot/pull/273)
* Replace spring with forceatlas2 (https://github.com/Ultraplot/UltraPlot/pull/275)
* Revert xdist addition (https://github.com/Ultraplot/UltraPlot/pull/277)
* fix: pass layout_kw in network test function (https://github.com/Ultraplot/UltraPlot/pull/278)
* fix: this one needs a seed too (https://github.com/Ultraplot/UltraPlot/pull/279)
* rm paren (https://github.com/Ultraplot/UltraPlot/pull/280)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.57...v1.57.1

v1.57: Support matplotlib 3.10 and python 3.13 (2025-06-16)
-----------------------------------------------------------

What's Changed
~~~~~~~~~~~~~~


* Fix unused parameters being passed to pie chart (https://github.com/Ultraplot/UltraPlot/pull/260)
* Update return requirements pytest 8.4.0 (https://github.com/Ultraplot/UltraPlot/pull/265)
* Bump python to 3.13 (https://github.com/Ultraplot/UltraPlot/pull/264)
* Update matplotlib to mpl 3.10 (https://github.com/Ultraplot/UltraPlot/pull/263)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/v1.56...v1.57

v1.56: Feature addition: Beeswarm plot (2025-06-13)
---------------------------------------------------

We are introducing a new plot type with this release: a beeswarm plot. A beeswarm plot is a data visualization technique that displays individual data points in a way that prevents overlap while maintaining their relationship to categorical groups, creating a distinctive "swarm" pattern that resembles bees clustering around a hive. 

Unlike traditional box plots or violin plots that aggregate data, beeswarm plots show every individual observation, making them ideal for datasets with moderate sample sizes where you want to see both individual points and overall distribution patterns, identify outliers clearly, and compare distributions across multiple categories without losing any information through statistical summaries.

This plot mimics the beeswarm from ``SHAP`` library, but lacks the more sophisticated patterns they apply such as inline group clustering. UltraPlot does not aim to add these features but instead provide an interface that is simpler that users can tweak to their hearts desires.


.. image:: https://github.com/user-attachments/assets/98623e13-b0ab-4e15-87b1-64dfcd22ad57
   :target: https://github.com/user-attachments/assets/98623e13-b0ab-4e15-87b1-64dfcd22ad57
   :alt: tmp



.. raw:: html

   <details> <summary> snippet </summary>


   ```python
   import ultraplot as uplt, numpy as np

   # Create mock data
   n_points, n_features = 50, 4
   features = np.arange(n_features)
   data = np.empty((n_points, n_features))
   feature_values = np.repeat(
       features,
       n_points,
   ).reshape(data.shape)

   for feature in features:
       data[:, feature] = np.random.normal(feature * 1.5, 0.6, n_points)

   cmap = uplt.Colormap(uplt.rc["cmap.diverging"])

   # Create plot and style
   fig, (left, right) = uplt.subplots(ncols=2, share=0)
   left.beeswarm(
       data,
       orientation="vertical",
       alpha=0.7,
       cmap=cmap,
   )
   left.format(
       title="Traditional Beeswarm Plot",
       xlabel="Category",
       ylabel="Value",
       xticks=features,
       xticklabels=["Group A", "Group B", "Group C", "Group D"],
   )
   right.beeswarm(
       data,
       feature_values=feature_values,
       cmap=cmap,
       colorbar="right",
   )
   right.format(
       title="Feature Value Beeswarm Plot",
       xlabel="SHAP Value",
       yticks=features,
       yticklabels=["A", "B", "C", "D"],
       ylabel="Feature",
   )
   uplt.show(block=1)
   ```
   </details>


What's Changed
~~~~~~~~~~~~~~


* Hotfix GeoAxes indicate zoom.  (https://github.com/Ultraplot/UltraPlot/pull/249)
* Feature: Beeswarm plot (https://github.com/Ultraplot/UltraPlot/pull/251)
* GeoTicks not responsive (https://github.com/Ultraplot/UltraPlot/pull/253)
* add top level ignores for local testing (https://github.com/Ultraplot/UltraPlot/pull/255)
* Update .gitignore (https://github.com/Ultraplot/UltraPlot/pull/257)
* Refactor beeswarm (https://github.com/Ultraplot/UltraPlot/pull/254)

**Full Changelog**\ : https://github.com/Ultraplot/UltraPlot/compare/V1.55...v1.56

v1.55: V1.55. Bug fixes.  (2025-06-04)
--------------------------------------

This release continues our ongoing mission to squash pesky bugs and make your plotting experience smoother and more intuitive.

✨ New Features
---------------


* 
  Centered Labels for pcolormesh
    You can now enable center_labels when using pcolormesh, making it easier to annotate discrete diverging colormaps—especially when including zero among the label values. Ideal for visualizing data with meaningful central thresholds.

* 
  Direct Bar Labels for bar and hbar
    Bar labels can now be added directly via the bar and hbar commands. No more extra steps—just call the method and get your labeled bars out of the box.

🐞 Bug Fixes
------------

Various internal improvements and minor bug fixes aimed at ensuring a more robust and predictable plotting experience.

As always, thank you for using UltraPlot! Feedback, issues, and contributions are welcome.

What's Changed
~~~~~~~~~~~~~~


* Cartesian docs links fixed (https://github.com/Ultraplot/ultraplot/pull/226)
* minor fix for mpl3.10 (https://github.com/Ultraplot/ultraplot/pull/229)
* Adjust the ticks to center on 'nice' values (https://github.com/Ultraplot/ultraplot/pull/228)
* rm unnecessary show (https://github.com/Ultraplot/ultraplot/pull/241)
* Feat bar labels (https://github.com/Ultraplot/ultraplot/pull/240)
* Fix links for 1d plots in docs (https://github.com/Ultraplot/ultraplot/pull/242)
* Deprecate basemap (https://github.com/Ultraplot/ultraplot/pull/243)
* Hotfix get_border_axes (https://github.com/Ultraplot/ultraplot/pull/236)
* Hotfix panel (https://github.com/Ultraplot/ultraplot/pull/238)
* Hot fix twinned y labels (https://github.com/Ultraplot/ultraplot/pull/246)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.50.2...V1.55

v1.50.2 (2025-05-20)
--------------------

What's Changed
~~~~~~~~~~~~~~


* perf: run comparison tests at the same time as the main tests (https://github.com/Ultraplot/ultraplot/pull/213)
* fix cycler setting to 1 when only 1 column is parsed (https://github.com/Ultraplot/ultraplot/pull/218)
* Skip sharing logic when colorbar is added to GeoPlots. (https://github.com/Ultraplot/ultraplot/pull/219)
* Restore redirection for tricontourf for GeoPlotting (https://github.com/Ultraplot/ultraplot/pull/222)
* Fix numerous geo docs visuals (https://github.com/Ultraplot/ultraplot/pull/223)
* Allow rasterization on GeoFeatures. (https://github.com/Ultraplot/ultraplot/pull/220)
* more fixes (https://github.com/Ultraplot/ultraplot/pull/224)
* Docs fix3 (https://github.com/Ultraplot/ultraplot/pull/225)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.50.1...v1.50.2

v1.50.1 (2025-05-12)
--------------------

What's Changed
~~~~~~~~~~~~~~


* fix: specify import exception type and add typing-extensions to deps (https://github.com/Ultraplot/ultraplot/pull/212)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.50...v1.50.1

v1.50: Networks, lollipops and sharing (2025-05-11)
---------------------------------------------------

.. role:: raw-html-m2r(raw)
   :format: html



.. raw:: html

   <h2>UltraPlot v1.50</h2>



.. raw:: html

   <p>
   Version <strong>v1.50</strong> is a major milestone for UltraPlot. As we become more familiar with the codebase, we’ve opened the door to new features—balancing innovation with continuous backend improvements and bug fixes.
   </p>



.. raw:: html

   <hr>



:raw-html-m2r:`<h3>🌍 GeoAxes Sharing</h3>`


.. raw:: html

   <table style="border: none; border-collapse: collapse;">
     <tr>
       <td style="vertical-align: top; width: 60%;">
         <p>
           You can now share axes between subplots using GeoAxes, as long as they use the same rectilinear projection. This enables cleaner, more consistent layouts when working with geographical data.
         </p>
       </td>
       <td style="vertical-align: top; width: 40%;">
         <img src="https://github.com/user-attachments/assets/0997eae8-fc7e-4df1-b1cf-974986f3d07f" width="100%" />
       </td>
     </tr>
   </table>



.. raw:: html

   <hr>



:raw-html-m2r:`<h3>🕸️ Network Graphs</h3>`


.. raw:: html

   <table style="border: none; border-collapse: collapse;">
     <tr>
       <td style="vertical-align: top; width: 60%; border:none">
         <p>
           UltraPlot now supports network visualizations out of the box. With smart defaults and simple customization options, creating beautiful network plots is easier than ever.
         </p>
       </td>
       <td style="vertical-align: top; width: 40%;">
         <img src="https://github.com/user-attachments/assets/c9daea96-be7a-477c-baeb-8f72ebd1f817" width="100%" />
       </td>
     </tr>
   </table>



.. raw:: html

   <details>
   <summary>Network plotting code</summary>

   ```python
   import networkx as nx, ultraplot as uplt
   n = 100
   g = nx.random_geometric_graph(n, radius=0.2)
   c = uplt.colormaps.get_cmap("viko")
   c = c(np.linspace(0, 1, n))
   node = dict(
       node_size=np.random.rand(n) * 100,
       node_color=c,
   )
   fig, ax = uplt.subplots()
   ax.graph(g, layout="kamada_kawai", node_kw=node)
   fig.show()
   ```

   </details>


:raw-html-m2r:`<h3>🍭 Lollipop Graphs</h3>`


.. raw:: html

   <table>
     <tr>
       <td style="vertical-align: top; width: 60%;">
         <p>
           A sleek alternative to bar charts, lollipop graphs are now available directly through UltraPlot.
           They shine when visualizing datasets with many bars, reducing visual clutter while retaining clarity.
         </p>
       </td>
       <td style="vertical-align: top; width: 40%;">
         <img src="https://github.com/user-attachments/assets/1055a6d9-935f-442d-8b43-db4d55e23248"
    width="100%" />
       </td>
     </tr>
   </table>



.. raw:: html

   <details>
   <summary>Lollipop example code</summary>

   ```python
   import ultraplot as uplt, pandas as pd, numpy as np
   data = np.random.rand(5, 5).cumsum(axis=0).cumsum(axis=1)[:, ::-1]
   data = pd.DataFrame(
       data,
       columns=pd.Index(np.arange(1, 6), name="column"),
       index=pd.Index(["a", "b", "c", "d", "e"], name="row idx"),
   )
   fig, ax = uplt.subplots(ncols=2, share=0)
   ax[0].lollipop(
       data,
       stemcolor="green",
       stemwidth=2,
       marker="d",
       edgecolor="k",
   )
   ax[1].lollipoph(data, linestyle="solid")
   ```

   </details>


What's Changed
~~~~~~~~~~~~~~


* separate logger for ultraplot and matplotlib (https://github.com/Ultraplot/ultraplot/pull/178)
* Capture warning (https://github.com/Ultraplot/ultraplot/pull/180)
* tmp turning of test (https://github.com/Ultraplot/ultraplot/pull/183)
* Skip missing tests if added in PR (https://github.com/Ultraplot/ultraplot/pull/175)
* Revert "Skip missing tests if added in PR" (https://github.com/Ultraplot/ultraplot/pull/184)
* rm conftest from codecov (https://github.com/Ultraplot/ultraplot/pull/187)
* skip tests properly (https://github.com/Ultraplot/ultraplot/pull/186)
* Fix colorbar loc (https://github.com/Ultraplot/ultraplot/pull/182)
* Fix bar alpha (https://github.com/Ultraplot/ultraplot/pull/192)
* make import uplt to be consistent with rest of repo (https://github.com/Ultraplot/ultraplot/pull/195)
* Ensure that shared labels are consistently updated. (https://github.com/Ultraplot/ultraplot/pull/177)
* sensible defaults and unittest (https://github.com/Ultraplot/ultraplot/pull/189)
* Deprecation fix mpl 3.10 and beyond (https://github.com/Ultraplot/ultraplot/pull/69)
* Add network plotting to UltraPlot (https://github.com/Ultraplot/ultraplot/pull/169)
* Hotfix test (https://github.com/Ultraplot/ultraplot/pull/196)
* Discrete colors for quiver (https://github.com/Ultraplot/ultraplot/pull/198)
* correct url for basemap objects (https://github.com/Ultraplot/ultraplot/pull/202)
* override logx/y/log with updated docstring (https://github.com/Ultraplot/ultraplot/pull/203)
* Add lollipop graph (https://github.com/Ultraplot/ultraplot/pull/194)
* Fix network linking in docs and api refs (https://github.com/Ultraplot/ultraplot/pull/205)
* Avoid getting edges and setting centers for some shaders (https://github.com/Ultraplot/ultraplot/pull/208)
* Fix some references in inset docs (https://github.com/Ultraplot/ultraplot/pull/209)
* rm dep warning (https://github.com/Ultraplot/ultraplot/pull/210)
* [Feature add] Share Axes in GeoPlot + bug fixes (https://github.com/Ultraplot/ultraplot/pull/159)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.11...v1.5

v1.11: Various bug fixes (2025-04-25)
-------------------------------------

What's Changed
~~~~~~~~~~~~~~


* Update intersphinx links (https://github.com/Ultraplot/ultraplot/pull/128)
* Update geo doc (https://github.com/Ultraplot/ultraplot/pull/129)
* Hotfix update geo doc (https://github.com/Ultraplot/ultraplot/pull/130)
* New site, who dis? (https://github.com/Ultraplot/ultraplot/pull/132)
* Add about page (https://github.com/Ultraplot/ultraplot/pull/133)
* Make it mobile friendly (https://github.com/Ultraplot/ultraplot/pull/134)
* Add gallery to github page (https://github.com/Ultraplot/ultraplot/pull/140)
* Fix readme (https://github.com/Ultraplot/ultraplot/pull/142)
* Fix readme fixed sizes (https://github.com/Ultraplot/ultraplot/pull/143)
* added page for errors (https://github.com/Ultraplot/ultraplot/pull/141)
* Bump dawidd6/action-download-artifact from 2 to 6 in /.github/workflows (https://github.com/Ultraplot/ultraplot/pull/144)
* fix: checkout from correct fork (https://github.com/Ultraplot/ultraplot/pull/145)
* Set seed prior to test to ensure fidelity (https://github.com/Ultraplot/ultraplot/pull/148)
* Move warning inside pytest config (https://github.com/Ultraplot/ultraplot/pull/151)
* Fix scaler parsing (https://github.com/Ultraplot/ultraplot/pull/153)
* Update site logo (https://github.com/Ultraplot/ultraplot/pull/154)
* Fix minor grid showing on cbar (https://github.com/Ultraplot/ultraplot/pull/150)
* Add option to place abc indicator outside the axis bbox (https://github.com/Ultraplot/ultraplot/pull/139)
* Add unitests for ultraplot.internals.fonts (https://github.com/Ultraplot/ultraplot/pull/156)
* Minor refactor of unittests (https://github.com/Ultraplot/ultraplot/pull/157)
* Make anchor_mode default (https://github.com/Ultraplot/ultraplot/pull/161)
* Ipy rc kernel reset (https://github.com/Ultraplot/ultraplot/pull/164)
* allow subfigure formatting (https://github.com/Ultraplot/ultraplot/pull/167)
* make cbar labelloc possible for all direction (https://github.com/Ultraplot/ultraplot/pull/165)
* Add pyarrow to rm pandas error (https://github.com/Ultraplot/ultraplot/pull/171)
* Center figures in docs (https://github.com/Ultraplot/ultraplot/pull/170)
* mv toc to left (https://github.com/Ultraplot/ultraplot/pull/172)
* surpress warnings on action (https://github.com/Ultraplot/ultraplot/pull/174)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.10.0...v1.11

v1.10.0: Ticks for Geoaxes (2025-03-20)
---------------------------------------

This release marks a newly added feature: ticks on GeoAxes

.. image:: https://github.com/user-attachments/assets/92670ef4-5cb1-49fe-9b23-8d69a80e80cf
   :target: https://github.com/user-attachments/assets/92670ef4-5cb1-49fe-9b23-8d69a80e80cf
   :alt: image

This allows for users to set ticks for the x and or y axis. These can be controlled by ``lonticklen``\ , ``latticklen`` or ``ticklen`` for controlling the ``x``\ , ``y`` or both axis at the same time. This works independently to the major and minor gridlines allow for optimal control over the look and feel of your plots.

What's Changed
~~~~~~~~~~~~~~


* prod: add me to maintainers (https://github.com/Ultraplot/ultraplot/pull/117)
* prod: only use readthedocs for PR tests (https://github.com/Ultraplot/ultraplot/pull/118)
* feat: enable test coverage with codecov (https://github.com/Ultraplot/ultraplot/pull/121)
* dynamically build what's new (https://github.com/Ultraplot/ultraplot/pull/122)
* rm extra == line (https://github.com/Ultraplot/ultraplot/pull/123)
* bugfix for Axes.legend when certain keywords are set to str (https://github.com/Ultraplot/ultraplot/pull/124)
* reduce verbosity of extension (https://github.com/Ultraplot/ultraplot/pull/127)
* allow ticks for geoaxes (https://github.com/Ultraplot/ultraplot/pull/126)

New Contributors
~~~~~~~~~~~~~~~~


* @syrte made their first contribution in https://github.com/Ultraplot/ultraplot/pull/124

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.9...v1.10.0

v1.0.9: IPython 9.0.0 compatibility and numerous backend fixes. (2025-03-05)
----------------------------------------------------------------------------

What's Changed
~~~~~~~~~~~~~~


* filter out property if not set (https://github.com/Ultraplot/ultraplot/pull/99)
* Add texgyre to docs (https://github.com/Ultraplot/ultraplot/pull/101)
* Texgyre fix (https://github.com/Ultraplot/ultraplot/pull/102)
* rm warnings when downloading data inside env (https://github.com/Ultraplot/ultraplot/pull/104)
* prod: only build ultraplot when ultraplot src changes (https://github.com/Ultraplot/ultraplot/pull/106)
* Gitignore baseline (https://github.com/Ultraplot/ultraplot/pull/109)
* Fix colorbar ticks (https://github.com/Ultraplot/ultraplot/pull/108)
* Attempt fix workflow docs build (https://github.com/Ultraplot/ultraplot/pull/114)
* rm ref semver (https://github.com/Ultraplot/ultraplot/pull/112)
* Only store failed tests mpl-pytest (https://github.com/Ultraplot/ultraplot/pull/113)
* fix: matrix test for no changes is running when it should not be (https://github.com/Ultraplot/ultraplot/pull/115)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.8...v1.0.9

v1.0.8-2: Hotfix cycling properties (2025-02-27)
------------------------------------------------

Hot fix for cycle not recognizing color argument

What's Changed
~~~~~~~~~~~~~~


* filter out property if not set (https://github.com/Ultraplot/ultraplot/pull/99)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.8...v1.0.8-2

v1.0.8: Minor bug fixes (2025-02-23)
------------------------------------

Fixes an issue where ticks were not properly set when giving levels and ticks in ``pcolormesh`` and related functions in the colorbar. See more of the changes below.

What's Changed
~~~~~~~~~~~~~~


* fix: remove race condition for pushes of tags (https://github.com/Ultraplot/ultraplot/pull/78)
* use seed for reproducibility (https://github.com/Ultraplot/ultraplot/pull/79)
* Fix demo function not extracting colormaps (https://github.com/Ultraplot/ultraplot/pull/83)
* allows cycle to be a tuple (https://github.com/Ultraplot/ultraplot/pull/87)
* Fixes heatmap not showing labels. (https://github.com/Ultraplot/ultraplot/pull/91)
* Doc link fix (https://github.com/Ultraplot/ultraplot/pull/92)
* explicitly override minor locator if given (https://github.com/Ultraplot/ultraplot/pull/96)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.7...v1.0.8

v1.0.7: Dev update. (2025-02-15)
--------------------------------

What's Changed
~~~~~~~~~~~~~~


* added path explicitly on publish (https://github.com/Ultraplot/ultraplot/pull/77)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.6...v1.0.7

v1.0.6: Ensure norm fix (2025-02-15)
------------------------------------

What's Changed
~~~~~~~~~~~~~~


* add case where cycler is already a cycle (https://github.com/Ultraplot/ultraplot/pull/65)
* fix: make sure PRs do not mess with releases (https://github.com/Ultraplot/ultraplot/pull/67)
* fix: ensure pypi readme works ok (https://github.com/Ultraplot/ultraplot/pull/70)
* feat: deduplicate pypi publish workflow (https://github.com/Ultraplot/ultraplot/pull/71)
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/Ultraplot/ultraplot/pull/73
* use norm explicitly (https://github.com/Ultraplot/ultraplot/pull/76)

New Contributors
~~~~~~~~~~~~~~~~


* @pre-commit-ci made their first contribution in https://github.com/Ultraplot/ultraplot/pull/73

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.5...v1.0.6

v1.0.5 (2025-02-02)
-------------------

What's Changed
~~~~~~~~~~~~~~


* test: adjust test matrix to use one locale and add matrix dimension over MPL versions (https://github.com/Ultraplot/ultraplot/pull/51)
* Dep build (https://github.com/Ultraplot/ultraplot/pull/57)
* Second dep on build still being skipped (https://github.com/Ultraplot/ultraplot/pull/58)
* another attempt to fix publish (https://github.com/Ultraplot/ultraplot/pull/59)
* fix: remove custom classifier for MPL (https://github.com/Ultraplot/ultraplot/pull/62)
* fix: correct chain of logic for publish workflow (https://github.com/Ultraplot/ultraplot/pull/63)
* fix: get pypi publish working (https://github.com/Ultraplot/ultraplot/pull/64)

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.4...v1.0.5

v1.0.4: Fixing Margins (2025-01-31)
-----------------------------------

A major change for this release is that the margins were not properly being set with the latest mpl. This reverts the margins back to the behavior where they are tighter as is expected from UltraPlot!

v1.0.3: Minor bug fixes (2025-01-27)
------------------------------------

We are still experiencing some growing pains with proplot -> ultraplot conversion, however it is looking good. Some bugs were fixed regarding compatibility with mpl3.10 and we are moving towards fidelity checks. Please update when you can to this latest release.

This release is to ensure that the latest version is on pypi and conda.

**Full Changelog**\ : https://github.com/Ultraplot/ultraplot/compare/v1.0.2...v1.0.3

v1.0: Big Compatibility Release! Matplotlib >= 3.8. (2025-01-11)
----------------------------------------------------------------

* 78367da2 (HEAD -> main, tag: v1.0, uplt/main) Matplotlib 3.10 - Compatability
* 4e15fde2 Merge pull request #16 from cvanelteren/linter-workflow
* 54837966 (origin/linter-workflow, linter-workflow) make repo - black compatible
* 7aa82a2c added linter workflow
* 97f14082 point readme badge to correct workflow
* fb762c5b (origin/main) Merge pull request #13 from - cvanelteren/triangulation-fix
* afa14caf (origin/triangulation-fix) removed pandas reference
* 2d66e46b added data dict to unittest test and made - preprocessing compatible
* 465688e7 add decorator to other trifunctions
* ad83bfb0 ensure backwards compatibility
* 23f65bb9 added df to unittest
* d239bfc3 added unittest for triangulaions
* 5bb8ac14 use mpl triangulation parser
* 5dc8b44b move logic to internals and update input parsing - functions for tri
* f213d870 tripoint also added
* 9eeda2db small typo
* a1c8894b Merge branch 'main' into triangulation-fix
* 83973941 allow triangulation object in tricountour(f)
* 6b8223a8 Merge pull request #4 from cvanelteren/conda
* fa1f2fcc (origin/conda) removed conda recipe
* defb219e separate build and test
* 4cf2c940 # This is a combination of 2 commits. # This is the - 1st commit message:
* 9c75035c separate build and test
* 0089fe04 license revert
* adac1c9a Merge pull request #10 from Ultraplot/revert-6-main
* e31afe64 (uplt/revert-6-main) Revert "license update"
* 35204ef4 renamed yml to ensure consistency
* b243afe7 Merge pull request #8 from cvanelteren/main
* 0c4bc1f8 replaced pplt -> uplt
* 656a7464 Merge pull request #5 from cvanelteren/logo_square
* 89c59cf5 Merge pull request #7 from cvanelteren/main
* 8d01cf33 typo in readme shield
* 7e0ec000 Merge pull request #6 from cvanelteren/main
* 70157b33 license update
* e6d8eca9 (origin/logo_square, logo_square) capitalization to - UltraPlot in docs
* e99be782 square logos
* c2a96554 separated workflows
* 5609372c conda and pypi publish workflow
* d04ea9d9 small changes in workflow
* 5432bdbe add workflow for conda-forge

