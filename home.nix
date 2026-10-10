{ config, pkgs, lib, ... }:

let
  repoRoot = "${config.home.homeDirectory}/dev/Projects/nix-home-manager-config";
  rootHome = if pkgs.stdenv.isDarwin then "/var/root" else "/root";
  frontendDesignSource = pkgs.fetchFromGitHub {
    owner = "anthropics";
    repo = "claude-code";
    rev = "2bfb629dfaff0c8318047a4beb93cf1dc5b58b18";
    hash = "sha256-qD7zEVcuPhwGbpknmsWKwCiR4XMc63iUumP7vLok704=";
  };
  frontendDesignSkill = "${frontendDesignSource}/plugins/frontend-design/skills/frontend-design";
  miseTools = [
    "node@26"
    "bun@latest"
    "gh@latest"
    "npm:@openai/codex@latest"
    "claude@latest"
    "rg@latest"
    "fd@latest"
    "python@3.14"
    "uv@latest"
    "rust[profile=minimal,components=clippy,rustfmt]@latest"
    "dust@latest"
    "bat@latest"
    "glow@latest"
    "zellij@latest"
    # fix(mise): avoid intermittent aqua .pkg extraction failures on macOS.
    "asdf:MetricMike/asdf-awscli@latest"
  ];
  miseActivationPackages = with pkgs; [
    bash
    coreutils
    curl
    gawk
    git
    gnutar
    gzip
    gnused
    mise
    unzip
  ];
  miseToolArgs = lib.escapeShellArgs miseTools;
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
  home.file.".gitignore_global".source = ./dotfiles/.gitignore_global;
  home.file.".zsh_aliases".source = ./dotfiles/.zsh_aliases;
  home.file.".zsh_functions".source = ./dotfiles/.zsh_functions;
  home.file.".zshrc".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.zshrc";
  home.file.".kubectl_aliases.zsh".source = ./dotfiles/.kubectl_aliases.zsh;
  home.file.".cache/zsh/completions/_kubectl".source =
    ./dotfiles/zsh/completions/_kubectl;
  home.file.".claude/settings.json".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.claude/settings.json";
  home.file.".claude/agents/developer-trivial.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.claude/agents/developer-trivial.md";
  home.file.".claude/agents/developer-routine.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.claude/agents/developer-routine.md";
  home.file.".claude/agents/developer-demanding.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.claude/agents/developer-demanding.md";
  home.file.".claude/CLAUDE.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/AGENTS.md";
  home.file.".codex/AGENTS.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/AGENTS.md";
  # feat(skills): share the pinned upstream skill without a client plugin cache.
  home.file.".agents/skills/frontend-design".source = frontendDesignSkill;
  home.file.".claude/skills/frontend-design".source = frontendDesignSkill;
  home.file.".codex/skills/peer-review".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/peer-review";
  home.file.".claude/skills/peer-review".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/peer-review";
  home.file.".codex/skills/peer-review-loop".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/peer-review-loop";
  home.file.".claude/skills/peer-review-loop".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/peer-review-loop";
  home.file.".codex/skills/continuous-peer-review".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/continuous-peer-review";
  home.file.".claude/skills/continuous-peer-review".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/continuous-peer-review";
  home.file.".codex/skills/pair-program".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/pair-program";
  home.file.".claude/skills/pair-program".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/pair-program";
  home.file.".codex/skills/subagent-pair-program".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/subagent-pair-program";
  home.file.".claude/skills/subagent-pair-program".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/subagent-pair-program";
  home.file.".codex/skills/agentic-workflow".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/agentic-workflow";
  home.file.".claude/skills/agentic-workflow".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/agentic-workflow";
  home.file.".codex/skills/keep-me-in-the-loop".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/keep-me-in-the-loop";
  home.file.".claude/skills/keep-me-in-the-loop".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/keep-me-in-the-loop";
  home.file.".codex/skills/maintain-project-status".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/maintain-project-status";
  home.file.".claude/skills/maintain-project-status".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/maintain-project-status";
  home.file.".codex/skills/three-tiered-plan".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/three-tiered-plan";
  home.file.".claude/skills/three-tiered-plan".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/three-tiered-plan";
  home.file.".codex/skills/overseer".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/overseer";
  home.file.".claude/skills/overseer".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/overseer";
  home.file.".codex/skills/prose-fix".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/prose-fix";
  home.file.".claude/skills/prose-fix".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/prose-fix";
  home.file.".codex/skills/fix-skill".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/fix-skill";
  home.file.".claude/skills/fix-skill".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/fix-skill";
  home.file.".codex/skills/assign".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/assign";
  home.file.".claude/skills/assign".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/assign";
  home.file.".codex/skills/reload-skill".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/reload-skill";
  home.file.".claude/skills/reload-skill".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/skills/reload-skill";
  home.file.".vibe/config.toml".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.vibe/config.toml";
  xdg.configFile."ccstatusline/settings.json".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.config/ccstatusline/settings.json";
  xdg.configFile."ghostty/config".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.config/ghostty/config";
  xdg.configFile."zellij/config.kdl".source = ./dotfiles/.config/zellij/config.kdl;

  home.sessionVariables = {
    BAT_THEME = "1337";
    LESS = "-FR --mouse";
    XDG_RUNTIME_DIR = "/run/user/$UID";
  };

  home.sessionPath = [
    "$HOME/.local/bin"
  ];

  programs.zsh = {
    enable = true;
    dotDir = "${config.xdg.configHome}/zsh";
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
    initContent = lib.mkMerge [
      (lib.mkOrder 550 ''
        # fix(kubectl): put managed completions on fpath before compinit scans.
        fpath+=("$HOME/.cache/zsh/completions")
      '')
      ''
        zstyle ':plugin:ez-compinit' 'compstyle' 'ohmy'
        eval "$(mise activate zsh)"
        # fix(completion): keep plain Tab on zsh completion while preserving fzf triggers.
        fzf_default_completion=expand-or-complete
        source ~/.zsh_functions
        source ~/.zsh_aliases
        bindkey "^[[1;3D" backward-word
        bindkey "^[[1;3C" forward-word
      ''
      (lib.mkOrder 2000 ''
        # feat(zsh): load the writable, repo-backed user configuration last.
        source "$HOME/.zshrc"
      '')
    ];
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
      core.excludesFile = "~/.gitignore_global";
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
  # gh auth login/config set write config.yml; keep it out of the read-only store.
  xdg.configFile."gh/config.yml".enable = false;

  programs.home-manager.enable = true;
  news.display = "silent";

  # Home Manager's generated option manpage currently triggers a Nix 2.34
  # store-path context warning while evaluating the activation package.
  manual.manpages.enable = false;

  home.activation.installGhosttyTerminfo = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    # feat(terminfo): make Ghostty's terminal definition available to root.
    mkdir -p "$HOME/.terminfo"
    ${pkgs.ncurses}/bin/tic -x -o "$HOME/.terminfo" ${./dotfiles/xterm-ghostty-terminfo.txt}

    # fix(terminfo): activation PATH is sanitized; locate sudo and skip if unavailable.
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      sudo mkdir -p "${rootHome}/.terminfo"
      sudo ${pkgs.ncurses}/bin/tic -x -o "${rootHome}/.terminfo" ${./dotfiles/xterm-ghostty-terminfo.txt}
    else
      echo "warning: skipping root Ghostty terminfo install (sudo unavailable or needs a password)" >&2
    fi
  '';

  home.activation.installMiseTools = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    # feat(mise): install shared global tools while preserving local config.
    # fix(mise): expose backend dependencies and macOS system tools during activation.
    export PATH="${lib.makeBinPath miseActivationPackages}:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

    if [ -z "''${MISE_GITHUB_TOKEN:-}" ]; then
      token="$(${pkgs.gh}/bin/gh auth token 2>/dev/null || true)"
      if [ -n "$token" ]; then
        export MISE_GITHUB_TOKEN="$token"
      fi
    fi

    # fix(mise): drop legacy Codex keys when selecting the official npm package.
    run ${pkgs.mise}/bin/mise use --global --yes \
      --remove awscli \
      --remove codex \
      --remove aqua:codex \
      --remove aqua:openai/codex \
      ${miseToolArgs}
  '';
}
