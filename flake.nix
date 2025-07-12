{
  description = "Development shell with python tools used random scripts and tax work";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

      in
      with pkgs;
      {
        devShells.default = mkShell {
          buildInputs = [
            python312
            uv
            python312Packages.plotly
            sqlite
          ];
          shellHook = ''
            source .venv/bin/activate
            export $(cat .env)
          '';

        };
      }
    );
}
