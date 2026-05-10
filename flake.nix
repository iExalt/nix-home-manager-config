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
      localConfig =
        let
          configFile = ./config.nix;
        in
        if builtins.pathExists configFile
        then import configFile
        else { };
      enabledOverlayNames = localConfig.overlays or [ ];
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
