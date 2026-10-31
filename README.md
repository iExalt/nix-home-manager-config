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

The filters keep reviewed preferences from these two files in Git; staging
never modifies the working files. These sections are cleaned out in full,
including all nested entries, and remain only on disk:

| File | Omitted key or section | Local state |
| --- | --- | --- |
| `dotfiles/.codex/config.toml` | `notify` | Notification commands and executable paths |
| `dotfiles/.codex/config.toml` | `marketplaces` | Marketplace registrations and source paths |
| `dotfiles/.codex/config.toml` | `mcp_servers` | MCP server commands, endpoints, and configuration |
| `dotfiles/.codex/config.toml` | `projects` | Project directories and trust settings |
| `dotfiles/.codex/config.toml` | `hooks` | Hook trust hashes, approved per machine with `/hooks` |
| `dotfiles/.codex/config.toml` | `tui.screen_reader_detection_done` | Machine-specific detection state |
| `dotfiles/.codex/config.toml` | `tui.model_availability_nux` | Model onboarding state |
| `dotfiles/.codex/config.toml` | `desktop.daybreak-enabled` | Account and user identifiers |
| `dotfiles/.claude/settings.json` | `extraKnownMarketplaces` | Local marketplace registrations |
| `dotfiles/.claude/settings.json` | `permissions.allow` | Permission rules with local command paths |
| `dotfiles/.claude/settings.json` | `env`, except `CLAUDE_CODE_SILENT_TURN_REMINDER_TEXT` | Environment variables, which may hold secrets |
| `dotfiles/.claude/claude.json` | Entire file (ignored, not filtered) | Account, project, and runtime state |

The allowlists in `scripts/clean-agent-config.py` define what is shared. All
unlisted keys at every nesting level are also omitted, including future keys.
Even an allowed key is omitted if its name or value contains a path separator
or a home-directory marker (`~`, `$HOME`, or `${HOME}`); a list containing such
a value is omitted in full. The one exception is a quoted path under
`"$HOME/.config/agent-hooks/`, the shared hook scripts that Home Manager links
from `dotfiles/agent-hooks`, so reviewed Claude `hooks` entries that run them
stay in Git. A hook entry is kept whole or omitted whole: one unlisted key or
private path drops the entry. Empty sections are dropped. Review and extend the
allowlists when adding a new portable preference, and keep this table current
when excluding additional sections. Output is canonicalized, so formatting
and local-only changes produce no content diff after renormalization.

Git can still report a file as modified when local edits change its byte size,
even when the filtered content matches the index. Use `git agent-status` (with
the usual status arguments) to refresh those entries before showing status.
It refreshes only files whose filtered hash already matches the index, so it
does not stage new preference changes. Plain `git status` retains this Git
limitation; the clean filter alone cannot eliminate it.

Git stores only the filtered content, so a pull, checkout, reset, or stash
that rewrites either file writes the filtered content back and drops the
private keys. To recover them, the clean filter also saves each raw version
that holds private keys to `.git/agent-config-private/`, keeping the last 10
(mode 0600, per worktree, never committed). A file that already equals its
filtered content is not saved, so a wiped file never replaces a good backup.
The installer adds `post-checkout`, `post-merge`, and `post-rewrite` hooks
(under a repository-local `core.hooksPath`; it warns and skips them when the
hooks directory is shared through global config, or when a hook it did not
write already exists) that run `git agent-restore`, so pulls, rebases, and
checkouts restore the keys automatically. No hook runs after `git stash`, `git
stash pop`, `git pull --autostash`, `git reset --hard`, or resolving a merge
conflict in either file; run `git agent-restore` yourself afterwards. Between
`git stash` and `git stash pop`, the agents run without their private
settings.

`git agent-restore` adds back only private keys that are missing; values
already in the file win, and portable preferences removed in Git stay removed.
It rewrites a file only when it adds keys, in canonical form, so hand-written
comments in `config.toml` are lost then. Deleting a private key is safe while
others remain, because the next backup lacks it. Deleting the last one is not
saved, so a later restore brings it back; remove that file's backups to drop it
for good. To recover an older version, run
`git agent-restore --from .git/agent-config-private/<file>`.

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
