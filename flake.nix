{
  description = "Development shell with python tools used random scripts and tax work";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";

  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      rust-overlay,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };

        rustToolchain = pkgs.pkgsBuildHost.rust-bin.fromRustupToolchainFile ./rust-toolchain.toml;

        pythonEnv = pkgs.python313.withPackages (
          ps: with ps; [
            pip
            pyautogui
            tkinter
            opencv-python
          ]
        );
        # pyPkgs = with pkgs.python313Packages.withPackages; [
        #   pip
        #   pyautogui
        #   tkinter
        # ];
        nativeBuildInputs = with pkgs; [
          rustToolchain
          pkg-config
        ];

      in
      with pkgs;
      {
        devShells.default = mkShell {
          inherit nativeBuildInputs;
          buildInputs = [
            pythonEnv
            uv
            sqlite
            cargo
            pre-commit

            xvfb-run
            scrot
            xorg.xorgserver # provides the Xvfb binary itself
            x11vnc # For debugging.

            openssl
            pkg-config
            libsodium
            zlib
            binutils
          ];
          packages = [ pythonEnv ];
          # ++ pyPkgs;

          RUST_SRC_PATH = "${rustToolchain}/lib/rustlib/src/rust/library";
          # RUST_SRC_PATH = "${pkgs.latest.rustChannels.stable.rust-src}/lib/rustlib/src/rust/library";

          shellHook = ''
            echo "sourcing venv"
            #source .venv/bin/activate
            set -o allexport && source .env && set +o allexport
            echo "sourced venv"
          '';

        };
      }
    );
}
