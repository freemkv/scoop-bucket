# freemkv Scoop bucket

[Scoop](https://scoop.sh) manifests for [freemkv](https://freemkv.org) on Windows.

```powershell
scoop bucket add freemkv https://github.com/freemkv/scoop-bucket
scoop install freemkv          # desktop app + `freemkv` command
```

| Manifest | What it installs |
| --- | --- |
| `freemkv` | Desktop app (Start menu shortcut) and the `freemkv` command |
| `freemkv-cli` | Command line only (`freemkv`). Install this or `freemkv`, not both. |
| `freemkv-flash` | Firmware flasher: desktop app and the `freemkv-flash` command |
| `freemkv-fw` | Firmware modification tool: desktop app and the `freemkv-fw` command |

x64 and ARM64 are both supported where the release ships them.

## Maintenance

Manifests are generated, not edited by hand. `bin/generate.py` rebuilds
`bucket/*.json` from the latest GitHub releases, covering every architecture
the release carries and taking hashes from the `.sha256` files. The Excavator
workflow runs it every 4 hours, then runs Scoop's standard checkver and
autoupdate. CI fails if the manifests no longer match the latest releases.
