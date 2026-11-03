{ config, lib, pkgs, ... }:

let
  # feat(hooks): one guard script serves Claude Code and Codex; both pass the shell command as
  # tool_input.command on PreToolUse. A pinned Python keeps the per-call cost near 15 ms.
  guard = "${pkgs.python3}/bin/python3 -I -S ${../dotfiles/hooks/process-probe-guard.py}";
  entry = matcher: {
    inherit matcher;
    hooks = [{ type = "command"; command = guard; timeout = 10; }];
  };
  claudeHooks = pkgs.writeText "claude-hooks.json" (builtins.toJSON { PreToolUse = [ (entry "Bash") ]; });
  settings = "${config.home.homeDirectory}/.claude/settings.json";
in
{
  # Codex reads ~/.codex/hooks.json. It runs a hook only after /hooks marks the current file
  # trusted, so every change here needs one review in Codex.
  home.file.".codex/hooks.json".text = builtins.toJSON {
    hooks.PreToolUse = [ (entry "^(Bash|exec_command|shell|local_shell)$") ];
  };

  # Claude Code keeps hooks in its live, untracked settings.json, which it also rewrites itself.
  # Replace only this guard's entries, keyed by the script name, and swap the file atomically.
  home.activation.mergeClaudeHooks = lib.hm.dag.entryAfter [ "syncAgentConfig" ] ''
    mergeClaudeHooks() {
      mkdir -p "$(dirname "${settings}")"
      [ -f "${settings}" ] || echo '{}' > "${settings}"
      merged="$(mktemp "${settings}.XXXXXX")"
      if ${pkgs.jq}/bin/jq --slurpfile ours ${claudeHooks} '
          .hooks.PreToolUse = ([(.hooks.PreToolUse // [])[]
            | select(([.hooks[]?.command] | any(test("process-probe-guard"))) | not)]
            + $ours[0].PreToolUse)
        ' "${settings}" > "$merged"; then
        chmod 600 "$merged"
        mv "$merged" "${settings}"
      else
        rm -f "$merged"
        warnEcho "Could not add the process-probe guard to ${settings}."
      fi
    }
    run mergeClaudeHooks
  '';
}
