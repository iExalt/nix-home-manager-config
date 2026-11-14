{ config, pkgs, lib, ... }:

let
  repoRoot = "${config.home.homeDirectory}/dev/Projects/nix-home-manager-config";
  rootHome = if pkgs.stdenv.hostPlatform.isDarwin then "/var/root" else "/root";
  miseTools = [
    "node@latest"
    "bun@latest"
    "gh@latest"
    "jq@latest"
    "npm:@openai/codex@latest"
    "npm:agent-browser@latest"
    "claude@latest"
    "rg@latest"
    "fd@latest"
    "python[postinstall=python -m pip install PyYAML]@latest"
    "uv@latest"
    "rust[profile=minimal,components=clippy,rustfmt]@latest"
    "dust@latest"
    "sd@latest"
    "ast-grep@latest"
    "hyperfine@latest"
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
  ] ++ lib.optional pkgs.stdenv.hostPlatform.isDarwin
    # feat(shell): macOS lacks `timeout`, which agents reach for to bound waits. Link only that
    # command from uutils, the Rust rewrite of GNU coreutils, so the BSD tools stay in charge.
    # Linux already has GNU timeout.
    (pkgs.runCommand "uutils-timeout" { } ''
      mkdir -p $out/bin
      ln -s ${pkgs.uutils-coreutils}/bin/uutils-timeout $out/bin/timeout
    '');

  home.file.".vimrc".source = ./dotfiles/.vimrc;
  home.file.".gitignore_global".source = ./dotfiles/.gitignore_global;
  home.file.".zsh_aliases".source = ./dotfiles/.zsh_aliases;
  home.file.".zsh_functions".source = ./dotfiles/.zsh_functions;
  home.file.".zshrc".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.zshrc";
  home.file.".kubectl_aliases.zsh".source = ./dotfiles/.kubectl_aliases.zsh;
  home.file.".cache/zsh/completions/_kubectl".source =
    ./dotfiles/zsh/completions/_kubectl;
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
  # feat(skills): the user's skills ship as one plugin, so both harnesses list
  # them as iExalt:<skill>. Claude Code loads it live from the skills directory;
  # Codex installs a copy from the local marketplace (see modules/codex-config.nix).
  home.file.".claude/skills/iExalt".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/plugins/iExalt";
  home.file.".codex/rules/phone-debug.rules".source =
    config.lib.file.mkOutOfStoreSymlink "${repoRoot}/dotfiles/.codex/rules/phone-debug.rules";
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
    "$HOME/.local/share/mise/shims"
  ];

  home.file.".local/bin/validate-agent-skill" = {
    source = pkgs.writeShellScript "validate-agent-skill" ''
      export AGENT_MISE_BIN=${pkgs.mise}/bin/mise
      exec ${pkgs.bash}/bin/bash ${./scripts/validate-agent-skill} "$@"
    '';
    executable = true;
  };

  home.file.".local/bin/scratch-rm" = {
    source = pkgs.writeShellScript "scratch-rm" ''
      export SCRATCH_RM_GIT=${pkgs.git}/bin/git
      exec ${pkgs.python3}/bin/python3 -I ${./scripts/scratch-rm.py} "$@"
    '';
    executable = true;
  };
  home.file.".codex/rules/scratch-rm.rules".source = ./dotfiles/.codex/rules/scratch-rm.rules;
  home.activation.allowScratchRemoval = lib.hm.dag.entryAfter [ "syncAgentConfig" ] ''
    run ${pkgs.python3}/bin/python3 -I ${./scripts/allow-scratch-rm.py} \
      "${config.home.homeDirectory}/.claude/settings.json"
  '';


  home.file.".local/bin/dev-instance" = {
    source = pkgs.writeShellScript "dev-instance" ''
      export DEV_INSTANCE_MISE=${pkgs.mise}/bin/mise
      export DEV_INSTANCE_GIT=${pkgs.git}/bin/git
      export DEV_INSTANCE_TIMEOUT=${pkgs.coreutils}/bin/timeout
      exec ${pkgs.bash}/bin/bash ${./scripts/dev-instance} "$@"
    '';
    executable = true;
  };

  programs.zsh = {
    enable = true;
    dotDir = "${config.xdg.configHome}/zsh";
    # Agent tool shells have no prompt: activate now and refresh on directory changes.
    envExtra = ''
      source ${./dotfiles/shell/agent-mise.zsh} ${pkgs.mise}/bin/mise
    '';
    # macOS path_helper runs after .zshenv and can reorder a login shell's PATH.
    profileExtra = ''
      if [[ ! -o interactive ]] && (( $+functions[_mise_hook] )); then
        _mise_hook --force
      fi
    '';
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
    run mkdir -p "$HOME/.terminfo"
    run ${pkgs.ncurses}/bin/tic -x -o "$HOME/.terminfo" ${./dotfiles/xterm-ghostty-terminfo.txt}

    # fix(terminfo): activation PATH is sanitized; locate sudo and skip if unavailable.
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      run sudo mkdir -p "${rootHome}/.terminfo"
      run sudo ${pkgs.ncurses}/bin/tic -x -o "${rootHome}/.terminfo" ${./dotfiles/xterm-ghostty-terminfo.txt}
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

    # Post-install hooks only run for new interpreters; cover existing ones too.
    run ${pkgs.mise}/bin/mise exec python@latest -- python -m pip install PyYAML
  '';
}
