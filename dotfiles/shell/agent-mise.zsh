# Mise's own chpwd hook preserves project environments when a tool call changes directory.
# The caller passes the pinned bootstrap executable, independent of inherited PATH.
if [[ ! -o interactive ]]; then
  eval "$("$1" activate zsh)"
fi
