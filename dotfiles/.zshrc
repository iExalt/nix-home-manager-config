# note(zsh): Home Manager sources this writable file after generated shell setup.

# fix(ssh): silence Ghostty's setup notice while preserving failure warnings.
# note(ghostty): the SSH wrapper is created during deferred prompt initialization.
if [[ -n ${GHOSTTY_RESOURCES_DIR:-} ]]; then
  _quiet_ghostty_ssh_setup() {
    emulate -L zsh
    local notice='print "Setting up xterm-ghostty terminfo on $ssh_hostname..." >&2'
    if [[ ${functions[ssh]:-} == *"$notice"* ]]; then
      functions[ssh]=${functions[ssh]//"$notice"/:}
      add-zsh-hook -d precmd _quiet_ghostty_ssh_setup
    fi
  }
  autoload -Uz add-zsh-hook
  add-zsh-hook precmd _quiet_ghostty_ssh_setup
fi
