{
  description = "obsidian-html builder";
  inputs.flake-utils = {
    url = "github:numtide/flake-utils";
  };
  inputs.nixpkgs = {
    url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
        };

        makeYaml = config: let
          configFile = pkgs.writeText "config.yml" (builtins.toJSON config);
        in
          pkgs.runCommandNoCC "config.yml" {} ''
            (${pkgs.yj}/bin/yj -jy < ${configFile}) > $out
          '';

        setup = builtins.fromJSON (builtins.readFile (pkgs.runCommandNoCC "setup.cfg" {} ''
          cat ${./setup.cfg} | ${pkgs.python3Packages.jc}/bin/jc --ini > $out
        ''));

        depNames = map (x: builtins.head(pkgs.lib.strings.splitString " " x)) (pkgs.lib.remove "" (pkgs.lib.splitString "\n"
          setup
          .options
          .install_requires));

        deps = pkgs.lib.attrsets.attrVals depNames pkgs.python3Packages;
      in rec {
        packages.default = pkgs.python3.pkgs.buildPythonApplication rec {
          pname = setup.metadata.name;
          version = setup.metadata.version;
          format = "pyproject";

          checkPhase = ''
            export PATH="$PATH:$out/bin"
            ${pkgs.python3}/bin/python3 ci/tests/basic_regression_test.py
          '';

          src = ./.;

          propagatedBuildInputs = deps;
        };

        checks.default = packages.default;

        devShells.default = let
          myPython = pkgs.python3.withPackages (p: pkgs.lib.attrsets.attrVals depNames p);
        in
          pkgs.mkShell {
            buildInputs = [
              myPython
            ];
            shellHook = ''
              PYTHONPATH=${myPython}/${myPython.sitePackages}
            '';
          };

        mkProject = args: let
          config =
            {
              obsidian_folder_path_str = args.src;
              obsidian_entrypoint_path_str = "${args.src}/${args.entrypoint}";
              md_folder_path_str = "mdout";
              md_entrypoint_path_str = "mdout/${args.entrypoint}";
              html_output_folder_path_str = "htmlout";
              copy_vault_to_tempdir = false;
              site_name = args.name;
            }
            // (removeAttrs args ["obsidian_folder_path_str" "entrypoint" "src" "name" "md_folder_path_str" "md_entrypoint_path_str" "html_output_folder_path_str"]);
          yamlConfig = makeYaml config;
        in {
          compile = pkgs.runCommandNoCC args.name {outputs = ["out" "md"];} ''
            ln -s $out htmlout
            ln -s $md mdout
            ${packages.default}/bin/obsidianhtml convert -i ${yamlConfig}
          '';
          run = pkgs.writeShellApplication {
            name = "run";
            text = ''
              TEMP=$(mktemp -d)
              cd "$TEMP"
              ${packages.default}/bin/obsidianhtml run -i ${yamlConfig}
            '';
          };
        };

        apps.default = flake-utils.lib.mkApp {
          drv = packages.default;
        };
      }
    );
}

