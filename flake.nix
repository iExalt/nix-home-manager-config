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
    ponytail = {
      url = "github:DietrichGebert/ponytail/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846";
      flake = false;
    };
    mattpocock-skills = {
      url = "github:mattpocock/skills/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d";
      flake = false;
    };
  };

  outputs = { nixpkgs, home-manager, ponytail, mattpocock-skills, ... }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      availableOverlays = {
        grafana-mcp = ./overlays/grafana-mcp.nix;
        victoria-metrics-mcp = ./overlays/victoria-metrics-mcp.nix;
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
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ (import ./overlays/mise.nix) ];
          };
          extraSpecialArgs = { inherit ponytail mattpocock-skills; };
          modules = [
            ./modules/ponytail-skills.nix
            ./modules/mattpocock-skills.nix
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
