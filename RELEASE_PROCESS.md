# Release process

A release means the new version is on the **Steam Workshop** (item 3814944518). In-game testing comes after release.

1. **Bump and repackage.** Set the new version in `data/island.json`, `mod/.metadata/metadata.json` and `data/main_overlay.json` (`base_release`). Run `python tools/refresh_overlay_bundle.py --promote-version`, then `python tools/verify_prepared_bundle.py`.
2. **Notes.** Add the version to `RELEASE_NOTES.md`, `RELEASE_NOTES_<ver>.md`, `PLAYER_README.md`, `README.md`, `STEAM_CHANGELOG.txt` and `STEAM_DESCRIPTION.txt` (LF, under 8000 bytes). Write the Workshop change notes to `build/release-<ver without dots>/<ver>.bbcode`.
3. **Branch and PR.** Commit on `release/v<ver>`, push to GitHub (`origin`) and open a PR into `main`. Pushing a `release/**` branch that changes `.release/manifest.json` runs `publish-release.yml`, which publishes the GitHub release and `v<ver>` tag.
4. **Steam Workshop.** With EU5 closed and Steam running as the Workshop owner, run `powershell -ExecutionPolicy Bypass -File tools/Release-Steam.ps1`. It clean-exports `HEAD`, runs the installer in an isolated profile and compares it with the packaged zip. It then installs into the active profile, updates the Workshop description and change notes, and uploads with `pdx-workshop-manager`. Receipts and logs go to `build/release-<ver>/`; the script resumes from the last completed step.
5. **Merge.** Merge the PR into `main`.
