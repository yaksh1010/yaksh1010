"""Draws the pixel "player stats" card from live GitHub data.

Usage: GITHUB_TOKEN=... python3 scripts/stats.py <output-dir> [login]
"""

import datetime
import json
import os
import sys
import urllib.request

from build import C, frame, pixels, ptext, svg
from pixelfont import text_width

SHORT_NAMES = {"Jupyter Notebook": "Jupyter", "Objective-C": "Obj-C", "JavaScript": "JS", "TypeScript": "TS"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    contributionsCollection { contributionCalendar { totalContributions } }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}
"""


def fetch(login, token):
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "pixel-profile"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise SystemExit(f"GitHub API error: {payload['errors']}")
    return payload["data"]["user"]


def draw(user, login):
    W, H = 960, 260
    repos = user["repositories"]
    stars = sum(node["stargazerCount"] for node in repos["nodes"])
    languages = {}
    for node in repos["nodes"]:
        for edge in node["languages"]["edges"]:
            name = edge["node"]["name"]
            entry = languages.setdefault(name, {"size": 0, "color": edge["node"]["color"] or C["dim"]})
            entry["size"] += edge["size"]
    total = sum(entry["size"] for entry in languages.values()) or 1
    top = sorted(languages.items(), key=lambda item: -item[1]["size"])[:6]

    body = [frame(0, 0, W, H, fill="#100e26")]
    since = user["createdAt"][:4]
    body.append(ptext(f"PLAYER {login.upper()}", 32, 28, 3, C["white"]))
    body.append(ptext(f"ON GITHUB SINCE {since}", 32, 60, 2, C["dim"]))

    stats = [
        ("PUBLIC REPOS", repos["totalCount"], C["cyan"]),
        ("STARS EARNED", stars, C["yellow"]),
        ("CONTRIBUTIONS 1Y", user["contributionsCollection"]["contributionCalendar"]["totalContributions"], C["green"]),
        ("FOLLOWERS", user["followers"]["totalCount"], C["pink"]),
    ]
    for i, (label, value, color) in enumerate(stats):
        x, y = 32 + (i % 2) * 250, 96 + (i // 2) * 76
        body.append(frame(x, y, 236, 64, 3, fill="#1a1638", edge="#2c2760", shadow=False))
        body.append(ptext(label, x + 14, y + 12, 2, C["dim"]))
        body.append(ptext(str(value), x + 14, y + 30, 3, color))

    # Languages as a segmented pixel bar plus a legend.
    lx, ly, lw = 560, 32, 368
    body.append(ptext("LANGUAGES", lx, ly, 3, C["white"]))
    x = lx
    for index, (name, entry) in enumerate(top):
        width = lw * entry["size"] / total if index < len(top) - 1 else lx + lw - x
        width = max(4, round(width / 4) * 4)
        body.append(f'<rect x="{x}" y="{ly + 34}" width="{min(width, lx + lw - x)}" height="20" fill="{entry["color"]}"/>')
        x += width
    if x < lx + lw:
        body.append(f'<rect x="{x}" y="{ly + 34}" width="{lx + lw - x}" height="20" fill="#3a3570"/>')
    body.append("".join(f'<rect x="{bx}" y="{ly + 34}" width="2" height="20" fill="#100e26"/>' for bx in range(lx + 6, lx + lw, 8)))
    for index, (name, entry) in enumerate(top):
        cx, cy = lx + (index % 2) * 190, ly + 74 + (index // 2) * 30
        body.append(pixels([".#.", "###", ".#."], cx, cy, 5, {"#": entry["color"]}))
        short = SHORT_NAMES.get(name, name)[:10].upper()
        label = f"{short} {entry['size'] * 100 / total:.0f}%"
        body.append(ptext(label, cx + 22, cy + 1, 2, C["white"]))

    updated = datetime.date.today().isoformat()
    body.append(ptext(f"UPDATED {updated}", W - 24 - text_width(f"UPDATED {updated}", 2), H - 30, 2, "#4c4785"))
    return svg(W, H, "".join(body), "", f"GitHub stats for {login}: {repos['totalCount']} public repos, {stars} stars")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    login = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITHUB_REPOSITORY_OWNER", "yaksh1010")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "stats.svg"), "w") as f:
        f.write(draw(fetch(login, token), login))
    print(f"{out}/stats.svg")


if __name__ == "__main__":
    main()
