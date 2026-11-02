final: prev:
let
  releases = {
    aarch64-darwin = {
      platform = "macos-arm64";
      hash = "sha256-d0I24yR+SNeAeMC8555TJ9TkR58alMhIeCfxeBl+45s=";
    };
    aarch64-linux = {
      platform = "linux-arm64-musl";
      hash = "sha256-hYS9mn6Aq0byCrz69tC5ob0hb7qougDFiogUtHpWU0Y=";
    };
    x86_64-linux = {
      platform = "linux-x64-musl";
      hash = "sha256-G8spE5agAsth2QlNuw0GR0q8PfTRq04f31ncZpynNQY=";
    };
  };
  release = releases.${final.stdenv.hostPlatform.system};
in
{
  # Use pinned upstream binaries to avoid a local Rust build on each upgrade.
  mise = final.stdenvNoCC.mkDerivation (finalAttrs: {
    pname = "mise";
    version = "2026.10.25";
    src = final.fetchurl {
      url = "https://github.com/jdx/mise/releases/download/v${finalAttrs.version}/mise-v${finalAttrs.version}-${release.platform}.tar.gz";
      inherit (release) hash;
    };
    nativeBuildInputs = [ final.installShellFiles ];
    dontBuild = true;
    # Preserve the upstream-signed macOS executable.
    dontStrip = true;
    installPhase = ''
      runHook preInstall
      install -Dm755 bin/mise "$out/bin/mise"
      installManPage man/man1/mise.1
      for shell in bash fish zsh; do
        "$out/bin/mise" completion "$shell" > "mise.$shell"
        installShellCompletion --cmd mise --$shell "mise.$shell"
      done
      mkdir -p "$out/lib/mise"
      touch "$out/lib/mise/.disable-self-update"
      runHook postInstall
    '';
    doInstallCheck = true;
    installCheckPhase = ''
      runHook preInstallCheck
      "$out/bin/mise" --version | grep -F '${finalAttrs.version}'
      runHook postInstallCheck
    '';
    meta = prev.mise.meta // {
      changelog = "https://github.com/jdx/mise/releases/tag/v${finalAttrs.version}";
      platforms = builtins.attrNames releases;
    };
  });
}
