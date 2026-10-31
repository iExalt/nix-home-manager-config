{ config, lib, pkgs, ... }:

let
  cfg = config.my.codex;
  tomlFormat = pkgs.formats.toml { };
  repoRoot = "${config.home.homeDirectory}/dev/Projects/nix-home-manager-config";
  overlayConfig = tomlFormat.generate "codex-overlay.toml" cfg.settings;
in
{
  options.my.codex.settings = lib.mkOption {
    type = tomlFormat.type;
    default = { };
    description = "Private Codex settings, such as MCP servers, merged into ~/.codex/config.toml.";
  };

  config = {
    # fix(config): the live Claude and Codex settings are untracked files that Git never
    # rewrites; sync shares their portable keys with the tracked copies, then merges in
    # overlay settings. Nix reads only the overlays, so private keys stay out of the store.
    home.activation.syncAgentConfig = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
      run ${pkgs.python3}/bin/python3 -I "${repoRoot}/scripts/clean-agent-config.py" sync \
        --repo "${repoRoot}" --overlay codex=${overlayConfig} \
        || warnEcho "Agent config sync failed; fix the problem above, then rerun ./reload.sh."
    '';
  };
}
