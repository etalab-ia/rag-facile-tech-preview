"""DSFR React component wrappers for Reflex.

Reflex v0.8.0+ uses Vite + React Router (not Next.js).
Use react-dsfr's SPA integration pattern with React Router Link registration.
"""

import reflex as rx


# Initialize DSFR with React Router Link integration
_DSFR_INIT_CODE = """
import { startReactDsfr } from "@codegouvfr/react-dsfr/spa";
import { Link } from "react-router-dom";

startReactDsfr({
  defaultColorScheme: "system",
  Link
});

declare module '@codegouvfr/react-dsfr/spa' {
  interface RegisterLink {
    Link: typeof Link;
  }
}
"""


class DsfrHeader(rx.NoSSRComponent):
    """DSFR Header component (Vite + React Router)."""

    library: str = "@codegouvfr/react-dsfr"
    tag: str = "Header"
    is_default: bool = True

    brand_top: rx.Var[str]
    service_title: rx.Var[str]
    service_tagline: rx.Var[str]
    home_link_props: rx.Var[dict]

    @classmethod
    def _get_custom_code(cls) -> str:
        return _DSFR_INIT_CODE


class DsfrFooter(rx.NoSSRComponent):
    """DSFR Footer component (Vite + React Router)."""

    library: str = "@codegouvfr/react-dsfr"
    tag: str = "Footer"
    is_default: bool = True

    brand_top: rx.Var[str]
    accessibility: rx.Var[str]
    content_description: rx.Var[str]
    home_link_props: rx.Var[dict]


def dsfr_header() -> rx.Component:
    """Render DSFR Header."""
    return DsfrHeader.create(
        brand_top="République\nFrançaise",
        service_title="RAG Facile",
        service_tagline="Assistant RAG pour les services publics",
        home_link_props={"href": "/", "title": "Accueil - RAG Facile"},
    )


def dsfr_footer() -> rx.Component:
    """Render DSFR Footer."""
    return DsfrFooter.create(
        brand_top="République\nFrançaise",
        accessibility="non compliant",
        content_description=(
            "RAG Facile est un starter kit open source pour construire "
            "des assistants RAG pour les services publics français."
        ),
        home_link_props={"href": "/", "title": "Accueil"},
    )
