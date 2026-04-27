{ config, pkgs, lib, ... }:

let
  repoRoot = "${config.home.homeDirectory}/Projects/nix-home-manager-config";
in
{
  # home.username and home.homeDirectory are set by flake.nix.

  # Don't change this — it pins the Home Manager release your config was written for.
  home.stateVersion = "25.11";

  home.packages = [
    pkgs.zsh
    pkgs.mise
    pkgs.difftastic
  ];

  home.file.".vimrc".source = ./dotfiles/.vimrc;
  home.file.".zsh_aliases".source = ./dotfiles/.zsh_aliases;
  home.file.".zsh_functions".source = ./dotfiles/.zsh_functions;
  home.file.".kubectl_aliases.zsh".source = ./dotfiles/.kubectl_aliases.zsh;
  home.file.".codex/config.toml".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.codex/config.toml";
  home.file.".claude/settings.json".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.claude/settings.json";
  home.file.".claude/CLAUDE.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/AGENTS.md";
  home.file.".codex/AGENTS.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/AGENTS.md";
  xdg.configFile."ccstatusline/settings.json".source = ./dotfiles/.config/ccstatusline/settings.json;

  home.sessionVariables = {
    LESS = "-FR";
  };

  programs.zsh = {
    enable = true;
    antidote = {
      enable = true;
      plugins = [
        "getantidote/use-omz"
        "mattmc3/ez-compinit"
        "ohmyzsh/ohmyzsh path:lib"
        "ohmyzsh/ohmyzsh path:plugins/git"
        "ahmetb/kubectx path:completion kind:fpath"
        "agkozak/zsh-z"
        "zdharma-continuum/fast-syntax-highlighting"
      ];
    };
    initContent = ''
      zstyle ':plugin:ez-compinit' 'compstyle' 'ohmy'
      eval "$(mise activate zsh --shims)"
      source ~/.zsh_functions
      source ~/.zsh_aliases
    '';
  };

  programs.starship = {
    enable = true;
    enableZshIntegration = true;
    settings = builtins.fromTOML (builtins.readFile ./dotfiles/starship.toml);
  };

  programs.fzf = {
    enable = true;
    enableZshIntegration = true;
  };

  programs.git = {
    enable = true;
    settings = {
      user = {
        name = "Clement Liaw";
        email = "cman101202@gmail.com";
      };
      core.editor = "vim";
      diff.external = "${pkgs.difftastic}/bin/difft";
      diff.tool = "difftastic";
      difftool.difftastic.cmd = ''${pkgs.difftastic}/bin/difft "$LOCAL" "$REMOTE"'';
      difftool.prompt = false;
      push.autoSetupRemote = true;
      gpg.ssh.allowedSignersFile = "~/.ssh/allowed_signers";
      "credential \"https://github.com\"".helper = "!gh auth git-credential";
    };
    signing = {
      format = "ssh";
      key = "~/.ssh/id_ed25519.pub";
      signByDefault = true;
    };
  };

  programs.gh = {
    enable = true;
  };

  programs.home-manager.enable = true;

  home.activation.installGhosttyTerminfo = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.terminfo"
    ${pkgs.ncurses}/bin/tic -x -o "$HOME/.terminfo" ${./dotfiles/xterm-ghostty-terminfo.txt}
  '';
}
