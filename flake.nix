{
  description = "Development shell with python tools used random scripts and tax work";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
    flake-utils.url = "github:numtide/flake-utils";
    naersk.url = "github:nix-community/naersk";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      naersk,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        #naersk' = pkgs.callPackage naersk { };

        pyPkgs = with pkgs.python312Packages; [
          plotly
          pandas
          openpyxl
          pip
        ];

      in
      with pkgs;
      {
        defaultPackage = naersk-lib.buildPackage ./property;
        devShells.default = mkShell {
          buildInputs = [
            python312
            uv
            sqlite
            cargo
            rustc
            rustfmt
            pre-commit
            rustPackages.clippy

            openssl
            pkg-config
            libsodium
            zlib
            binutils
          ]
          ++ pyPkgs;

          RUST_SRC_PATH = rustPlatform.rustLibSrc;

          shellHook = ''
            echo "sourcing venv"
            source .venv/bin/activate
            export $(cat .env)
            echo "sourced venv"
          '';

        };
      }
    );
}
