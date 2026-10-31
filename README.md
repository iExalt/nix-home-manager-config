# nix-home-manager-config

My nix home-manager config (flake-based).

## Setup

The easiest path is the quickstart script, which installs Determinate Nix and
applies the flake:

```sh
git clone https://github.com/clliaw/nix-home-manager-config.git ~/dev/Projects/nix-home-manager-config
cd ~/dev/Projects/nix-home-manager-config
./quickstart.sh
```

### Manual setup

1. Install [Determinate Nix](https://github.com/DeterminateSystems/nix-installer)
   (flakes are enabled by default):

   ```sh
   curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --determinate
   ```

2. Clone this repo to `~/dev/Projects/nix-home-manager-config` (the path matters
   for a few `mkOutOfStoreSymlink` dotfiles referenced from `home.nix`).

3. Apply the config:

   ```sh
   nix run --inputs-from path:$HOME/dev/Projects/nix-home-manager-config home-manager -- \
     switch --flake path:$HOME/dev/Projects/nix-home-manager-config#x86_64-linux -b backup --impure
   ```

   Replace `x86_64-linux` with your system (`aarch64-linux`, `aarch64-darwin`).
   `--impure` is required — the flake reads `$USER` and `$HOME` at eval
   time so the same config works for any login user.

   If GitHub returns an HTTP 403 rate-limit error while Nix is fetching flakes,
   rerun the quickstart with `GITHUB_TOKEN` or `GH_TOKEN` set. The script passes
   that token to Nix as an `access-tokens` entry.

## Usage

### Private agent state and shared preferences

Claude Code and Codex keep their settings in regular, untracked files on each
machine: `~/.claude/settings.json` and `~/.codex/config.toml`. Git never reads
or writes them, so pulls, stashes, and checkouts cannot touch their private
keys. The repository tracks only reviewed, portable preferences, in
`dotfiles/.claude/settings.json` and `dotfiles/.codex/config.toml`.

`dotfiles/.claude/claude.json` is ignored and stays on disk. Home Manager
creates it if missing and merges optional overlay settings into the existing
file during activation. Nix evaluation no longer requires that private file.
Untracking the file does not remove copies from old commits.

`./reload.sh` runs `scripts/clean-agent-config.py sync` during activation. It
merges each live file's portable keys with the tracked copy, using the tracked
copy from the last sync, kept in `~/.local/state/agent-config/`, as the base:

- A key changed only in the repository, as after a pull, is applied to the
  live file.
- A key changed only on this machine, as with `/model`, is copied into the
  tracked file; commit or revert it.
- A key changed on both sides keeps this machine's value, with a warning.
- Without a base, as on a machine's first sync, keys found on one side only
  are added to the other, and nothing is deleted.

To share a preference change without reloading, run
`mise exec -- python scripts/clean-agent-config.py sync` from the main
checkout; sync refuses to run from a linked worktree, because every checkout
shares one base. Sync rewrites a live file only when it changes something, in
canonical form, so comments in `config.toml` are lost then. If an app saves
the file while sync runs, sync merges again. Codex overlay settings (see
[Optional Overlays](#optional-overlays)) are merged into `~/.codex/config.toml`
on every sync and may set private keys only. Keep your own backup of anything
you cannot recreate.

These sections are never shared, including all nested entries:

| File | Omitted key or section | Local state |
| --- | --- | --- |
| `~/.codex/config.toml` | `notify` | Notification commands and executable paths |
| `~/.codex/config.toml` | `marketplaces` | Marketplace registrations and source paths |
| `~/.codex/config.toml` | `mcp_servers` | MCP server commands, endpoints, and configuration |
| `~/.codex/config.toml` | `projects` | Project directories and trust settings |
| `~/.codex/config.toml` | `hooks` | Hook trust hashes, approved per machine with `/hooks` |
| `~/.codex/config.toml` | `tui.screen_reader_detection_done` | Machine-specific detection state |
| `~/.codex/config.toml` | `tui.model_availability_nux` | Model onboarding state |
| `~/.codex/config.toml` | `desktop.daybreak-enabled` | Account and user identifiers |
| `~/.claude/settings.json` | `extraKnownMarketplaces` | Local marketplace registrations |
| `~/.claude/settings.json` | `permissions.allow` | Permission rules with local command paths |
| `~/.claude/settings.json` | `env`, except `CLAUDE_CODE_SILENT_TURN_REMINDER_TEXT` | Environment variables, which may hold secrets |
| `dotfiles/.claude/claude.json` | Entire file (ignored, linked to `~/.claude.json`) | Account, project, and runtime state |

The allowlists in `scripts/clean-agent-config.py` define what is shared. All
unlisted keys at every nesting level are also omitted, including future keys.
Even an allowed key is omitted if its name or value contains a path separator
or a home-directory marker (`~`, `$HOME`, or `${HOME}`); a list containing
such a value is omitted in full. When that keeps a key the allowlist names
local, such as `developer_instructions` containing "and/or", sync and the
filter print a warning naming the key until the value changes, and sync
leaves the key alone on both sides. The one exception is a quoted path under
`"$HOME/.config/agent-hooks/`, the shared hook scripts that Home Manager links
from `dotfiles/agent-hooks`, so reviewed Claude `hooks` entries that run them
are shared. A hook entry is kept whole or omitted whole: one unlisted key or
private path keeps the entry local, while the other entries for the same event
are shared. Empty sections are dropped. Review and extend the allowlists when
adding a new portable preference, and keep this table current when excluding
additional sections.

Quickstart also installs Git clean filters for the two tracked files, as a
safety net: Git stores only their allowlisted content, so private keys left in
a tracked copy never reach a commit. For an existing clone or manual setup,
run:

```sh
bash scripts/install-git-filters.sh
```

Filters are clone-local Git configuration: install them in every clone before
staging these files. Rerun the installer if the Mise Python installation is
replaced. A configured filter failure blocks staging instead of passing raw
content through. Review `git diff --cached` before publishing.

#### Moving from the previous layout

The live files used to be links into this repository, kept private by backups
and Git hooks. Rerun the installer once in each existing clone: it removes
those hooks and the `git agent-status` and `git agent-restore` aliases. The
first sync on such a machine creates each live file from the tracked copy,
which still holds that machine's private keys. If a pull had already wiped
them, it uses the newest backup in `.git/agent-config-private/` instead. Each
clone keeps its own; delete it once that clone has synced. The first sync
shrinks both tracked files to their shared content, so `git status` lists them
as modified until `git add` refreshes Git's index; nothing is staged, because
their content is unchanged. Earlier Home Manager generations put copies of the
full Codex config in the Nix store; they remain until those generations expire
and are garbage-collected.

### Apply configuration

Edit `home.nix` and run:

```sh
./reload.sh
```

To pull in newer package versions (nixpkgs + home-manager track rolling
unstable), run `nix flake update` then re-switch. Commit `flake.lock`
to pin inputs between updates.

### frontend-design skill

`dotfiles/skills/frontend-design` merges Impeccable, Vercel's Web Interface
Guidelines, and Anthropic's frontend-design skill into one workflow; it replaces
the upstream Anthropic skill. Its `NOTICE.md` records the source revisions and
licenses. Leave the Claude `frontend-design@claude-code-plugins` plugin out of
`enabledPlugins` so the upstream skill does not load alongside it.

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
