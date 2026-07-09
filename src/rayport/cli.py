import argparse
import shutil
from pathlib import Path

from rayport.packager import pack_game
from rayport.html_generator import generate_html

RUNTIME_DIR = Path(__file__).parent.parent.parent / "runtime"


def cmd_build(args):
    game_dir = Path(args.game_dir).resolve()
    output_dir = Path(args.output).resolve()

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    print(f"Packing game from {game_dir}...")
    pack_game(str(game_dir), str(output_dir / "game.tar.gz"))

    print("Generating index.html...")
    generate_html(
        str(output_dir / "index.html"),
        title=args.title,
        width=args.width,
        height=args.height,
    )

    print("Copying runtime files...")
    for fname in ["main.wasm", "main.js", "main.data"]:
        src = RUNTIME_DIR / fname
        if not src.exists():
            raise FileNotFoundError(f"Runtime file not found: {src}\nRun 'make runtime' first.")
        shutil.copy2(src, output_dir / fname)

    print(f"Build complete: {output_dir}/")
    print(f"  index.html, main.wasm, main.js, main.data, game.tar.gz")


def main():
    parser = argparse.ArgumentParser(prog="rayport", description="Package raylib Python games for the web")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build a game for web deployment")
    build_parser.add_argument("game_dir", help="Path to the game project directory (must contain main.py)")
    build_parser.add_argument("--output", "-o", default="build", help="Output directory (default: build)")
    build_parser.add_argument("--title", "-t", default="rayport game", help="Game title (default: rayport game)")
    build_parser.add_argument("--width", "-W", type=int, default=800, help="Canvas width (default: 800)")
    build_parser.add_argument("--height", "-H", type=int, default=450, help="Canvas height (default: 450)")

    args = parser.parse_args()
    if args.command == "build":
        cmd_build(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
