# Agent tool shells are non-interactive, so /etc/zshrc never runs nix-daemon.sh for them,
# and macOS path_helper moves the system directories ahead of whatever they inherit.
# Put the Nix profiles just before /usr/bin: ahead of Apple's tools, behind mise's.
# Every path returns 0 so `zsh -e` startup files never fail here.
_nix_path_before_system() {
  if [[ -o interactive ]]; then
    return 0
  fi
  local -a nix_bins
  local dir
  for dir in "$HOME/.nix-profile/bin" /nix/var/nix/profiles/default/bin; do
    if [[ -d $dir ]]; then
      nix_bins+=("$dir")
    fi
  done
  if (( ! $#nix_bins )); then
    return 0
  fi
  path=(${path:|nix_bins})
  local i=${path[(i)/usr/bin]}
  path=("${(@)path[1,i-1]}" "${nix_bins[@]}" "${(@)path[i,-1]}")
  return 0
}
_nix_path_before_system
