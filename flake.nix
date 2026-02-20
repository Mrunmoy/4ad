{
  description = "Four Against Darkness - CLI dungeon crawler in Rust";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, rust-overlay, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs { inherit system overlays; };
        rustToolchain = pkgs.rust-bin.fromRustupToolchainFile ./rust-toolchain.toml;

        # Phase definitions - update current_phase as you progress
        shellHook = ''
          PHASE_FILE="$PWD/.phase"
          if [ ! -f "$PHASE_FILE" ]; then
            echo "1" > "$PHASE_FILE"
          fi
          CURRENT_PHASE=$(cat "$PHASE_FILE")

          case "$CURRENT_PHASE" in
            1) PHASE_NAME="The Descent Begins"
               PHASE_DESC="Solo play MVP - dice, classes, dungeon gen, combat, ASCII map"
               PHASE_ICON="[I]"
               ROOM_ART='
    +=====+  You stand at the dungeon entrance.
    |.....+  Torchlight flickers off damp stone walls.
    |.@...|  Your party of four readies their weapons.
    |.....|
    +==D==+  The foundation must be laid...
               '
               ;;
            2) PHASE_NAME="Into the Depths"
               PHASE_DESC="Complete rules engine - monsters, spells, gear, quests, bosses"
               PHASE_ICON="[II]"
               ROOM_ART='
    +=====+=====+  The dungeon sprawls before you.
    |.....D..$!.|  Monsters lurk in every shadow.
    |..@..+--+..|  Spells crackle, steel rings,
    |.....|##|.B|  and a boss awaits below...
    +==D==+=====+
               '
               ;;
            3) PHASE_NAME="The Gilded Halls"
               PHASE_DESC="TUI polish - split-pane, colors, dice animation, help overlay"
               PHASE_ICON="[III]"
               ROOM_ART='
    +=========+=======+  The dungeon gleams with new light.
    |         | HP:18 |  Colors dance across the walls.
    |  @-->B  | Lv: 3 |  Every surface polished to
    |         +-------+  a brilliant sheen.
    +====D====| LOG:  |
    | ROLL: 6!| Atk!! |  Beauty in the darkness...
    +=========+=======+
               '
               ;;
            4) PHASE_NAME="The Alliance"
               PHASE_DESC="LAN multiplayer - tokio server/client, UDP discovery, turn sync"
               PHASE_ICON="[IV]"
               ROOM_ART='
       @----TCP----@     Heroes from distant lands
       |   :7777   |     join forces over the network.
       +---HOST----+     UDP beacons light the way.
       |   :7777   |
       @----TCP----@     No one fights alone.
               '
               ;;
            *) PHASE_NAME="Unknown Phase"
               PHASE_DESC="Set .phase to 1-4"
               PHASE_ICON="[?]"
               ROOM_ART=""
               ;;
          esac

          RUST_V=$(rustc --version | cut -d' ' -f2)

          echo ""
          echo -e "\033[33m  ______                     _____            _           _     _____            _"
          echo -e " |  ____|                   / __  \          (_)         | |   |  __ \          | |"
          echo -e "  | |__ ___  _   _ _ __    | |__| | __ _  __ _ _ __  ___| |_  | |  | | __ _ _ __| | __"
          echo -e "  |  __/ _ \| | | | '__|   |  __  |/ _\` |/ _\` | '_ \/ __| __| | |  | |/ _\` | '__| |/ /"
          echo -e "  | | | (_) | |_| | |      | |  | | (_| | (_| | | | \__ \ |_  | |__| | (_| | |  |   <"
          echo -e "  |_|  \___/ \__,_|_|      |_|  |_|\__, |\__,_|_| |_|___/\__| |_____/ \__,_|_|  |_|\_\\"
          echo -e "                                     __/ |"
          echo -e "                                    |___/\033[0m"
          echo ""
          echo -e "  \033[36m--- Phase $PHASE_ICON: $PHASE_NAME ---\033[0m"
          echo -e "  \033[2m$PHASE_DESC\033[0m"
          echo -e "\033[32m$ROOM_ART\033[0m"
          echo -e "  \033[2mRust $RUST_V | cargo build | cargo test | cargo run\033[0m"
          echo -e "  \033[2mAdvance phase: echo N > .phase  (N = 1..4)\033[0m"
          echo ""

          export PS1=$'\n\033[33m[4AD]\033[0m \033[36mPhase '"$PHASE_ICON"$'\033[0m \033[32m\w\033[0m\n\033[33m>>> \033[0m'
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            rustToolchain
            pkgs.pkg-config
          ];
          inherit shellHook;
        };
      }
    );
}
