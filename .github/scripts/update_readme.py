"""Refreshes the dynamic parts of the profile README.

- PROJECT: the most recently pushed public repo (not a fork, not this repo)
"""
import json
import os
import re
import urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]
README = "README.md"


def api(url):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def replace_section(text, name, content):
    pattern = rf"(<!-- {name}:START -->).*?(<!-- {name}:END -->)"
    return re.sub(pattern, lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", text, flags=re.S)


def latest_project():
    repos = api(f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30")
    repo = next((r for r in repos if not r["fork"] and r["name"].lower() != USER.lower()), None)
    if repo is None:
        return "- 🔭 Currently working on: something new, stay tuned!"
    line = f"- 🔭 Currently working on: **[{repo['name']}]({repo['html_url']})**"
    if repo["description"]:
        line += f" — {repo['description']}"
    print("latest project:", repo["name"])
    return line


with open(README, encoding="utf-8") as f:
    readme = f.read()

readme = replace_section(readme, "PROJECT", latest_project())

with open(README, "w", encoding="utf-8") as f:
    f.write(readme)
