# nix-home-manager-config

My nix home-manager config (flake-based).

## Setup

The easiest path is the quickstart script, which installs Determinate Nix and
applies the flake:

```sh
git clone https://github.com/clliaw/nix-home-manager-config.git ~/Projects/nix-home-manager-config
cd ~/Projects/nix-home-manager-config
./quickstart.sh
```

### Manual setup

1. Install [Determinate Nix](https://github.com/DeterminateSystems/nix-installer)
   (flakes are enabled by default):

   ```sh
   curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --determinate
   ```

2. Clone this repo to `~/Projects/nix-home-manager-config` (the path matters
   for a few `mkOutOfStoreSymlink` dotfiles referenced from `home.nix`).

3. Apply the config:

   ```sh
   nix run --inputs-from path:$HOME/Projects/nix-home-manager-config home-manager -- \
     switch --flake path:$HOME/Projects/nix-home-manager-config#x86_64-linux -b backup --impure
   ```

   Replace `x86_64-linux` with your system (`aarch64-linux`, `aarch64-darwin`).
   `--impure` is required — the flake reads `$USER` and `$HOME` at eval
   time so the same config works for any login user.

   If GitHub returns an HTTP 403 rate-limit error while Nix is fetching flakes,
   rerun the quickstart with `GITHUB_TOKEN` or `GH_TOKEN` set. The script passes
   that token to Nix as an `access-tokens` entry.

## Usage

### Private agent state and Git filters

`dotfiles/.claude/claude.json` is ignored and stays on disk. Home Manager
creates it if missing and merges optional overlay settings into the existing
file during activation. Nix evaluation no longer requires that private file.
Untracking the file does not remove copies from old commits.

Quickstart installs local Git clean filters after provisioning Mise. For an
existing clone or manual setup, run:

```sh
bash scripts/install-git-filters.sh
git add --renormalize dotfiles/.codex/config.toml dotfiles/.claude/settings.json
```

The filters keep reviewed preferences from these two files in Git without
modifying the working files. These sections are cleaned out in full, including
all nested entries, and remain only on disk:

| File | Omitted key or section | Local state |
| --- | --- | --- |
| `dotfiles/.codex/config.toml` | `notify` | Notification commands and executable paths |
| `dotfiles/.codex/config.toml` | `marketplaces` | Marketplace registrations and source paths |
| `dotfiles/.codex/config.toml` | `mcp_servers` | MCP server commands, endpoints, and configuration |
| `dotfiles/.codex/config.toml` | `projects` | Project directories and trust settings |
| `dotfiles/.codex/config.toml` | `tui.screen_reader_detection_done` | Machine-specific detection state |
| `dotfiles/.codex/config.toml` | `tui.model_availability_nux` | Model onboarding state |
| `dotfiles/.claude/settings.json` | `extraKnownMarketplaces` | Local marketplace registrations |
| `dotfiles/.claude/claude.json` | Entire file (ignored, not filtered) | Account, project, and runtime state |

The allowlists in `scripts/clean-agent-config.py` define what is shared. All
unlisted keys at every nesting level are also omitted, including future keys.
Even an allowed key is omitted if its name or value contains a path separator
or a home-directory marker (`~`, `$HOME`, or `${HOME}`); a list containing such
a value is omitted in full. Empty sections are dropped. Review and extend the
allowlists when adding a new portable preference, and keep this table current
when excluding additional sections. Output is canonicalized, so formatting
and local-only changes produce no content diff after renormalization.

Git can still report a file as modified when local edits change its byte size,
even when the filtered content matches the index. Use `git agent-status` (with
the usual status arguments) to refresh those entries before showing status.
It refreshes only files whose filtered hash already matches the index, so it
does not stage new preference changes. Plain `git status` retains this Git
limitation; the clean filter alone cannot eliminate it.

Filters are clone-local Git configuration: install them in every clone before
staging these files. Rerun the installer if the Mise Python installation is
replaced. A configured filter failure blocks staging instead of passing raw
content through. Review `git diff --cached` before publishing.

A clean filter is not a backup: a checkout, reset, or merge that replaces a
working file can discard its local-only settings. Back up local config before
such operations. The smudge filter passes repository content through unchanged.

### Apply configuration

Edit `home.nix` and run:

```sh
./reload.sh
```

To pull in newer package versions (nixpkgs + home-manager track rolling
unstable), run `nix flake update` then re-switch. Commit `flake.lock`
to pin inputs between updates.

## Optional Overlays

Machine-specific Home Manager overlays can be enabled without committing local
state:

```nix
# config.nix
{
  overlays = [ "grafana-mcp" ];
}
```

Start from `config.nix.example`, then run `./reload.sh`. `config.nix` is
ignored by git so each clone can choose its own overlays.

Available overlays:

- `grafana-mcp`: adds the Grafana MCP server to Codex
  (`~/.codex/config.toml`) and Claude Code (`~/.claude.json`).
