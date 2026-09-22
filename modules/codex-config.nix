{ config, lib, pkgs, ... }:

let
  cfg = config.my.codex;
  tomlFormat = pkgs.formats.toml { };
  repoRoot = "${config.home.homeDirectory}/Projects/nix-home-manager-config";
  codexConfigFile = "${repoRoot}/dotfiles/.codex/config.toml";
  modelCatalogFile = "${repoRoot}/dotfiles/.codex/models-catalog.local.json";
  generatedConfig = tomlFormat.generate "codex-config.toml" cfg.settings;
in
{
  options.my.codex.settings = lib.mkOption {
    type = tomlFormat.type;
    default = { };
    description = "Codex CLI settings written to ~/.codex/config.toml.";
  };

  config = {
    # fix(codex): resolve the machine-local model catalog under this host's home directory.
    my.codex.settings = builtins.fromTOML (builtins.readFile ../dotfiles/.codex/config.toml)
      // { model_catalog_json = modelCatalogFile; };

    # note: Materialize the merged config into the repo so Codex can persist TUI edits.
    home.file.".codex/config.toml".source =
      config.lib.file.mkOutOfStoreSymlink codexConfigFile;

    home.activation.writeCodexConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "$(dirname "${codexConfigFile}")"
      if ! cmp -s ${generatedConfig} "${codexConfigFile}"; then
        install -m 0644 ${generatedConfig} "${codexConfigFile}"
      fi

      # note: Codex refuses to start when model_catalog_json is missing, so generate it on new hosts.
      if [ ! -e "${modelCatalogFile}" ] && [ -e "$HOME/.codex/models_cache.json" ]; then
        ${pkgs.python3}/bin/python3 "${repoRoot}/dotfiles/.codex/patch-model-catalog.py" \
          --output "${modelCatalogFile}" || true
      fi
      if [ ! -e "${modelCatalogFile}" ]; then
        echo "warning: ${modelCatalogFile} unavailable; dropping model_catalog_json from Codex config" >&2
        ${pkgs.gnused}/bin/sed -i '/^model_catalog_json = /d' "${codexConfigFile}"
      fi
    '';
  };
}
