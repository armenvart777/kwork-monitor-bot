import asyncio
import aiohttp
import ssl
import certifi
import json
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KworkProject:
    id: int
    name: str
    description: str
    price_limit: int
    possible_price_limit: int
    time_left: str
    offers_count: int
    category_id: int
    hire_percent: int
    url: str


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


def _extract_json_object(text: str, start_pos: int) -> dict | None:
    """Extract a JSON object from text starting at start_pos using brace counting."""
    brace_start = text.find("{", start_pos)
    if brace_start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(brace_start, min(brace_start + 500_000, len(text))):
        ch = text[i]

        if escape_next:
            escape_next = False
            continue

        if ch == "\\":
            if in_string:
                escape_next = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace_start : i + 1])
                except json.JSONDecodeError:
                    return None

    return None


async def fetch_kwork_projects(categories: list[int], max_retries: int = 3) -> list[KworkProject]:
    """Fetch projects from Kwork exchange with retry on failure."""
    projects = []

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        for cat_id in categories:
            for attempt in range(1, max_retries + 1):
                try:
                    url = f"https://kwork.ru/projects?c={cat_id}"
                    async with session.get(url, headers=HEADERS) as resp:
                        if resp.status != 200:
                            logger.warning(
                                "Kwork returned status %d for category %d (attempt %d/%d)",
                                resp.status, cat_id, attempt, max_retries,
                            )
                            if attempt < max_retries:
                                await asyncio.sleep(2 * attempt)
                                continue
                            break

                        html = await resp.text()
                        page_projects = _parse_projects_from_html(html)
                        projects.extend(page_projects)
                        break  # success

                except Exception as e:
                    logger.error(
                        "Error fetching category %d (attempt %d/%d): %s",
                        cat_id, attempt, max_retries, e,
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(2 * attempt)
                    continue

    return projects


def _parse_projects_from_html(html: str) -> list[KworkProject]:
    """Parse projects from embedded wantsListData in the Kwork HTML page."""
    projects = []

    patterns = [
        r"wantsListData\s*=\s*",
        r"wantsListData\s*:\s*",
        r'"wantsListData"\s*:\s*',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if not match:
            continue

        data = _extract_json_object(html, match.end() - 1)
        if not data:
            continue

        items = []
        if "pagination" in data:
            items = data["pagination"].get("data", [])
        elif "data" in data:
            items = data["data"]

        for item in items:
            try:
                project = KworkProject(
                    id=int(item.get("id", 0)),
                    name=item.get("name", "").strip(),
                    description=item.get("description", "").strip(),
                    price_limit=int(float(item.get("priceLimit", 0))),
                    possible_price_limit=int(
                        float(item.get("possiblePriceLimit", 0))
                    ),
                    time_left=item.get("timeLeft", ""),
                    offers_count=int(item.get("wantGetSumOrderCount", 0)),
                    category_id=int(item.get("category_id", 0)),
                    hire_percent=int(item.get("hirePercent", 0)),
                    url=f"https://kwork.ru/new_offer?project={item.get('id', 0)}",
                )
                if project.id and project.name:
                    projects.append(project)
            except (ValueError, TypeError) as e:
                logger.warning("Error parsing project item: %s", e)
                continue

        if projects:
            break

    if not projects:
        logger.warning("Could not extract projects from Kwork HTML (%d chars)", len(html))

    return projects


def filter_projects(
    projects: list[KworkProject],
    keywords: list[str],
    min_budget: int = 0,
    max_offers: int = 0,
) -> list[KworkProject]:
    """Filter projects by keywords, minimum budget, and max offers count."""
    filtered = []

    for project in projects:
        if min_budget > 0 and project.price_limit < min_budget:
            continue

        if max_offers > 0 and project.offers_count > max_offers:
            continue

        text = f"{project.name} {project.description}".lower()
        if any(kw.lower() in text for kw in keywords):
            filtered.append(project)

    return filtered
