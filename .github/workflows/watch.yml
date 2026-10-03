name: gamba-ticket-watch

on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Check ticket page
        env:
          WATCH_URL: ${{ secrets.WATCH_URL }}
          NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
        run: python gamba_check.py
      - name: Save state
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add state.txt || true
          git diff --cached --quiet || (git commit -m "update state" && git push)
