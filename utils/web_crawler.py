from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from dataclasses import dataclass, field
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)


@dataclass
class FormField:
    name: str
    field_type: str
    placeholder: str
    label: str = ""
    options: List[str] = field(default_factory=list)


@dataclass
class FormBlueprint:
    action: str
    method: str
    fields: List[FormField] = field(default_factory=list)


@dataclass
class PageBlueprint:
    url: str
    depth: int
    title: str
    status: int
    content_type: str
    parent: Optional[str] = None
    links: List[str] = field(default_factory=list)
    forms: List[FormBlueprint] = field(default_factory=list)
    headings: List[str] = field(default_factory=list)
    buttons: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
    assets: Dict[str, List[str]] = field(default_factory=dict)


class WebCrawler:
    def __init__(
        self,
        base_url: str,
        max_depth: int = 2,
        max_pages: int = 200,
        include_domains: Optional[Iterable[str]] = None,
        exclude_paths: Optional[Iterable[str]] = None,
        timeout: int = 10,
        delay: float = 0.0,
        user_agent: Optional[str] = None,
        respect_robots: bool = True,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = self._normalize_url(base_url.rstrip("/")) or base_url.rstrip("/")
        self.max_depth = max_depth
        self.max_pages = max_pages
        base_domain = urlparse(self.base_url).netloc.lower()
        include_domains = include_domains or {base_domain}
        self.include_domains = {domain.lower() for domain in include_domains}
        self.exclude_paths = set(exclude_paths or [])
        self.timeout = timeout
        self.delay = max(0.0, delay)
        self.respect_robots = respect_robots

        self.session = session or requests.Session()
        default_agent = (
            user_agent
            or "Mozilla/5.0 (compatible; DemoShopCrawler/1.0; +https://demo-shop.local/crawler)"
        )
        self.session.headers.setdefault("User-Agent", default_agent)

        self.robot_parser: Optional[RobotFileParser] = None
        if self.respect_robots:
            self.robot_parser = self._bootstrap_robot_parser()

        self.visited: Set[str] = set()
        self.pending: Set[str] = set()
        self.queue: Deque[Tuple[str, int, Optional[str]]] = deque()
        self.broken_links: Dict[str, int] = {}
        self.errors: Dict[str, str] = {}
        self.pages: Dict[str, PageBlueprint] = {}

    def crawl(self) -> Dict[str, object]:
        self._reset_state()
        started_at = datetime.utcnow()

        self._enqueue(self.base_url, depth=0, parent=None)

        while self.queue and len(self.pages) < self.max_pages:
            current_url, depth, parent = self.queue.popleft()
            self.pending.discard(current_url)
            if current_url in self.visited or depth > self.max_depth:
                continue
            self.visited.add(current_url)

            try:
                page = self._fetch_page(current_url, depth, parent)
            except Exception as exc:  # safeguard against parser edge-cases
                self.errors[current_url] = str(exc)
                LOGGER.debug("Error processing %s: %s", current_url, exc)
                continue

            if page:
                self.pages[current_url] = page
                for link in page.links:
                    self._enqueue(link, depth=depth + 1, parent=current_url)

            if self.delay:
                time.sleep(self.delay)

        completed_at = datetime.utcnow()
        return {
            "started_at": started_at.isoformat() + "Z",
            "started_epoch": started_at.timestamp(),
            "completed_at": completed_at.isoformat() + "Z",
            "completed_epoch": completed_at.timestamp(),
            "seed": self.base_url,
            "visited_count": len(self.visited),
            "broken_links": self.broken_links,
            "errors": self.errors,
            "statistics": self._build_statistics(),
            "site_map": {url: page.links for url, page in self.pages.items()},
            "pages": {url: _page_to_dict(page) for url, page in self.pages.items()},
        }

    def _reset_state(self) -> None:
        self.visited.clear()
        self.pending.clear()
        self.queue.clear()
        self.broken_links.clear()
        self.errors.clear()
        self.pages.clear()

    def _bootstrap_robot_parser(self) -> Optional[RobotFileParser]:
        robots_url = urljoin(self.base_url, "/robots.txt")
        parser = RobotFileParser()
        try:
            parser.set_url(robots_url)
            parser.read()
        except Exception as exc:  # pragma: no cover - network failures vary
            LOGGER.debug("Unable to read robots.txt at %s: %s", robots_url, exc)
            return None
        return parser

    def _enqueue(self, url: str, depth: int, parent: Optional[str]) -> None:
        normalised = self._normalize_url(url)
        if not normalised:
            return
        if normalised in self.visited or normalised in self.pending:
            return
        if depth > self.max_depth:
            return
        if not self._is_allowed(normalised):
            return
        if self.respect_robots and not self._is_robot_allowed(normalised):
            return
        self.queue.append((normalised, depth, parent))
        self.pending.add(normalised)

    def _fetch_page(self, url: str, depth: int, parent: Optional[str]) -> Optional[PageBlueprint]:
        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.RequestException:
            self.broken_links[url] = 0
            return None

        status = response.status_code
        content_type = response.headers.get("Content-Type", "").lower()
        if status >= 400:
            self.broken_links[url] = status
            return None
        if "text/html" not in content_type:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        page = PageBlueprint(
            url=url,
            depth=depth,
            title=(soup.title.string.strip() if soup.title and soup.title.string else ""),
            status=status,
            content_type=content_type,
            parent=parent,
        )

        page.meta = {
            (meta.get("name") or meta.get("property") or "").strip(): meta.get("content", "").strip()
            for meta in soup.find_all("meta")
            if meta.get("content")
        }

        page.forms = [self._parse_form(form) for form in soup.find_all("form")]
        page.inputs = self._extract_inputs(page.forms)
        page.headings = self._extract_headings(soup)
        page.buttons = self._extract_buttons(soup)
        page.assets = self._extract_assets(soup, url)

        links: Set[str] = set()
        for anchor in soup.find_all("a", href=True):
            destination = self._normalize_url(urljoin(url, anchor.get("href", "")))
            if not destination or not self._is_allowed(destination):
                continue
            if self.respect_robots and not self._is_robot_allowed(destination):
                continue
            links.add(destination)

        page.links = sorted(links)
        return page

    def _extract_inputs(self, forms: Iterable[FormBlueprint]) -> List[str]:
        discovered: List[str] = []
        seen: Set[str] = set()
        for form in forms:
            for field in form.fields:
                label = field.label or field.name or field.placeholder or field.field_type
                label = label.strip()
                if not label or label.lower() in seen:
                    continue
                seen.add(label.lower())
                discovered.append(label)
        return discovered

    @staticmethod
    def _extract_headings(soup: BeautifulSoup) -> List[str]:
        headings = [tag.get_text(strip=True) for tag in soup.find_all(["h1", "h2", "h3"]) if tag.get_text(strip=True)]
        return list(dict.fromkeys(headings))

    @staticmethod
    def _extract_buttons(soup: BeautifulSoup) -> List[str]:
        candidates = []
        for element in soup.find_all(["button", "a"]):
            if element.name == "a" and element.get("role") != "button" and "btn" not in (element.get("class") or []):
                continue
            text = element.get_text(strip=True) or element.get("aria-label", "").strip()
            if text:
                candidates.append(text)
        return list(dict.fromkeys(candidates))

    def _extract_assets(self, soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
        stylesheets = {
            self._normalize_url(urljoin(base_url, link.get("href", "")))
            for link in soup.find_all("link", rel=lambda value: value and "stylesheet" in value)
            if link.get("href")
        }
        scripts = {
            self._normalize_url(urljoin(base_url, script.get("src", "")))
            for script in soup.find_all("script", src=True)
            if script.get("src")
        }
        images = {
            self._normalize_url(urljoin(base_url, image.get("src", "")))
            for image in soup.find_all("img", src=True)
            if image.get("src")
        }
        return {
            "stylesheets": sorted(filter(None, stylesheets)),
            "scripts": sorted(filter(None, scripts)),
            "images": sorted(filter(None, images)),
        }

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if parsed.netloc and parsed.netloc.lower() not in self.include_domains:
            return False
        for path in self.exclude_paths:
            if path and parsed.path.startswith(path):
                return False
        return True

    def _is_robot_allowed(self, url: str) -> bool:
        if not self.robot_parser:
            return True
        agent = self.session.headers.get("User-Agent", "*")
        try:
            return self.robot_parser.can_fetch(agent, url)
        except Exception:  # pragma: no cover - depends on parser internals
            return True

    def _parse_form(self, form) -> FormBlueprint:
        action = form.get("action", "").strip()
        method = form.get("method", "get").strip().lower()
        fields: List[FormField] = []
        for input_field in form.find_all(["input", "textarea", "select"]):
            name = (input_field.get("name") or input_field.get("id") or "").strip()
            placeholder = input_field.get("placeholder", "").strip()
            field_type = (input_field.get("type") or input_field.name or "").strip()
            label = self._resolve_label(form, input_field)
            options: List[str] = []
            if input_field.name == "select":
                options = [option.get_text(strip=True) for option in input_field.find_all("option") if option.get_text(strip=True)]
            fields.append(
                FormField(
                    name=name,
                    field_type=field_type,
                    placeholder=placeholder,
                    label=label,
                    options=options,
                )
            )
        return FormBlueprint(action=action, method=method, fields=fields)

    @staticmethod
    def _resolve_label(form, input_field) -> str:
        label_text = ""
        field_id = input_field.get("id")
        if field_id:
            label_tag = form.find("label", attrs={"for": field_id})
            if label_tag and label_tag.get_text(strip=True):
                label_text = label_tag.get_text(strip=True)
        if not label_text and input_field.parent and input_field.parent.name == "label":
            label_text = input_field.parent.get_text(strip=True)
        return label_text

    def _normalize_url(self, url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        query = parsed.query
        if query:
            query_items = parse_qsl(query, keep_blank_values=True)
            query = urlencode(sorted(query_items))
        return urlunparse((parsed.scheme, netloc, path, "", query, ""))

    def _build_statistics(self) -> Dict[str, object]:
        page_count = len(self.pages)
        form_count = sum(len(page.forms) for page in self.pages.values())
        link_count = sum(len(page.links) for page in self.pages.values())
        max_depth_reached = max((page.depth for page in self.pages.values()), default=0)
        unique_domains = sorted({urlparse(url).netloc for url in self.pages})
        average_links = link_count / page_count if page_count else 0
        return {
            "pages_scanned": page_count,
            "forms_detected": form_count,
            "broken_link_count": len(self.broken_links),
            "max_depth_reached": max_depth_reached,
            "unique_domains": unique_domains,
            "average_links_per_page": round(average_links, 2),
        }


def _page_to_dict(page: PageBlueprint) -> Dict[str, object]:
    return {
        "url": page.url,
        "depth": page.depth,
        "title": page.title,
        "status": page.status,
        "content_type": page.content_type,
        "parent": page.parent,
        "links": page.links,
        "forms": [
            {
                "action": form.action,
                "method": form.method,
                "fields": [field.__dict__ for field in form.fields],
            }
            for form in page.forms
        ],
        "headings": page.headings,
        "buttons": page.buttons,
        "inputs": page.inputs,
        "meta": page.meta,
        "assets": page.assets,
    }
