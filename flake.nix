{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        pkgs.xorg.libX11
        pkgs.xorg.libXext
        pkgs.xorg.libXt
        pkgs.xorg.libXrender
        pkgs.xorg.libXmu
        pkgs.python312
        pkgs.python312Packages.vtk
        pkgs.python312Packages.numpy
        pkgs.libGL
        pkgs.libGLU
        pkgs.mesa
      ];

      shellHook = ''
        export LD_LIBRARY_PATH=${pkgs.mesa}/lib:${pkgs.libGL}/lib:$LD_LIBRARY_PATH
      '';
    };
  };
}
