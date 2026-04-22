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
   nix run github:nix-community/home-manager -- \
     switch --flake ~/Projects/nix-home-manager-config#x86_64-linux -b backup --impure
   ```

   Replace `x86_64-linux` with your system (`aarch64-linux`, `aarch64-darwin`).
   `--impure` is required — the flake reads `$USER` and `$HOME` at eval
   time so the same config works for any login user.

## Usage

Edit `home.nix` and run:

```sh
home-manager switch --flake .#$(nix eval --impure --raw --expr 'builtins.currentSystem') --impure
```

To pull in newer package versions (nixpkgs + home-manager track rolling
unstable), run `nix flake update` then re-switch. Commit `flake.lock`
to pin inputs between updates.
