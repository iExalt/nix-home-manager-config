{ config, lib, pkgs, ... }:

let
  cfg = config.my.claude;
  jsonFormat = pkgs.formats.json { };
  repoRoot = "${config.home.homeDirectory}/Projects/nix-home-manager-config";
  claudeConfigFile = "${repoRoot}/dotfiles/.claude/claude.json";
  generatedConfig = jsonFormat.generate "claude-config.json" cfg.settings;
in
{
  options.my.claude.settings = lib.mkOption {
    type = jsonFormat.type;
    default = { };
    description = "Claude Code settings written to ~/.claude.json.";
  };

  config = {
    my.claude.settings = builtins.fromJSON (builtins.readFile ../dotfiles/.claude/claude.json);

    # fix(claude): materialize config in the repo so Claude Code can persist TUI state.
    home.file.".claude.json".source =
      config.lib.file.mkOutOfStoreSymlink claudeConfigFile;

    home.activation.writeClaudeConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "$(dirname "${claudeConfigFile}")"
      if ! cmp -s ${generatedConfig} "${claudeConfigFile}"; then
        install -m 0644 ${generatedConfig} "${claudeConfigFile}"
      fi
    '';
  };
}
