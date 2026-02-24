"""DSFR React component wrappers for Reflex.

Wraps @codegouvfr/react-dsfr Header and Footer as Reflex NoSSRComponents.
startReactDsfr() is injected via _get_custom_code() on DsfrHeader and
runs at module load time (before render), satisfying react-dsfr's
requirement that initialization happens before any DSFR components render.
"""

import reflex as rx


class DsfrHeader(rx.NoSSRComponent):
    """Wraps the @codegouvfr/react-dsfr Header component.

    Header is the mandatory government identity component — displays
    the Marianne logo, brand name, and service title at the top of every
    French government service.
    """

    library: str = "@codegouvfr/react-dsfr/Header"
    tag: str = "Header"
    is_default: bool = True

    # Required props (camelCase handled automatically by Reflex)
    brand_top: rx.Var[str]  # e.g. "République\nFrançaise"
    home_link_props: rx.Var[dict]  # e.g. {"href": "/", "title": "Accueil"}

    # Optional props
    service_title: rx.Var[str]
    service_tagline: rx.Var[str]
    quick_access_items: rx.Var[list]

    @classmethod
    def _get_custom_code(cls) -> str:
        """Inject startReactDsfr() at module load time (before render)."""
        return (
            'import { startReactDsfr } from "@codegouvfr/react-dsfr/spa";\n'
            'startReactDsfr({ defaultColorScheme: "system" });\n'
        )


class DsfrFooter(rx.NoSSRComponent):
    """Wraps the @codegouvfr/react-dsfr Footer component.

    Footer is the mandatory government identity component at the bottom
    of every French government service.
    """

    library: str = "@codegouvfr/react-dsfr/Footer"
    tag: str = "Footer"
    is_default: bool = True

    # Required props
    brand_top: rx.Var[str]
    home_link_props: rx.Var[dict]
    # DSFR requires an accessibility statement level
    accessibility: rx.Var[
        str
    ]  # "fully compliant" | "partially compliant" | "non compliant"

    # Optional props
    content_description: rx.Var[str]
    bottom_items: rx.Var[list]


def dsfr_header() -> rx.Component:
    """Render the DSFR government identity header."""
    return DsfrHeader.create(
        brand_top="République\nFrançaise",
        home_link_props={"href": "/", "title": "Accueil - RAG Facile"},
        service_title="RAG Facile",
        service_tagline="Assistant RAG pour les services publics",
    )


def dsfr_footer() -> rx.Component:
    """Render the DSFR government identity footer."""
    return DsfrFooter.create(
        brand_top="République\nFrançaise",
        home_link_props={"href": "/", "title": "Accueil - RAG Facile"},
        accessibility="non compliant",
        content_description=(
            "RAG Facile est un starter kit open source pour construire "
            "des assistants RAG pour les services publics français."
        ),
    )
