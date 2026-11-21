"""Refreshes the dynamic parts of the profile README.

- PROJECT: the most recently pushed public repo (not a fork, not this repo)
- STATS: the stats card, hiding every row whose value is 0
"""
import json
import os
import re
import urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]
README = "README.md"

STATS_URL = (
    f"https://github-readme-stats.vercel.app/api?username={USER}&show_icons=true&hide_border=true"
    "&bg_color=fff4d6&title_color=b5651d&icon_color=e8a317&text_color=5a3a1a"
    "&custom_title=Alexandra%27s%20GitHub%20Stats&hide_rank=true"
)

STATS_QUERY = """
query($login: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) { totalCount }
    contributionsCollection { totalCommitContributions }
    repositories(ownerAffiliations: OWNER, first: 100) { nodes { stargazerCount } }
  }
}
"""


def api(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def replace_section(text, name, content):
    pattern = rf"(<!-- {name}:START -->).*?(<!-- {name}:END -->)"
    return re.sub(pattern, lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", text, flags=re.S)


def stats_card():
    user = api("https://api.github.com/graphql", {"query": STATS_QUERY, "variables": {"login": USER}})["data"]["user"]
    counts = {
        "stars": sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "contribs": user["repositoriesContributedTo"]["totalCount"],
    }
    print("stats:", counts)
    hidden = [key for key, value in counts.items() if value == 0]
    url = STATS_URL + (f"&hide={','.join(hidden)}" if hidden else "")
    return f'  <img height="165" src="{url}" alt="GitHub stats"/>'


def latest_project():
    repos = api(f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30")
    repo = next((r for r in repos if not r["fork"] and r["name"].lower() != USER.lower()), None)
    if repo is None:
        return "- 🔭 Currently working on: something new, stay tuned!"
    line = f"- 🔭 Currently working on: **[{repo['name']}]({repo['html_url']})**"
    if repo["description"]:
        line += f" — {repo['description']}"
    if repo["language"]:
        line += f" ({repo['language']})"
    print("latest project:", repo["name"])
    return line


with open(README, encoding="utf-8") as f:
    readme = f.read()

readme = replace_section(readme, "PROJECT", latest_project())
readme = replace_section(readme, "STATS", stats_card())

with open(README, "w", encoding="utf-8") as f:
    f.write(readme)
