"""Public configuration API, initialized before its settings are exposed."""

from . import _config

_config._initialize()

from ._config import (
    Configurator,
    rc,
    rc_ultraplot,
    rc_matplotlib,
    use_style,
    config_inline_backend,
    register_cmaps,
    register_cycles,
    register_colors,
    register_fonts,
)

__all__ = [
    "Configurator",
    "rc",
    "rc_ultraplot",
    "rc_matplotlib",
    "use_style",
    "config_inline_backend",
    "register_cmaps",
    "register_cycles",
    "register_colors",
    "register_fonts",
]


def __getattr__(name):
    # Preserve access to existing configuration helpers.
    return getattr(_config, name)
