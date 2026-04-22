# nix-home-manager-config

My nix home-manager config (flake-based).

## Setup

The easiest path is the quickstart script, which installs Determinate Nix and
applies the flake:

```sh
git clone https://github.com/clliaw/nix-home-manager-config.git ~/Projects/nix-home-manager-config
cd ~/Projects/nix-home-manager-config
./quickstart.sh
```

### Manual setup

1. Install [Determinate Nix](https://github.com/DeterminateSystems/nix-installer)
   (flakes are enabled by default):

   ```sh
   curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --determinate
   ```

2. Clone this repo to `~/Projects/nix-home-manager-config` (the path matters
   for a few `mkOutOfStoreSymlink` dotfiles referenced from `home.nix`).

3. Apply the config:

   ```sh
   nix run github:nix-community/home-manager/release-25.11 -- \
     switch --flake ~/Projects/nix-home-manager-config#clliaw@x86_64-linux -b backup
   ```

   Replace `x86_64-linux` with your system (`aarch64-linux`, `aarch64-darwin`).

## Usage

Edit `home.nix` and run `home-manager switch --flake .#clliaw@$(nix eval --impure --raw --expr 'builtins.currentSystem')`
to apply changes. Commit `flake.lock` to pin inputs.
