{
  description = "Development shell with Plotly and Python 12";

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
            			source budget/.venv/bin/activate
            			'';


        };
      stdenv.mkDerivation {
        name = "hello-flake-package";
        src = ./.;
        installPhase = ''
          mkdir -p $out/bin
          cp hello.sh $out/bin/hello.sh
          chmod +x $out/bin/hello.sh
        '';
		};
      };
    );
}
