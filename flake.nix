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

        pyPkgs = with pkgs.python312Packages; [
          plotly
          pandas
          openpyxl
          pip
        ];

      in
      with pkgs;
      {
        devShells.default = mkShell {
          buildInputs = [
            python312
            uv
            sqlite
          ] ++ pyPkgs;

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
