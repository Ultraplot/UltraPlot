.. _lazy_loading:

===================================
Lazy Loading and Adding New Modules
===================================

UltraPlot uses a lazy loading mechanism to improve import times. This means that
submodules are not imported until they are actually used. This is controlled by the
:py:func:`__getattr__` function in `ultraplot/__init__.py`.

The lazy loading system is mostly automated. It works by scanning the `ultraplot`
directory for modules and exposing them based on conventions.

**Convention-Based Loading**

The automated system follows these rules:

1.  **Single-Class Modules:** If a module `my_module.py` has an `__all__`
    variable with a single class or function `MyCallable`, it will be exposed
    at the top level as `uplt.my_module`. For example, since
    `ultraplot/figure.py` has `__all__ = ['Figure']`, you can access the `Figure`
    class with `uplt.figure`.

2.  **Multi-Content Modules:** If a module has multiple items in `__all__` or no
    `__all__`, the module itself will be exposed. For example, you can access
    the `utils` module with :py:mod:`uplt.utils`.

**Adding New Modules**

When adding a new submodule, you usually don't need to modify `ultraplot/__init__.py`.
Simply follow these conventions:

*   If you want to expose a single class or function from your module as a
    top-level attribute, set the `__all__` variable in your module to a list
    containing just that callable's name.

*   If you want to expose the entire module, you can either use an `__all__` with
    multiple items, or no `__all__` at all.

**Handling Exceptions**

For cases that don't fit the conventions, there is an exception-based
configuration. The `_LAZY_LOADING_EXCEPTIONS` dictionary in
`ultraplot/__init__.py` is used to manually map top-level attributes to
modules and their contents.

You should only need to edit this dictionary if you are:

*   Creating an alias for a module (e.g., `crs` for `proj`).
*   Exposing an internal variable (e.g., `colormaps` for `_cmap_database`).
*   Exposing a submodule that doesn't follow the file/directory structure.

By following these guidelines, your new module will be correctly integrated into
the lazy loading system.
