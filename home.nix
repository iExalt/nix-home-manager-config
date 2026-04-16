{ config, pkgs, ... }:

{
  home.username = builtins.getEnv "USER";
  home.homeDirectory = builtins.getEnv "HOME";

  # Don't change this — it pins the Home Manager release your config was written for.
  home.stateVersion = "25.11";

  home.packages = [
    pkgs.zsh
    pkgs.mise
  ];

  home.file.".vimrc".source = ./dotfiles/.vimrc;

  home.sessionVariables = {};

  programs.zsh.enable = true;

  programs.home-manager.enable = true;
}
