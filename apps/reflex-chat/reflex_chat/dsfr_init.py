"""DSFR React component wrappers for Reflex.

Reflex v0.8.0+ uses Vite + React Router (SPA).
Single-init pattern to avoid Reflex issue #5923 (duplicate identifier errors).

Architecture:
- `DsfrInit` is an invisible component that injects the `startReactDsfr` code globally.
- `DsfrHeader` and `DsfrFooter` are standard reflexive wrappers mapped natively to `@codegouvfr/react-dsfr` exports.
"""

import reflex as rx


class DsfrInit(rx.Component):
    """Invisible component to initialize DSFR without triggering Vite module resolution."""

    tag: str = "Fragment"

    @classmethod
    def create(cls, *children, **props):
        return rx.script(
            """
            if (typeof window !== "undefined") {
                import("/node_modules/@codegouvfr/react-dsfr/spa.js")
                    .then(mod => mod.startReactDsfr({ defaultColorScheme: "system" }))
                    .catch(e => console.error("DSFR init error", e));
            }
            """,
            type="module",
        )


class DsfrHeader(rx.Component):
    """DSFR Header component (Vite + React Router)."""

    tag: str = "DsfrHeaderWrapper"
    lib_dependencies: list[str] = ["@codegouvfr/react-dsfr"]

    def _get_custom_code(self) -> str:
        return """
import { lazy, Suspense } from "react";
const reflexResolveDsfrHeader = (mod, name) => {
    const comp = mod[name] || (mod.default && mod.default[name]) || (mod.default && mod.default.default) || mod.default || mod;
    return { default: comp };
};
const LazyDsfrHeader = lazy(() => import("@codegouvfr/react-dsfr/Header").then(mod => reflexResolveDsfrHeader(mod, "Header")));
export function DsfrHeaderWrapper(props) {
    return <Suspense fallback={<div />}><LazyDsfrHeader {...props} /></Suspense>;
}
"""

    brand_top: rx.Var[str]
    service_title: rx.Var[str]
    service_tagline: rx.Var[str]
    home_link_props: rx.Var[dict]


class DsfrFooter(rx.Component):
    """DSFR Footer component (Vite + React Router)."""

    tag: str = "DsfrFooterWrapper"
    lib_dependencies: list[str] = ["@codegouvfr/react-dsfr"]

    def _get_custom_code(self) -> str:
        return """
import { lazy as reflexLazyFtr, Suspense as ReflexSuspenseFtr } from "react";
const reflexResolveDsfrFooter = (mod, name) => {
    const comp = mod[name] || (mod.default && mod.default[name]) || (mod.default && mod.default.default) || mod.default || mod;
    return { default: comp };
};
const LazyDsfrFooter = reflexLazyFtr(() => import("@codegouvfr/react-dsfr/Footer").then(mod => reflexResolveDsfrFooter(mod, "Footer")));
export function DsfrFooterWrapper(props) {
    return <ReflexSuspenseFtr fallback={<div />}><LazyDsfrFooter {...props} /></ReflexSuspenseFtr>;
}
"""

    brand_top: rx.Var[str]
    accessibility: rx.Var[str]
    content_description: rx.Var[str]
    home_link_props: rx.Var[dict]


def dsfr_header() -> rx.Component:
    """Render DSFR Header."""
    return DsfrHeader.create(
        brand_top="République\\nFrançaise",
        service_title="RAG Facile",
        service_tagline="Assistant RAG pour les services publics",
        home_link_props={"href": "/", "title": "Accueil - RAG Facile"},
    )


def dsfr_footer() -> rx.Component:
    """Render DSFR Footer."""
    return DsfrFooter.create(
        brand_top="République\\nFrançaise",
        accessibility="non compliant",
        content_description=(
            "RAG Facile est un starter kit open source pour construire "
            "des assistants RAG pour les services publics français."
        ),
        home_link_props={"href": "/", "title": "Accueil"},
    )
