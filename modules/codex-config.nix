{ config, lib, pkgs, ... }:

let
  cfg = config.my.codex;
  tomlFormat = pkgs.formats.toml { };
in
{
  options.my.codex.settings = lib.mkOption {
    type = tomlFormat.type;
    default = { };
    description = "Codex CLI settings written to ~/.codex/config.toml.";
  };

  config = {
    my.codex.settings = builtins.fromTOML (builtins.readFile ../dotfiles/.codex/config.toml);

    home.file.".codex/config.toml".source =
      tomlFormat.generate "codex-config.toml" cfg.settings;
  };
}
