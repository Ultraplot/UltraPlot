# UltraPlot v2.6.0: Histogram KDEs, sticky edges, and smoother integrations

UltraPlot 2.6.0 adds kernel density overlays to histograms, makes sticky axis
edges configurable, expands geographic legends, and improves interoperability
with Seaborn. This release also fixes shared geographic tick configuration,
refreshes the documentation experience, and hardens tag-based package releases.

## New Features

* **Kernel density overlays for histograms (`hist(..., kde=True)`)**: Histograms
  can now draw a Gaussian kernel density estimate for every data column. Each
  curve follows its histogram's color, count or density scaling, orientation,
  weights, and stacking. Use `kde_kw` to select the bandwidth and evaluation
  resolution or pass ordinary line styling. SciPy is available through the new
  `stats` extra with `pip install ultraplot[stats]` (#795).

<img width="700" alt="UltraPlot and Seaborn histogram KDE comparison" src="https://github.com/user-attachments/assets/b930c5b1-45db-4071-b2d0-5614c5e0ca0f" />

  <details>
  <summary>snippet</summary>

  ```python
  import numpy as np
  import ultraplot as uplt

  rng = np.random.default_rng(51423)
  data = rng.normal(size=(500, 3)) + np.arange(3)

  fig, ax = uplt.subplots(refwidth=4)
  ax.hist(
      data,
      bins=20,
      kde=True,
      kde_kw={"bw_method": "silverman", "linewidth": 2},
      labels=("A", "B", "C"),
      legend="ur",
  )
  ax.format(xlabel="value", ylabel="count")
  ```
  </details>

* **Configurable sticky edges**: The new `axes.sticky_edges` rc setting and
  per-axes `use_sticky_edges` property control whether lines, fills, and similar
  artists meet the axes bounds without automatic padding. This keeps the useful
  default while making it easy to restore margins globally or for one axes
  (#796).

  <details>
  <summary>snippet</summary>

  ```python
  import ultraplot as uplt

  uplt.rc["axes.sticky_edges"] = False
  fig, axs = uplt.subplots(ncols=2)
  axs[0].plot([0, 1], [0, 1])

  # Override the global setting for an individual axes.
  axs[1].use_sticky_edges = True
  axs[1].plot([0, 1], [0, 1])
  ```
  </details>

* **Line entries in geographic legends**: Geographic legends now accept line
  symbols alongside the existing point and area symbols (#783).

## Integrations

* **Better Seaborn legend compatibility**: `UltraLegend` now implements
  `remove()`, and UltraPlot supplies the compatibility hooks expected by
  `seaborn.move_legend`. Legends created by Seaborn inside `ax.external()` can
  therefore be moved or removed normally (#793).

  <details>
  <summary>snippet</summary>

  ```python
  import seaborn as sns
  import ultraplot as uplt

  fig, ax = uplt.subplots()
  with ax.external():
      sns.histplot(data, ax=ax, kde=True, legend=True)
      sns.move_legend(ax, "upper right")
  ```
  </details>

## Bug Fixes

* **Shared geographic ticks**: Explicit longitude and latitude locators,
  minor locators, and formatters now propagate across shared `GeoAxes`. The
  single-tick edge case is also handled correctly (#801).
* **Statistical plotting docs**: Fixed the documentation build after adding the
  histogram KDE example (#798).

## Deprecations

* **Basemap backend**: The Basemap geographic backend is now deprecated for
  UltraPlot 3.0. Use Cartopy for new geographic plots (#786).
* **Legacy ProPlot API**: Removed items that had remained deprecated since the
  ProPlot transition (#779).

## Documentation and Maintenance

* Reworked the **Why UltraPlot?** page into interactive before-and-after
  comparisons and made the divider directly draggable (#788, #799).
* Corrected tag-derived package versions and limited release-version validation
  to publish builds (#790, #791).
* Made `docs/Makefile` perform a genuinely clean documentation rebuild while
  preserving efficient CI caching (#789).
* Refreshed CI workflows and GitHub Actions dependencies (#784, #785).

## Commits

* `5828da6f` Add line to geolegend (#783)
* `9987c1dc` Bump the github-actions group with 2 updates (#784)
* `11cc5416` Remove deprecated items
* `58568d6c` Fix black formatting
* `2ab3b6ce` Update the other workflow files (#785)
* `3eb03e35` Deprecate the basemap backend starting from version 3.0 (#786)
* `f0b07a9d` Remove deprecated items (#779)
* `f6a0611f` Make docs clean fully reset the build cache (#789)
* `81cba25b` Fix release build versioning from Git tags (#790)
* `c4665a99` Only validate release version on non-PR publish builds (#791)
* `9c1d900a` Rework the Why UltraPlot? page with comparison cards (#788)
* `3502a4e3` Add remove to legend (#793)
* `70f8fb9e` Add sticky edges configuration (#796)
* `7de5adb1` Fix failing documentation (#798)
* `ae8e13e2` Add KDE support for histograms (#795)
* `bbcdfff6` Make the comparison selector directly draggable (#799)
* `9583a012` Fix shared geographic tick synchronization (#801)

## What's Changed

* Add line to geolegend by @gepcel in https://github.com/Ultraplot/UltraPlot/pull/783
* Bump the GitHub Actions group by @dependabot in https://github.com/Ultraplot/UltraPlot/pull/784
* Update source-formatting workflows by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/785
* Deprecate the Basemap backend by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/786
* Remove deprecated items by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/779
* Rework the Why UltraPlot? page by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/788
* Fully reset the docs build cache on clean by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/789
* Fix release build versioning from Git tags by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/790
* Fix release version validation for pull requests by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/791
* Add Seaborn-compatible legend removal by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/793
* Add configurable sticky edges by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/796
* Fix the statistical plotting documentation by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/798
* Add KDE support for histograms by @gepcel in https://github.com/Ultraplot/UltraPlot/pull/795
* Improve the comparison selector by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/799
* Fix shared geographic tick synchronization by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/801

**Full Changelog**: https://github.com/Ultraplot/UltraPlot/compare/v2.5.0...v2.6.0
