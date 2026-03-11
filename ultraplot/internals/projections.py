#!/usr/bin/env python3
"""
Projection binding registry used by figure axes creation.
"""

from dataclasses import dataclass, field

import matplotlib.projections as mproj

from .. import constructor


@dataclass(frozen=True)
class ProjectionContext:
    """
    Context passed to projection bindings.
    """

    figure: object
    proj_kw: dict
    backend: str | None


@dataclass(frozen=True)
class ProjectionResolution:
    """
    Resolved projection plus any injected keyword arguments.
    """

    projection: object | str | None = None
    kwargs: dict = field(default_factory=dict)

    def as_kwargs(self, kwargs=None):
        merged = dict(kwargs or {})
        if self.projection is not None:
            merged["projection"] = self.projection
        merged.update(self.kwargs)
        return merged


@dataclass(frozen=True)
class ProjectionBinding:
    """
    Projection matcher and resolver pair.
    """

    name: str
    matcher: object
    resolver: object


_PROJECTION_BINDINGS = []


def register_projection_binding(name, matcher, resolver=None):
    """
    Register a projection binding. Can be used as a decorator.
    """
    if resolver is None:

        def decorator(func):
            _PROJECTION_BINDINGS.append(ProjectionBinding(name, matcher, func))
            return func

        return decorator

    _PROJECTION_BINDINGS.append(ProjectionBinding(name, matcher, resolver))
    return resolver


def iter_projection_bindings():
    """
    Return the registered projection bindings.
    """
    return tuple(_PROJECTION_BINDINGS)


def _get_axes_module():
    from .. import axes as paxes

    return paxes


def _looks_like_astropy_projection(proj):
    module = getattr(type(proj), "__module__", "")
    return module.startswith("astropy.")


def _prefixed_projection_name(name):
    if name.startswith("ultraplot_"):
        return name if name in mproj.get_projection_names() else None
    prefixed = "ultraplot_" + name
    try:
        mproj.get_projection_class(prefixed)
    except (KeyError, ValueError):
        return None
    return prefixed


def _container_projection_name(external_axes_class):
    token = f"{external_axes_class.__module__}_{external_axes_class.__name__}"
    return "_ultraplot_container_" + token.replace(".", "_").replace("-", "_").lower()


def _wrap_external_projection(figure, projection):
    if projection is None:
        return ProjectionResolution()

    external_axes_class = None
    external_axes_kwargs = {}
    if isinstance(projection, str):
        if projection.startswith("ultraplot_") or projection.startswith(
            "_ultraplot_container_"
        ):
            return ProjectionResolution(projection=projection)
        try:
            external_axes_class = mproj.get_projection_class(projection)
        except (KeyError, ValueError):
            return ProjectionResolution(projection=projection)
    elif hasattr(projection, "_as_mpl_axes"):
        try:
            external_axes_class, external_axes_kwargs = (
                figure._process_projection_requirements(projection=projection)
            )
        except Exception:
            return ProjectionResolution(projection=projection)
    else:
        return ProjectionResolution(projection=projection)

    paxes = _get_axes_module()
    if issubclass(external_axes_class, paxes.Axes):
        return ProjectionResolution(
            projection=projection,
            kwargs=dict(external_axes_kwargs),
        )

    from ..axes.container import create_external_axes_container

    container_name = _container_projection_name(external_axes_class)
    if container_name not in mproj.get_projection_names():
        container_class = create_external_axes_container(
            external_axes_class, projection_name=container_name
        )
        mproj.register_projection(container_class)

    return ProjectionResolution(
        projection=container_name,
        kwargs={
            "external_axes_class": external_axes_class,
            "external_axes_kwargs": dict(external_axes_kwargs),
        },
    )


@register_projection_binding(
    "astropy_wcs_string",
    lambda proj, context: isinstance(proj, str)
    and proj in ("astro", "astropy", "wcs", "ultraplot_astro"),
)
def _resolve_astropy_wcs_string(proj, context):
    _get_axes_module().get_astro_axes_class(load=True)
    return ProjectionResolution(projection="ultraplot_astro")


@register_projection_binding(
    "native_ultraplot_string",
    lambda proj, context: isinstance(proj, str)
    and _prefixed_projection_name(proj) is not None,
)
def _resolve_native_ultraplot_string(proj, context):
    return ProjectionResolution(projection=_prefixed_projection_name(proj))


@register_projection_binding(
    "astropy_wcs_object",
    lambda proj, context: (
        not isinstance(proj, str)
        and _looks_like_astropy_projection(proj)
        and bool(_get_axes_module().get_astropy_wcs_types(load=True))
        and isinstance(proj, _get_axes_module().get_astropy_wcs_types())
    ),
)
def _resolve_astropy_wcs_object(proj, context):
    return ProjectionResolution(projection="ultraplot_astro", kwargs={"wcs": proj})


@register_projection_binding(
    "cartopy_projection_object",
    lambda proj, context: (
        not isinstance(proj, str)
        and constructor.Projection is not object
        and isinstance(proj, constructor.Projection)
    ),
)
def _resolve_cartopy_projection_object(proj, context):
    return ProjectionResolution(
        projection="ultraplot_cartopy",
        kwargs={"map_projection": proj},
    )


@register_projection_binding(
    "basemap_projection_object",
    lambda proj, context: (
        not isinstance(proj, str)
        and constructor.Basemap is not object
        and isinstance(proj, constructor.Basemap)
    ),
)
def _resolve_basemap_projection_object(proj, context):
    return ProjectionResolution(
        projection="ultraplot_basemap",
        kwargs={"map_projection": proj},
    )


@register_projection_binding(
    "geographic_projection_name",
    lambda proj, context: isinstance(proj, str)
    and (constructor.Projection is not object or constructor.Basemap is not object),
)
def _resolve_geographic_projection_name(proj, context):
    try:
        proj_obj = constructor.Proj(
            proj,
            backend=context.backend,
            include_axes=True,
            **context.proj_kw,
        )
    except ValueError:
        return ProjectionResolution()
    return ProjectionResolution(
        projection="ultraplot_" + proj_obj._proj_backend,
        kwargs={"map_projection": proj_obj},
    )


@register_projection_binding(
    "registered_matplotlib_string",
    lambda proj, context: isinstance(proj, str)
    and proj in mproj.get_projection_names(),
)
def _resolve_registered_matplotlib_string(proj, context):
    return ProjectionResolution(projection=proj)


def resolve_projection(proj, *, figure, proj_kw=None, backend=None):
    """
    Resolve a user projection spec to a final projection and kwargs.
    """
    proj_kw = proj_kw or {}
    if isinstance(proj, str):
        proj = proj.lower()
    context = ProjectionContext(figure=figure, proj_kw=proj_kw, backend=backend)

    resolution = None
    for binding in _PROJECTION_BINDINGS:
        if binding.matcher(proj, context):
            resolution = binding.resolver(proj, context)
            if resolution.projection is not None or resolution.kwargs:
                break

    if resolution is None or (resolution.projection is None and not resolution.kwargs):
        if isinstance(proj, str):
            paxes = _get_axes_module()
            raise ValueError(
                f"Invalid projection name {proj!r}. If you are trying to generate a "
                "GeoAxes with a cartopy.crs.Projection or mpl_toolkits.basemap.Basemap "
                "then cartopy or basemap must be installed. Otherwise the known axes "
                f"subclasses are:\n{paxes._cls_table}"
            )
        resolution = ProjectionResolution(projection=proj)

    final = _wrap_external_projection(figure, resolution.projection)
    merged_kwargs = dict(resolution.kwargs)
    merged_kwargs.update(final.kwargs)
    projection = (
        final.projection if final.projection is not None else resolution.projection
    )
    return ProjectionResolution(projection=projection, kwargs=merged_kwargs)


def resolve_projection_kwargs(figure, proj, *, proj_kw=None, backend=None, kwargs=None):
    """
    Resolve a projection and merge the result into an existing keyword dictionary.
    """
    resolution = resolve_projection(
        proj,
        figure=figure,
        proj_kw=proj_kw,
        backend=backend,
    )
    return resolution.as_kwargs(kwargs)


def finalize_projection_kwargs(figure, kwargs):
    """
    Finalize an already-parsed projection dictionary.
    """
    projection = kwargs.get("projection")
    if projection is None:
        return kwargs
    final = _wrap_external_projection(figure, projection)
    return final.as_kwargs(kwargs)
