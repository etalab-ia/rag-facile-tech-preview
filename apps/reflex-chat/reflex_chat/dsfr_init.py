"""DSFR React component wrappers for Reflex.

Reflex v0.8.0+ uses Vite + React Router (SPA).
Single-init pattern to avoid Reflex issue #5923 (duplicate identifier errors).

Architecture:
- Only DsfrHeader defines _get_custom_code() — initialize + import both subcomponents
- DsfrFooter: no custom code, just references the wrapper
- This prevents duplicate const declarations in generated JS
"""

import reflex as rx


# Custom code for DsfrHeader only: import + initialize DSFR + export both wrappers
_DSFR_INIT_CODE = """
import { startReactDsfr } from "@codegouvfr/react-dsfr/spa";
import HeaderBase from "@codegouvfr/react-dsfr/Header";
import FooterBase from "@codegouvfr/react-dsfr/Footer";

// Initialize DSFR once at app startup
startReactDsfr({ defaultColorScheme: "system" });

// Export wrapped components for use by DsfrHeader and DsfrFooter
export const DsfrHeaderComponent = HeaderBase;
export const DsfrFooterComponent = FooterBase;
"""


class DsfrHeader(rx.NoSSRComponent):
    """DSFR Header component (Vite + React Router).

    Initializes DSFR and imports both Header/Footer components.
    """

    library: str = "@codegouvfr/react-dsfr"
    tag: str = "DsfrHeaderComponent"

    brand_top: rx.Var[str]
    service_title: rx.Var[str]
    service_tagline: rx.Var[str]
    home_link_props: rx.Var[dict]

    @classmethod
    def _get_custom_code(cls) -> str:
        return _DSFR_INIT_CODE


class DsfrFooter(rx.NoSSRComponent):
    """DSFR Footer component (Vite + React Router).

    Initialized by DsfrHeader._get_custom_code() — no custom code here.
    (Avoids Reflex issue #5923: duplicate identifier errors)
    """

    library: str = "@codegouvfr/react-dsfr"
    tag: str = "DsfrFooterComponent"

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
