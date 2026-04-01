"""Convert page blueprints into structured scenario ideas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set
from urllib.parse import urlsplit, urlunsplit

LOGIN_KEYWORDS = {"user", "username", "email", "login"}
PASSWORD_KEYWORDS = {"pass", "password", "pwd"}
CHECKOUT_KEYWORDS = {"checkout", "payment", "card"}
SEARCH_KEYWORDS = {"search", "query", "filter"}


@dataclass
class ScenarioIdea:
    title: str
    requirement: str
    source_url: str
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)

    def as_requirement(self) -> str:
        details = f"Source: {self.source_url}. Priority: {self.priority}."
        return f"{self.requirement} ({details})"


class ScenarioPlanner:
    """Derives natural language scenario ideas from a blueprint JSON payload."""

    def __init__(self, blueprint: Dict[str, Any]):
        self.blueprint = blueprint
        self.pages: Dict[str, Dict[str, Any]] = blueprint.get("pages", {})
        self._seen_pages: Set[str] = set()
        self._form_signatures: Set[str] = set()
        self._login_generated = False

    def plan(self) -> List[ScenarioIdea]:
        ideas: List[ScenarioIdea] = []
        for url, page in self.pages.items():
            canonical = self._canonical_url(url)
            if not canonical or canonical in self._seen_pages:
                continue
            self._seen_pages.add(canonical)
            ideas.append(self._page_smoke_idea(canonical, page))
            ideas.extend(self._form_ideas(canonical, page.get("forms", [])))
            ideas.extend(self._navigation_ideas(canonical, page.get("links", [])))
        return ideas

    def _form_ideas(self, url: str, forms: Iterable[Dict[str, Any]]) -> List[ScenarioIdea]:
        ideas: List[ScenarioIdea] = []
        for form in forms:
            fields: List[Dict[str, Any]] = form.get("fields", [])
            field_names = [self._field_label(field) for field in fields]
            signature = self._form_signature(field_names)
            if signature in self._form_signatures:
                continue
            self._form_signatures.add(signature)
            tags = ["form"]
            priority = "medium"
            title = f"Validate form at {url}"
            requirement = self._default_form_requirement(field_names, url)

            if self._looks_like_login(fields):
                if self._login_generated:
                    continue
                self._login_generated = True
                title = "Successful login flow"
                requirement = (
                    "Exercise the login form ensuring valid users authenticate successfully "
                    "and are redirected to inventory."
                )
                tags.extend(["login", "critical"])
                priority = "high"
            elif self._looks_like_checkout(fields):
                title = "Checkout payment capture"
                requirement = (
                    "Submit the checkout form with valid payment details and confirm the order summary."
                )
                tags.extend(["checkout", "critical"])
                priority = "high"
            elif self._looks_like_search(fields):
                title = "Catalog search filtering"
                requirement = (
                    "Use the search/filter controls to narrow inventory results and ensure relevant items appear."
                )
                tags.append("search")
                priority = "medium"

            ideas.append(
                ScenarioIdea(
                    title=title,
                    requirement=requirement,
                    source_url=url,
                    priority=priority,
                    tags=sorted(set(tags)),
                )
            )
        return ideas

    def _navigation_ideas(self, url: str, links: Iterable[str]) -> List[ScenarioIdea]:
        unique = sorted(
            {
                self._canonical_url(link)
                for link in links
                if self._canonical_url(link) and self._canonical_url(link) != url
            }
        )
        ideas: List[ScenarioIdea] = []
        for link in unique[:10]:  # guard runaway link graphs
            requirement = (
                f"Navigate from {url} to {link} and verify the destination page loads with expected title."
            )
            ideas.append(
                ScenarioIdea(
                    title=f"Navigate to {link}",
                    requirement=requirement,
                    source_url=url,
                    priority="low",
                    tags=["navigation"],
                )
            )
        return ideas

    @staticmethod
    def _page_smoke_idea(url: str, page: Dict[str, Any]) -> ScenarioIdea:
        title = page.get("title") or "Unnamed page"
        status = page.get("status")
        requirement = (
            f"Ensure the page at {url} responds with HTTP {status or '200'} and displays the title '{title}'."
        )
        return ScenarioIdea(
            title=f"Smoke check for {title}",
            requirement=requirement,
            source_url=url,
            priority="medium",
            tags=["smoke"],
        )

    @staticmethod
    def _canonical_url(url: str) -> str:
        if not url:
            return ""
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    @staticmethod
    def _form_signature(field_names: List[str]) -> str:
        normalised = [name.strip().lower() for name in field_names if name]
        return "|".join(sorted(normalised))

    @staticmethod
    def _field_label(field: Dict[str, Any]) -> str:
        return field.get("name") or field.get("placeholder") or field.get("field_type") or "field"

    @staticmethod
    def _looks_like_login(fields: Iterable[Dict[str, Any]]) -> bool:
        names = [ScenarioPlanner._field_label(field).lower() for field in fields]
        has_user = any(any(keyword in name for keyword in LOGIN_KEYWORDS) for name in names)
        has_pass = any(any(keyword in name for keyword in PASSWORD_KEYWORDS) for name in names)
        return has_user and has_pass

    @staticmethod
    def _looks_like_checkout(fields: Iterable[Dict[str, Any]]) -> bool:
        names = [ScenarioPlanner._field_label(field).lower() for field in fields]
        return any(keyword in name for name in names for keyword in CHECKOUT_KEYWORDS)

    @staticmethod
    def _looks_like_search(fields: Iterable[Dict[str, Any]]) -> bool:
        names = [ScenarioPlanner._field_label(field).lower() for field in fields]
        return any(keyword in name for name in names for keyword in SEARCH_KEYWORDS)

    @staticmethod
    def _default_form_requirement(field_names: List[str], url: str) -> str:
        readable = ", ".join(name or "field" for name in field_names)
        return f"Submit the form on {url} covering fields: {readable}."