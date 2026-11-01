{ lib, ponytail, ... }:

let
  skills = [
    "ponytail"
    "ponytail-audit"
    "ponytail-debt"
    "ponytail-gain"
    "ponytail-help"
    "ponytail-review"
  ];
in
{
  home.file = lib.listToAttrs (lib.concatMap
    (agent: map
      (skill: lib.nameValuePair "${agent}/skills/${skill}" {
        source = "${ponytail}/skills/${skill}";
      })
      skills)
    [ ".codex" ".claude" ]);
}
