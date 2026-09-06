# cartoon-xiaban v0.2.0

## Published installer

```bash
bash <(curl -fsSL 'https://skill.vyibc.com/install-cartoon-xiaban.sh?ts=20260906063744') codex
```

Omit `codex` for the tool-selection menu. Installing updates this named skill only; an existing installation is moved to a timestamped backup first. It does not install models or cloud credentials.

- Package: https://skill.vyibc.com/cartoon-xiaban/release/cartoon-xiaban-20260906063744.zip
- SHA-256: `aea2b27dcbc19530ea05494e52d18873536c03ff29c4dcabb0984e661a2ecf72`
- Publisher: https://github.com/ChangfengHU/skill-publisher
- Publisher base revision: `e8a2f02c69af68ecd5b9247707d5b04b4ccb3612`
- Local safety adjustment: generated installers move the existing named skill to a timestamped backup under the hidden .backups directory instead of deleting it. No upstream repository was changed.
- Reviewed SOP contract included; it is optional adapter metadata, not an independently deployed video-generation service.

No personal audio, reference voice cache, private behavior records, credentials, third-party tracks, model weights or fonts were uploaded. Current visual direction is approved; voice and music remain auditions, and comedy writing remains an improvement priority.

Repository: https://github.com/ChangfengHU/cartoon-video-skills

Source publication completed on 2026-09-06. The `main` branch was pushed using a credential retrieved from the private vault, and the remote commit was verified against the local commit. Credentials were not written to the repository or persisted by the publication helper. CDN publication and package installation were also verified independently.
