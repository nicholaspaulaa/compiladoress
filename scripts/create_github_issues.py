#!/usr/bin/env python3
"""Create milestones, labels, and issues from docs/PLAN-GITHUB-ISSUES.md."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "nicholaspaulaa/compiladoress"
GH = r"C:\Program Files\GitHub CLI\gh.exe"
ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "PLAN-GITHUB-ISSUES.md"

MILESTONES = [
    (
        "Sprint 1 — Foundation & Auth",
        "Estrutura mínima: Docker Compose, Supabase, login, JWT, health. "
        "DoD: clone → docker compose up → login → health verde.",
    ),
    (
        "Sprint 2 — Editor & NASM Panel",
        "Monaco + tokenizer SIMPLES + layout 3 painéis. Run mockado.",
    ),
    (
        "Sprint 3 — Compilation Pipeline",
        "simplesc → nasm → ld via REST, erros como markers.",
    ),
    (
        "Sprint 4 — Interactive Execution",
        "WebSocket + PTY + xterm.js + leia E2E.",
    ),
    (
        "Sprint 5 — Hardening & Observability",
        "Stop, timeouts, sandbox, rate limit, métricas, auditoria.",
    ),
    (
        "Sprint 6 — Polish & (Opcional) Deploy",
        "E2E, cobertura, docs, demo, deploy opcional.",
    ),
]

LABELS = [
    ("sprint-1", "0E8A16", "Sprint 1"),
    ("sprint-2", "1D76DB", "Sprint 2"),
    ("sprint-3", "5319E7", "Sprint 3"),
    ("sprint-4", "D93F0B", "Sprint 4"),
    ("sprint-5", "B60205", "Sprint 5"),
    ("sprint-6", "FBCA04", "Sprint 6"),
    ("frontend", "7057FF", "React, Monaco, xterm, UI"),
    ("backend", "0075CA", "Flask, APIs, WebSocket, compilação"),
    ("devops", "006B75", "Docker, Nginx, CI, deploy, GitHub"),
    ("docs", "C5DEF5", "Documentação, README, apresentação"),
    ("security", "E11D21", "Sandbox, JWT, rate limit, auditoria"),
]


def run(args: list[str], *, input_text: str | None = None) -> str:
    cmd = [GH, *args]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout.strip()


def parse_issues(plan_text: str) -> list[dict]:
    issues: list[dict] = []
    blocks = re.split(r"#### Issue \d+\.\d+\s*\n", plan_text)
    for block in blocks[1:]:
        title_m = re.search(r"- \*\*Título:\*\* `([^`]+)`", block)
        labels_m = re.search(r"- \*\*Labels:\*\* `([^`]+)`, `([^`]+)`", block)
        body_m = re.search(
            r"\*\*Body:\*\*\s*\n+```markdown\n(.*?)```", block, re.DOTALL
        )
        if not (title_m and labels_m and body_m):
            raise ValueError(f"Could not parse issue block:\n{block[:200]}...")
        sprint_label = labels_m.group(1)
        type_label = labels_m.group(2)
        milestone_idx = int(sprint_label.split("-")[1]) - 1
        issues.append(
            {
                "title": title_m.group(1),
                "labels": [sprint_label, type_label],
                "milestone": MILESTONES[milestone_idx][0],
                "body": body_m.group(1).strip(),
            }
        )
    return issues


def create_milestones() -> dict[str, int]:
    """Return milestone title -> GitHub milestone number."""
    mapping: dict[str, int] = {}
    for title, description in MILESTONES:
        out = run(
            [
                "api",
                f"repos/{REPO}/milestones",
                "-f",
                f"title={title}",
                "-f",
                f"description={description}",
            ]
        )
        data = json.loads(out)
        mapping[title] = data["number"]
        print(f"Milestone #{data['number']}: {title}")
    return mapping


def create_labels() -> None:
    for name, color, desc in LABELS:
        try:
            run(
                [
                    "label",
                    "create",
                    name,
                    "--color",
                    color,
                    "--description",
                    desc,
                    "--repo",
                    REPO,
                ]
            )
            print(f"Label created: {name}")
        except RuntimeError as e:
            if "already exists" in str(e).lower():
                print(f"Label exists: {name}")
            else:
                raise


def create_issues(issues: list[dict]) -> list[dict]:
    created: list[dict] = []
    for issue in issues:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(issue["body"])
            body_path = f.name
        try:
            url = run(
                [
                    "issue",
                    "create",
                    "--repo",
                    REPO,
                    "--title",
                    issue["title"],
                    "--body-file",
                    body_path,
                    "--label",
                    ",".join(issue["labels"]),
                    "--milestone",
                    issue["milestone"],
                ]
            )
        finally:
            Path(body_path).unlink(missing_ok=True)
        num_m = re.search(r"/issues/(\d+)", url)
        num = int(num_m.group(1)) if num_m else 0
        created.append({"number": num, "title": issue["title"], "url": url})
        print(f"Issue #{num}: {issue['title']}")
    return created


def write_progress(created: list[dict], issues: list[dict]) -> None:
    sprint_headers = [m[0] for m in MILESTONES]
    lines = [
        "# Progress — Simples Editor",
        "",
        "> Atualizar conforme issues forem fechadas. "
        "Gerado por `scripts/create_github_issues.py`.",
        "",
    ]
    idx = 0
    counts = [9, 7, 7, 7, 9, 8]
    for header, count in zip(sprint_headers, counts):
        lines.append(f"## {header}")
        for _ in range(count):
            c = created[idx]
            lines.append(f"- [ ] #{c['number']} — {c['title']}")
            idx += 1
        lines.append("")
    path = ROOT / "PROGRESS.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    if not PLAN.is_file():
        sys.exit(f"Plan not found: {PLAN}")
    plan_text = PLAN.read_text(encoding="utf-8")
    issues = parse_issues(plan_text)
    if len(issues) != 47:
        sys.exit(f"Expected 47 issues, parsed {len(issues)}")

    print("Creating milestones...")
    milestone_map = create_milestones()
    print("Creating labels...")
    create_labels()
    print("Creating issues...")
    _ = milestone_map
    created = create_issues(issues)
    write_progress(created, issues)
    print("Done.")


if __name__ == "__main__":
    main()
