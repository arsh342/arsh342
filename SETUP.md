# arsh342 GitHub Profile

Terminal-style profile README inspired by the Neofetch-style layout of Andrew6rant/Andrew6rant.

## Files

- `README.md` — embeds the light/dark profile SVG
- `today.py` — pulls GitHub statistics through GraphQL
- `light_mode.svg` — light theme
- `dark_mode.svg` — dark theme
- `.github/workflows/update-profile.yml` — updates the SVG daily

## Install

Use this as the contents of your profile repository:

```text
arsh342/arsh342
├── .github/
│   └── workflows/
│       └── update-profile.yml
├── assets/
│   ├── light_mode.svg
│   └── dark_mode.svg
├── README.md
└── today.py
```

The repository must be public and its name must exactly match your GitHub username for GitHub to display it as the profile README.

## Important

The workflow uses the automatically provided `GITHUB_TOKEN`; no personal access token needs to be stored.

The first workflow run generates the real repository, star, commit, contribution, follower, and net line-of-code values.

## Local test

Set a GitHub token and run:

```bash
export GITHUB_TOKEN="your_token"
export USER_NAME="arsh342"
python3 today.py
```

Do not commit a personal access token to the repository.
