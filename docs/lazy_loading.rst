.. _lazy_loading:

===================================
Lazy Loading and Adding New Modules
===================================

UltraPlot uses a lazy loading mechanism to improve import times. This means that
submodules are not imported until they are actually used. This is controlled by the
`__getattr__` function in `ultraplot/__init__.py`.

When adding a new submodule, you need to make sure it's compatible with the lazy
loader. Here's how to do it:

1.  **Add the submodule to `_STAR_MODULES`:** In `ultraplot/__init__.py`, add the
    name of your new submodule to the `_STAR_MODULES` tuple. This will make it
    discoverable by the lazy loader.

2.  **Add the submodule to `_MODULE_SOURCES`:** Also in `ultraplot/__init__.py`,
    add an entry to the `_MODULE_SOURCES` dictionary that maps the name of your
    submodule to its source file.

3.  **Exposing Callables:** If you want to expose a function or class from your
    submodule as a top-level attribute of the `ultraplot` package (e.g.,
    `uplt.my_function`), you need to add an entry to the `_EXTRA_ATTRS`
    dictionary.

    *   To expose a function or class `MyFunction` from `my_module.py` as
        `uplt.my_function`, add the following to `_EXTRA_ATTRS`:
        `"my_function": ("my_module", "MyFunction")`.
    *   If you want to expose the entire submodule as a top-level attribute
        (e.g., `uplt.my_module`), you can add:
        `"my_module": ("my_module", None)`.

By following these steps, you can ensure that your new module is correctly
integrated into the lazy loading system.
