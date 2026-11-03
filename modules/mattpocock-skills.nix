{ lib, mattpocock-skills, ... }:

let
  # Upstream groups skills by category; the wrappers call their dependencies
  # by name, so the closure must stay complete:
  # grill-me -> grilling; grill-with-docs -> grilling, domain-modeling;
  # improve-codebase-architecture -> codebase-design, grilling, domain-modeling.
  skills = {
    grill-me = "productivity/grill-me";
    grilling = "productivity/grilling";
    grill-with-docs = "engineering/grill-with-docs";
    domain-modeling = "engineering/domain-modeling";
    codebase-design = "engineering/codebase-design";
    improve-codebase-architecture = "engineering/improve-codebase-architecture";
  };
in
{
  home.file = lib.listToAttrs (lib.concatMap
    (agent: lib.mapAttrsToList
      (skill: subdir: lib.nameValuePair "${agent}/skills/${skill}" {
        source = "${mattpocock-skills}/skills/${subdir}";
      })
      skills)
    [ ".codex" ".claude" ]);
}
