"""
repo_finder.py - GitHub repository search for SmellScope dataset expansion.

Queries the GitHub Search API for Python repositories created after
2025-02-01 and writes a JSON array of candidates to disk for
repo_validator.py to process.

Usage:
    python repo_finder.py --token <github_token> --output candidates.json
    python repo_finder.py --token <github_token> --output candidates.json --max 50 --min-stars 5
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

_SEARCH_URL = "https://api.github.com/search/repositories"
_FIELDS = (
    "full_name",
    "html_url",
    "clone_url",
    "created_at",
    "updated_at",
    "size",
    "stargazers_count",
    "default_branch",
)
_QUERY_BASE = "language:Python created:>2025-02-01 size:10..500"
_PER_PAGE = 30
_PAGE_SLEEP = 2


def _build_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def _fetch_page(session: requests.Session, token: str, page: int, query: str) -> dict:
    """Fetch one page of search results. Raises on non-200 response."""
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": _PER_PAGE,
        "page": page,
    }
    response = session.get(_SEARCH_URL, headers=_build_headers(token), params=params)
    if response.status_code == 403:
        reset = response.headers.get("X-RateLimit-Reset", "unknown")
        print(
            f"[repo_finder] Rate limit hit (403). Reset at epoch {reset}.",
            file=sys.stderr,
        )
        response.raise_for_status()
    if response.status_code != 200:
        print(
            f"[repo_finder] ERROR: HTTP {response.status_code} on page {page}.",
            file=sys.stderr,
        )
        response.raise_for_status()
    return response.json()


def _extract_fields(item: dict) -> dict:
    return {field: item.get(field) for field in _FIELDS}


def _print_summary(repo: dict) -> None:
    print(
        f"  {repo['full_name']:<45} "
        f"created={repo['created_at'][:10]}  "
        f"size={repo['size']:>5} KB  "
        f"stars={repo['stargazers_count']}"
    )


def find_candidate_repos(
    token: str, output_path: Path, max_results: int = 50, min_stars: int = 2
) -> list[dict]:
    """
    Search GitHub for candidate Python repos and write results to output_path.

    Returns the list of collected repo dicts.
    """
    query = f"{_QUERY_BASE} stars:>={min_stars}"
    candidates: list[dict] = []
    session = requests.Session()
    page = 1

    print(f"[repo_finder] Searching GitHub (max_results={max_results}, min_stars={min_stars})...")
    print(f"[repo_finder] Query: {query}")

    while len(candidates) < max_results:
        print(f"[repo_finder] Fetching page {page}...")
        try:
            data = _fetch_page(session, token, page, query)
        except requests.HTTPError as exc:
            print(f"[repo_finder] Stopping early: {exc}", file=sys.stderr)
            break

        items = data.get("items", [])
        if not items:
            print("[repo_finder] No more results.")
            break

        for item in items:
            if len(candidates) >= max_results:
                break
            repo = _extract_fields(item)
            candidates.append(repo)
            _print_summary(repo)

        total_count = data.get("total_count", 0)
        fetched_so_far = (page - 1) * _PER_PAGE + len(items)
        if fetched_so_far >= total_count:
            print("[repo_finder] All available results retrieved.")
            break

        page += 1
        time.sleep(_PAGE_SLEEP)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(candidates, indent=2), encoding="utf-8")
    print(f"\n[repo_finder] {len(candidates)} candidate(s) written to {output_path}")
    return candidates


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SmellScope: find candidate Python repos via GitHub Search API."
    )
    parser.add_argument("--token", required=True, help="GitHub personal access token.")
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the candidates JSON file.",
    )
    parser.add_argument(
        "--max",
        dest="max_results",
        type=int,
        default=50,
        metavar="N",
        help="Maximum number of repos to collect (default: 50).",
    )
    parser.add_argument(
        "--min-stars",
        dest="min_stars",
        type=int,
        default=2,
        metavar="N",
        help="Minimum star count to include (default: 2).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    find_candidate_repos(args.token, args.output, args.max_results, args.min_stars)


if __name__ == "__main__":
    main()
