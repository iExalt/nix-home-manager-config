{ config, pkgs, lib, ... }:

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
  home.file.".zsh_aliases".source = ./dotfiles/.zsh_aliases;
  home.file.".kubectl_aliases.zsh".source = ./dotfiles/.kubectl_aliases.zsh;

  home.sessionVariables = {};

  programs.zsh = {
    enable = true;
    antidote = {
      enable = true;
      plugins = [
        "getantidote/use-omz"
        "ohmyzsh/ohmyzsh path:lib"
        "ohmyzsh/ohmyzsh path:plugins/git"
        "ahmetb/kubectx path:completion kind:fpath"
        "agkozak/zsh-z"
        "zdharma-continuum/fast-syntax-highlighting"
      ];
    };
    initContent = ''
      source ~/.zsh_aliases
    '';
  };

  programs.starship = {
    enable = true;
    enableZshIntegration = true;
    settings = builtins.fromTOML (builtins.readFile ./dotfiles/starship.toml);
  };

  programs.git = {
    enable = true;
    settings = {
      user = {
        name = "Clement Liaw";
        email = "cman101202@gmail.com";
      };
      core.editor = "vim";
      push.autoSetupRemote = true;
      gpg.ssh.allowedSignersFile = "~/.ssh/allowed_signers";
    };
    signing = {
      format = "ssh";
      key = "~/.ssh/id_ed25519.pub";
      signByDefault = true;
    };
  };

  programs.home-manager.enable = true;

  home.activation.installGhosttyTerminfo = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.terminfo"
    ${pkgs.ncurses}/bin/tic -x -o "$HOME/.terminfo" ${./dotfiles/xterm-ghostty-terminfo.txt}
  '';
}
