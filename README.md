# nix-home-manager-config

My nix home-manager config.

## Setup

### 1. Install Nix

Use the [Determinate Nix Installer](https://github.com/DeterminateSystems/nix-installer), which handles macOS-specific quirks automatically:

```sh
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Restart your terminal after installation.

### 2. Install standalone home-manager

```sh
nix-channel --add https://github.com/nix-community/home-manager/archive/master.tar.gz home-manager
nix-channel --update
nix-shell '<home-manager>' -A install
```

### 3. Clone this repo and activate

```sh
git clone https://github.com/clliaw/nix-home-manager-config.git
cd nix-home-manager-config
ln -sf "$PWD/home.nix" ~/.config/home-manager/home.nix
home-manager switch -b bak
```

## Usage

Edit `home.nix` and run `home-manager switch` to apply changes.
