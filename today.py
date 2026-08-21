import json
import os
import urllib.request

USERNAME = os.environ.get("USER_NAME", "arsh342")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    followers {
      totalCount
    }
    repositories(ownerAffiliations: OWNER, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
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


def github_graphql():
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USERNAME
        }
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "arsh342-profile"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)

    if "errors" in result:
        messages = "; ".join(
            error.get("message", "Unknown GitHub GraphQL error")
            for error in result["errors"]
        )
        raise RuntimeError(messages)

    return result["data"]["user"]


def fmt(value):
    return f"{value:,}"


def main():
    user = github_graphql()

    repositories = user["repositories"]

    repos = repositories["totalCount"]

    stars = sum(
        repo["stargazerCount"]
        for repo in repositories["nodes"]
    )

    contributions = user["contributionsCollection"]

    contributed = contributions[
        "totalRepositoriesWithContributedCommits"
    ]

    commits = contributions[
        "totalCommitContributions"
    ]

    followers = user["followers"]["totalCount"]

    values = {
        "USERNAME": user["login"],
        "REPOS": fmt(repos),
        "CONTRIBUTED": fmt(contributed),
        "STARS": fmt(stars),
        "FOLLOWERS": fmt(followers),
        "COMMITS": fmt(commits),
    }

    for theme in ("light", "dark"):
        template_path = f"assets/{theme}_mode.svg"
        output_path = f"{theme}_mode.svg"

        with open(template_path, "r", encoding="utf-8") as file:
            svg = file.read()

        for key, value in values.items():
            svg = svg.replace(
                "{" + key + "}",
                value
            )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(svg)


if __name__ == "__main__":
    main()
