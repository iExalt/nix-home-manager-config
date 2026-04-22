{
  description = "clliaw home-manager configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    home-manager = {
      url = "github:nix-community/home-manager/release-25.11";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, home-manager, ... }:
    let
      username = "clliaw";
      mkHome = system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          isDarwin = pkgs.stdenv.hostPlatform.isDarwin;
        in
        home-manager.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            ./home.nix
            {
              home.username = username;
              home.homeDirectory =
                if isDarwin then "/Users/${username}" else "/home/${username}";
            }
          ];
        };
    in
    {
      homeConfigurations = {
        "${username}@x86_64-linux" = mkHome "x86_64-linux";
        "${username}@aarch64-linux" = mkHome "aarch64-linux";
        "${username}@aarch64-darwin" = mkHome "aarch64-darwin";
      };
    };
}
