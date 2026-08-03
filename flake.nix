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

            gnumake

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

        # This vibecoded thing doesn't actually work but does a bunch of packaging. 
        # TODO: Fix or delete.
        packages = {
          default = self.packages.${system}.hsbc-download;

          hsbc-download = pkgs.writeShellApplication {
            name = "hsbc-download";
            runtimeInputs = [
              pythonEnv
              pkgs.xvfb-run
              pkgs.xorg.xorgserver
              pkgs.scrot
              pkgs.xdotool
              pkgs.firefox
            ];
            text = ''
              pkill firefox || true

              export DOWNLOAD_PNG_PATH="${./download.png}"
              touch "$HOME/.Xauthority" || true
              2>/dev/null 1>&2 Xvfb :99 -screen 0 1920x1080x24 &
              sleep 1
              2>/dev/null 1>&2 x11vnc -display :99 -localhost -forever -passwd mysecret &
              sleep 1
              export DISPLAY=:99; 2>/dev/null 1>&2 firefox -P default --width 1800 --height 900 "https://www.hsbc.com.au" &

              sleep 10
              export DISPLAY=:99; python3 ${./bank-statements}/hsbc.py 
              rm ~/.Xauthority || true

              pkill firefox || true
            '';
          };
        };
      }
    );
}
