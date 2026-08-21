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
        name
        stargazerCount
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 1) { totalCount }
            }
          }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalRepositoriesWithContributedCommits
      contributionCalendar { totalContributions }
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
        messages = "; ".join(error.get("message", "Unknown GraphQL error") for error in result["errors"])
        raise RuntimeError(f"GitHub GraphQL error: {messages}")

    return result["data"]


def years_months_days(created_at):
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


def repository_loc(owner, repo):
    query = """
    query($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, after: $cursor) {
                edges {
                  node {
                    additions
                    deletions
                    author { user { login } }
                  }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
      }
    }
    """

    additions = 0
    deletions = 0
    cursor = None

    while True:
        data = github_graphql(
            query,
            {"owner": owner, "repo": repo, "cursor": cursor},
        )
        repository = data.get("repository")
        if not repository or not repository.get("defaultBranchRef"):
            break

        target = repository["defaultBranchRef"].get("target")
        history = target.get("history") if target else None
        if not history:
            break

        for edge in history["edges"]:
            commit = edge["node"]
            author = commit.get("author", {}).get("user")
            if author and author.get("login", "").lower() == USERNAME.lower():
                additions += commit["additions"] or 0
                deletions += commit["deletions"] or 0

        if not history["pageInfo"]["hasNextPage"]:
            break
        cursor = history["pageInfo"]["endCursor"]

    return additions - deletions


def main():
    data = github_graphql()
    user = data["user"]
    repos = user["repositories"]["nodes"]

    stars = sum(repo["stargazerCount"] for repo in repos)
    repos_owned = user["repositories"]["totalCount"]

    contribution_data = user["contributionsCollection"]
    commits = contribution_data["totalCommitContributions"]
    contributions = contribution_data["contributionCalendar"]["totalContributions"]
    contributed_repos = contribution_data["totalRepositoriesWithContributedCommits"]
    followers = user["followers"]["totalCount"]
    uptime = years_months_days(user["createdAt"])

    # Net lines changed in commits authored by the profile owner.
    # This mirrors the reference project's LOC concept.
    loc = 0
    for repo in repos:
        owner, name = repo["nameWithOwner"].split("/", 1)
        loc += repository_loc(owner, name)

    values = {
        "USERNAME": user["login"],
        "DISPLAY_NAME": user["name"] or user["login"],
        "UPTIME": uptime,
        "REPOS": fmt(repos_owned),
        "CONTRIBUTED": fmt(contributed_repos),
        "STARS": fmt(stars),
        "COMMITS": fmt(commits),
        "CONTRIBUTIONS": fmt(contributions),
        "FOLLOWERS": fmt(followers),
        "LOC": fmt(loc),
    }

    for theme in ("light", "dark"):
        template = open(f"assets/{theme}_mode.svg", encoding="utf-8").read()
        for key, value in values.items():
            template = template.replace(f"{{{{{key}}}}}", value)
        open(f"{theme}_mode.svg", "w", encoding="utf-8").write(template)


if __name__ == "__main__":
    main()
