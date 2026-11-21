"""Draws the contribution calendar as cheese, with a mouse head that eats it.

Usage: python cheese_mouse.py dist/cheese-mouse.svg
"""
import json
import math
import os
import sys
import urllib.request

CELL = 15
PAD = 20
SPEED = 140  # px per second
TRAVEL = 88  # % of the loop spent eating; the rest refills the cheese

CHEESE = {
    "FIRST_QUARTILE": ("#ffe08a", .6),
    "SECOND_QUARTILE": ("#ffcc4d", .75),
    "THIRD_QUARTILE": ("#f5b014", .9),
    "FOURTH_QUARTILE": ("#d48806", 1.05),
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { weekday contributionLevel } }
      }
    }
  }
}
"""

MOUSE = """
<g id="mouse">
  <circle cx="3" cy="-7" r="4" fill="#a06a35"/><circle cx="3" cy="-7" r="2.2" fill="#f2a5a0"/>
  <circle cx="-4" cy="-6" r="4" fill="#b5773d"/><circle cx="-4" cy="-6" r="2.3" fill="#f2a5a0"/>
  <circle cx="0" cy="0" r="6.5" fill="#b5773d"/>
  <ellipse cx="6" cy="1.5" rx="4" ry="3" fill="#f3d6a8"/>
  <circle cx="9.6" cy="1" r="1.4" fill="#4a2a14"/>
  <ellipse cx="2" cy="-2" rx="1.5" ry="1.8" fill="#fff"/><circle cx="2.5" cy="-2" r=".9" fill="#222"/>
  <ellipse class="chomp" cx="6.5" cy="4" rx="1.8" ry="1.2" fill="#4a2a14"/>
</g>"""


def fetch_weeks(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def render(weeks):
    width = PAD * 2 + len(weeks) * CELL
    height = PAD * 2 + 7 * CELL

    cells, cheeses = [], []
    for w, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = PAD + w * CELL + CELL / 2
            y = PAD + day["weekday"] * CELL + CELL / 2
            cells.append((x, y))
            if day["contributionLevel"] in CHEESE:
                # zig-zag: down on even weeks, up on odd weeks
                order = (w, day["weekday"] if w % 2 == 0 else -day["weekday"])
                cheeses.append((order, x, y, day["contributionLevel"]))
    cheeses.sort()

    mid = PAD + 3.5 * CELL
    points = [(-20, mid)] + [(x, y) for _, x, y, _ in cheeses] + [(width + 20, mid)]
    dist = [0.0]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        dist.append(dist[-1] + math.hypot(x2 - x1, y2 - y1))
    duration = dist[-1] / SPEED / (TRAVEL / 100)
    pct = [d / dist[-1] * TRAVEL for d in dist]

    css = [
        f".k{{animation:{duration:.2f}s linear infinite}}",
        ".chomp{transform-box:fill-box;transform-origin:center;animation:chomp .25s ease-in-out infinite alternate}",
        "@keyframes chomp{from{transform:scaleY(.3)}to{transform:scaleY(1.2)}}",
        f".m{{animation:m {duration:.2f}s linear infinite}}",
        "@keyframes m{"
        + "".join(f"{p:.3f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}" for p, (x, y) in zip(pct, points))
        + f"100%{{transform:translate({points[-1][0]:.1f}px,{points[-1][1]:.1f}px)}}}}",
    ]
    for i, p in enumerate(pct[1:-1]):
        css.append(
            f"@keyframes e{i}{{0%,{p:.3f}%{{transform:scale(1)}}{p + .4:.3f}%,95%{{transform:scale(0)}}100%{{transform:scale(1)}}}}"
        )

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        "<style>" + "".join(css) + "</style>",
        f"<defs>{MOUSE}</defs>",
    ]
    out += [
        f'<rect x="{x - 5.5}" y="{y - 5.5}" width="11" height="11" rx="2.5" fill="#8b949e" opacity=".18"/>'
        for x, y in cells
    ]
    for i, (_, x, y, level) in enumerate(cheeses):
        color, size = CHEESE[level]
        out.append(
            f'<g transform="translate({x} {y}) scale({size})"><g class="k" style="animation-name:e{i}">'
            f'<path d="M-6 4.5H6V-5z" fill="{color}" stroke="#c98a12" stroke-width="1" stroke-linejoin="round"/>'
            f'<circle cx="2.8" cy="1.6" r="1.3" fill="#c98a12" opacity=".55"/></g></g>'
        )
    out.append('<g class="m"><use href="#mouse"/></g>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "dist/cheese-mouse.svg"
    svg = render(fetch_weeks(os.environ["GH_USER"], os.environ["GITHUB_TOKEN"]))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
