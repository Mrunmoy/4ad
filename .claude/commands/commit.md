Review all staged and unstaged changes, then create a git commit following these rules:

1. Stage only the relevant changed files (never use `git add -A` or `git add .`)
2. Write a commit message like a human would — precise, natural, no filler
3. Imperative mood for the subject (e.g., "Add dice roller with explosive six")
4. Keep the subject line under 72 characters
5. The subject should describe *what changed and why* in plain English, not repeat filenames or list every modification
6. Add a body only when the subject alone doesn't explain the reasoning
7. No emojis, no Co-Authored-By, no tags, no prefixes
8. After committing, show the resulting `git log --oneline -1` to confirm
