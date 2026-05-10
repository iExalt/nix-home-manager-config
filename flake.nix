{
  description = "home-manager configuration";

  inputs = {
    # Rolling unstable so user tools (mise, etc.) don't lag months
    # behind. Run `nix flake update` to advance the pin; `flake.lock`
    # still guarantees reproducibility between updates.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, home-manager, ... }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      availableOverlays = {
        grafana-mcp = ./overlays/grafana-mcp.nix;
      };
      overlayNamesFromEnv =
        lib.filter (name: name != "") (
          lib.splitString "," (builtins.getEnv "HM_OVERLAYS")
        );
      overlayNamesFromFile =
        let
          overlayFile =
            if builtins.getEnv "HM_OVERLAYS_FILE" != ""
            then builtins.getEnv "HM_OVERLAYS_FILE"
            else "${builtins.getEnv "HOME"}/.config/nix-home-manager/overlays.nix";
        in
        if overlayFile != "" && builtins.pathExists overlayFile
        then import overlayFile
        else [ ];
      enabledOverlayNames = lib.unique (overlayNamesFromFile ++ overlayNamesFromEnv);
      enabledOverlayModules =
        map
          (name:
            availableOverlays.${name} or (throw "Unknown home-manager overlay '${name}'"))
          enabledOverlayNames;
      mkHome = system:
        home-manager.lib.homeManagerConfiguration {
          pkgs = nixpkgs.legacyPackages.${system};
          modules = [
            ./modules/claude-config.nix
            ./modules/codex-config.nix
            ./home.nix
            {
              # Read at eval time — requires `--impure`. Keeps the flake
              # portable across VMs where the login user isn't "clliaw"
              # (e.g. cloud dev boxes named after the provider account).
              home.username = builtins.getEnv "USER";
              home.homeDirectory = builtins.getEnv "HOME";
            }
          ] ++ enabledOverlayModules;
        };
    in
    {
      homeConfigurations = nixpkgs.lib.genAttrs systems mkHome;
    };
}
