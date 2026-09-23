{ config, lib, pkgs, ... }:

let
  cfg = config.my.codex;
  tomlFormat = pkgs.formats.toml { };
  repoRoot = "${config.home.homeDirectory}/Projects/nix-home-manager-config";
  codexConfigFile = "${repoRoot}/dotfiles/.codex/config.toml";
  generatedConfig = tomlFormat.generate "codex-config.toml" cfg.settings;
in
{
  options.my.codex.settings = lib.mkOption {
    type = tomlFormat.type;
    default = { };
    description = "Codex CLI settings written to ~/.codex/config.toml.";
  };

  config = {
    my.codex.settings = builtins.fromTOML (builtins.readFile ../dotfiles/.codex/config.toml);

    # note: Materialize the merged config into the repo so Codex can persist TUI edits.
    home.file.".codex/config.toml".source =
      config.lib.file.mkOutOfStoreSymlink codexConfigFile;

    home.activation.writeCodexConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "$(dirname "${codexConfigFile}")"
      if ! cmp -s ${generatedConfig} "${codexConfigFile}"; then
        install -m 0644 ${generatedConfig} "${codexConfigFile}"
      fi
    '';
  };
}
