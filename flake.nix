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
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      mkHome = system:
        home-manager.lib.homeManagerConfiguration {
          pkgs = nixpkgs.legacyPackages.${system};
          modules = [
            ./home.nix
            {
              # Read at eval time — requires `--impure`. Keeps the flake
              # portable across VMs where the login user isn't "clliaw"
              # (e.g. cloud dev boxes named after the provider account).
              home.username = builtins.getEnv "USER";
              home.homeDirectory = builtins.getEnv "HOME";
            }
          ];
        };
    in
    {
      homeConfigurations = nixpkgs.lib.genAttrs systems mkHome;
    };
}
