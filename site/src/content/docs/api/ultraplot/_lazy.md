---
title: "ultraplot._lazy"
description: "Helpers for lazy attribute loading in :mod:`ultraplot`."
source: "ultraplot/_lazy.py"
---

`ultraplot._lazy`

Helpers for lazy attribute loading in :mod:`ultraplot`.

## Public Classes

### `LazyLoader`

Encapsulates lazy-loading mechanics for the ultraplot top-level module.

## Public Functions

### `install_module_proxy(module: Optional[types.ModuleType])`

Prevent lazy-loading names from being clobbered by submodule imports.
