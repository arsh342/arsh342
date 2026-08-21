import json
import os
import urllib.request
from datetime import datetime, timezone

USERNAME = os.environ.get("USER_NAME", "arsh342")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
GRAPHQL = """
query($login: String!) {
  user(login: $login) {
    name
    login
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        nameWithOwner
        stargazerCount
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalRepositoriesWithContributedCommits
    }
  }
}
"""

def github_graphql(query=GRAPHQL, variables=None):
    payload = json.dumps({
        "query": query,
        "variables": variables or {"login": USERNAME},
    }).encode()

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "arsh342-profile-readme",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)

    if "errors" in result:
        messages = "; ".join(
            error.get("message", "Unknown GraphQL error")
            for error in result["errors"]
        )
        raise RuntimeError(f"GitHub GraphQL error: {messages}")

    return result["data"]

def account_age(created_at):
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    years = now.year - created.year
    months = now.month - created.month
    days = now.day - created.day

    if days < 0:
        months -= 1
        previous_month = now.month - 1 or 12
        previous_year = now.year if now.month > 1 else now.year - 1
        if previous_month in (1, 3, 5, 7, 8, 10, 12):
            days += 31
        elif previous_month in (4, 6, 9, 11):
            days += 30
        else:
            days += 29 if previous_year % 4 == 0 else 28

    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"

def fmt(value):
    return f"{value:,}"

def main():
    data = github_graphql()
    user = data["user"]
    repos = user["repositories"]["nodes"]

    stars = sum(repo["stargazerCount"] for repo in repos)
    contributions = user["contributionsCollection"]

    values = {
        "USERNAME": user["login"],
        "REPOS": fmt(user["repositories"]["totalCount"]),
        "CONTRIBUTED": fmt(contributions["totalRepositoriesWithContributedCommits"]),
        "STARS": fmt(stars),
        "COMMITS": fmt(contributions["totalCommitContributions"]),
        "FOLLOWERS": fmt(user["followers"]["totalCount"]),
    }

    for theme in ("light", "dark"):
        template = open(f"assets/{theme}_mode.svg", encoding="utf-8").read()
        for key, value in values.items():
            template = template.replace(f"{{{key}}}", value)
        open(f"{theme}_mode.svg", "w", encoding="utf-8").write(template)

if __name__ == "__main__":
    main()
