"""
main.py - DriftLens CLI.

Evaluates LLM awareness of architectural smells by injecting smells into Python
repos at four severity tiers and comparing Gemini vs static analysis detection.

Usage:
    python main.py [options]
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

import git
from config import REPO_CONFIGS, SEVERITY_TIERS
from injector import inject_snapshot
from llm_interface import run_llm
from oracle_runner import install_repo_deps, run_oracle
from reporter import generate_report

BASE = Path(__file__).parent
REPOS_DIR = BASE / "repos"
SNAPSHOTS_DIR = BASE / "snapshots"
OUTPUT_DIR = BASE / "output"


def _parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="DriftLens: LLM architectural smell detection evaluation."
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        default=list(REPO_CONFIGS.keys()),
        choices=list(REPO_CONFIGS.keys()),
        metavar="REPO",
        help="Repos to process (default: all).",
    )
    parser.add_argument(
        "--severity",
        nargs="+",
        default=SEVERITY_TIERS,
        choices=SEVERITY_TIERS,
        metavar="TIER",
        help="Severity tiers to run (default: all).",
    )
    parser.add_argument(
        "--gemini-key",
        default=os.environ.get("GEMINI_API_KEY", ""),
        help="Gemini API key (falls back to GEMINI_API_KEY env var).",
    )
    parser.add_argument("--skip-clone", action="store_true", help="Skip git clone step.")
    parser.add_argument("--skip-inject", action="store_true", help="Skip injection step.")
    parser.add_argument("--skip-oracle", action="store_true", help="Skip oracle runner step.")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM interface step.")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Run reporter only on existing results, skip all other steps.",
    )
    return parser.parse_args()


def _clone_repo(repo_cfg: dict) -> Path:
    """Clone a repo if the target directory does not already exist."""
    dest = REPOS_DIR / repo_cfg["name"]
    if dest.exists():
        print(f"  Already cloned: {dest}")
    else:
        print(f"  Cloning {repo_cfg['url']} -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(repo_cfg["url"], dest)
    return dest


def _run_pipeline(args: argparse.Namespace) -> None:
    """Execute the full DriftLens pipeline based on CLI flags."""
    repos = args.repos
    tiers = args.severity
    api_key = args.gemini_key
    skip_llm = args.skip_llm or args.report_only
    skip_clone = args.skip_clone or args.report_only
    skip_inject = args.skip_inject or args.report_only
    skip_oracle = args.skip_oracle or args.report_only

    if not skip_llm and not api_key:
        print(
            "ERROR: GEMINI_API_KEY is not set and --skip-llm was not passed. "
            "Export GEMINI_API_KEY or pass --gemini-key.",
            file=sys.stderr,
        )
        sys.exit(1)

    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not skip_clone:
        print("[1/5] Cloning repos...")
        for repo_name in repos:
            _clone_repo(REPO_CONFIGS[repo_name])
    else:
        print("[1/5] Cloning repos... (skipped)")

    if not skip_inject:
        for repo_name in repos:
            print(f"[2/5] Running injector ({repo_name} x {len(tiers)} tiers)...")
            repo_cfg = REPO_CONFIGS[repo_name]
            package_path = REPOS_DIR / repo_name / repo_cfg["package_subpath"]
            for tier in tiers:
                try:
                    inject_snapshot(package_path, tier, SNAPSHOTS_DIR / repo_name / tier, repo_name, repo_cfg)
                except Exception as exc:
                    print(f"  ERROR injecting {repo_name}/{tier}: {exc} - continuing.", file=sys.stderr)
    else:
        print("[2/5] Running injector... (skipped)")

    deps_installed = set()
    if not skip_oracle:
        for repo_name in repos:
            print(f"[3/5] Running oracle ({repo_name} x {len(tiers)} tiers)...")
            repo_cfg = REPO_CONFIGS[repo_name]
            if repo_name not in deps_installed:
                install_repo_deps(repo_cfg["install_deps"])
                deps_installed.add(repo_name)
            for tier in tiers:
                snap_path = SNAPSHOTS_DIR / repo_name / tier
                if not snap_path.exists():
                    print(f"  SKIP: snapshot missing for {repo_name}/{tier}", file=sys.stderr)
                    continue
                try:
                    run_oracle(snap_path, repo_cfg, repo_name, tier)
                except Exception as exc:
                    print(f"  ERROR in oracle {repo_name}/{tier}: {exc} - continuing.", file=sys.stderr)
    else:
        print("[3/5] Running oracle... (skipped)")

    if not skip_llm:
        for repo_name in repos:
            print(f"[4/5] Running LLM interface ({repo_name} x {len(tiers)} tiers)...")
            for tier in tiers:
                snap_path = SNAPSHOTS_DIR / repo_name / tier
                if not snap_path.exists():
                    print(f"  SKIP: snapshot missing for {repo_name}/{tier}", file=sys.stderr)
                    continue
                try:
                    run_llm(snap_path, repo_name, tier, api_key)
                except Exception as exc:
                    print(f"  ERROR in LLM {repo_name}/{tier}: {exc} - continuing.", file=sys.stderr)
    else:
        print("[4/5] Running LLM interface... (skipped)")

    print("[5/5] Generating report...")
    generate_report(SNAPSHOTS_DIR, OUTPUT_DIR, list(REPO_CONFIGS.keys()))

    print(
        f"\nDone. Output written to "
        f"{OUTPUT_DIR / 'driftlens_report.json'} and "
        f"{OUTPUT_DIR / 'driftlens_report.md'}"
    )


def main() -> None:
    """Entry point for the DriftLens CLI."""
    args = _parse_args()
    _run_pipeline(args)


if __name__ == "__main__":
    main()
