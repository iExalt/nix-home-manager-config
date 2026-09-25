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
    # fix(claude): materialize config in the repo so Claude Code can persist TUI state.
    home.file.".claude.json".source =
      config.lib.file.mkOutOfStoreSymlink claudeConfigFile;

    home.activation.writeClaudeConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "$(dirname "${claudeConfigFile}")"
      # fix(claude): merge overlay settings without importing private runtime state.
      if [ ! -f "${claudeConfigFile}" ]; then
        install -m 0600 ${generatedConfig} "${claudeConfigFile}"
      else
        mergedConfig="$(mktemp "${claudeConfigFile}.XXXXXX")"
        if ${pkgs.jq}/bin/jq -s '.[0] * .[1]' \
          "${claudeConfigFile}" ${generatedConfig} > "$mergedConfig"; then
          chmod 600 "$mergedConfig"
          mv "$mergedConfig" "${claudeConfigFile}"
        else
          rm -f "$mergedConfig"
          exit 1
        fi
      fi
    '';
  };
}
