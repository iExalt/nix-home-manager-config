#!/bin/bash

home-manager switch --flake .#$(nix eval --impure --raw --expr 'builtins.currentSystem') --impure
