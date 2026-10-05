# freemkv Scoop bucket

[Scoop](https://scoop.sh) manifests for [freemkv](https://freemkv.org) on Windows.

```powershell
scoop bucket add freemkv https://github.com/freemkv/scoop-bucket
scoop install freemkv          # desktop app + `freemkv` command line
```

| Manifest | What it installs |
| --- | --- |
| `freemkv` | Desktop app (Start menu shortcut) and the `freemkv` command |
| `freemkv-cli` | Command line only (`freemkv`); install this or `freemkv`, not both |
| `freemkv-flash` | Firmware flasher: desktop app + `freemkv-flash` command |
| `freemkv-fw` | Firmware tool: desktop app + `freemkv-fw` command |

x64 and ARM64 are both supported where the release ships them.

## Maintenance

Manifests are generated, not hand-edited: `bin/generate.py` rebuilds
`bucket/*.json` from the latest GitHub releases (every architecture the release
carries, hashes from the `.sha256` sidecars). The Excavator workflow runs it
every 4 hours, then Scoop's standard checkver/autoupdate.
