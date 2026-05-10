{ config, lib, pkgs, ... }:

let
  cfg = config.my.claude;
  jsonFormat = pkgs.formats.json { };
in
{
  options.my.claude.settings = lib.mkOption {
    type = jsonFormat.type;
    default = { };
    description = "Claude Code settings written to ~/.claude.json.";
  };

  config = {
    my.claude.settings = builtins.fromJSON (builtins.readFile ../dotfiles/.claude/claude.json);

    home.file.".claude.json".source =
      jsonFormat.generate "claude-config.json" cfg.settings;
  };
}
