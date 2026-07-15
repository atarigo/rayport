import argparse
import shutil
from pathlib import Path

from rayport.config import ConfigError, PRESENTATION_MODES, load_config, validate_web_values
from rayport.packager import pack_game
from rayport.packager import decide_file, inspect_game
from rayport.html_generator import generate_html
from rayport.dev_server import run_dev
from rayport.runtime_files import RUNTIME_FILENAMES, find_runtime_dir


def cmd_build(args):
    game_dir = Path(args.game_dir).resolve()
    output_dir = Path(args.output).resolve()
    config = load_config(game_dir, args.config)
    title = args.title if args.title is not None else config.web.title
    presentation = args.presentation if args.presentation is not None else config.web.presentation
    background = args.background if args.background is not None else config.web.background
    validate_web_values(title, presentation, background)

    if (args.width is None) != (args.height is None):
        raise ConfigError("--width and --height must be provided together")

    if args.list_files:
        for decision in inspect_game(
            str(game_dir),
            exclude=config.package.exclude,
            include=config.package.include,
        ):
            if decision.included:
                print(decision.path)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    print(f"Packing game from {game_dir}...")
    pack_game(
        str(game_dir),
        str(output_dir / "game.tar.gz"),
        optimize=args.optimize,
        exclude=config.package.exclude,
        include=config.package.include,
    )

    print("Generating index.html...")
    generate_html(
        str(output_dir / "index.html"),
        title=title,
        width=args.width,
        height=args.height,
        presentation=presentation,
        background=background,
    )

    print("Copying runtime files...")
    runtime_dir = find_runtime_dir()
    for fname in RUNTIME_FILENAMES:
        src = runtime_dir / fname
        shutil.copy2(src, output_dir / fname)

    print(f"Build complete: {output_dir}/")
    print(f"  index.html, main.wasm, main.js, main.data, game.tar.gz")


def cmd_dev(args):
    if (args.width is None) != (args.height is None):
        raise ConfigError("--width and --height must be provided together")
    config = load_config(args.game_dir, args.config)
    title = args.title if args.title is not None else config.web.title
    presentation = args.presentation if args.presentation is not None else config.web.presentation
    background = args.background if args.background is not None else config.web.background
    validate_web_values(title, presentation, background)
    run_dev(
        game_dir=args.game_dir,
        output_dir=args.output,
        title=title,
        width=args.width,
        height=args.height,
        port=args.port,
        optimize=args.optimize,
        presentation=presentation,
        background=background,
        exclude=config.package.exclude,
        include=config.package.include,
    )


def cmd_inspect(args):
    game_dir = Path(args.game_dir).resolve()
    config = load_config(game_dir, args.config)
    if args.explain:
        decision = decide_file(
            args.explain,
            exclude=config.package.exclude,
            include=config.package.include,
        )
        state = "included" if decision.included else "excluded"
        print(f"{decision.path}: {state} ({decision.reason})")
        return

    for decision in inspect_game(
        str(game_dir),
        exclude=config.package.exclude,
        include=config.package.include,
    ):
        if decision.included or args.excluded:
            state = "include" if decision.included else "exclude"
            print(f"{state:7} {decision.path}  # {decision.reason}")


def add_shared_options(parser):
    parser.add_argument("--config", help="Configuration file (default: GAME_DIR/rayport.toml)")
    parser.add_argument("--title", "-t", default=None, help="Override web page title")
    parser.add_argument(
        "--presentation",
        choices=sorted(PRESENTATION_MODES),
        default=None,
        help="Override canvas presentation mode",
    )
    parser.add_argument("--background", default=None, help="Override page background color")


def main():
    parser = argparse.ArgumentParser(prog="rayport", description="Package raylib Python games for the web")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build a game for web deployment")
    build_parser.add_argument("game_dir", nargs="?", default=".", help="Game project directory (default: current directory)")
    build_parser.add_argument("--output", "-o", default="build", help="Output directory (default: build)")
    add_shared_options(build_parser)
    build_parser.add_argument("--width", "-W", type=int, default=None, help="Legacy initial canvas width")
    build_parser.add_argument("--height", "-H", type=int, default=None, help="Legacy initial canvas height")
    build_parser.add_argument("--optimize", action="store_true", help="Optimize PNG and audio assets (requires pngquant and ffmpeg)")
    build_parser.add_argument("--list-files", action="store_true", help="List packaged files before building")

    dev_parser = subparsers.add_parser("dev", help="Start dev server with live reload")
    dev_parser.add_argument("game_dir", nargs="?", default=".", help="Game project directory (default: current directory)")
    dev_parser.add_argument("--output", "-o", default="build", help="Output directory (default: build)")
    add_shared_options(dev_parser)
    dev_parser.add_argument("--width", "-W", type=int, default=None, help="Legacy initial canvas width")
    dev_parser.add_argument("--height", "-H", type=int, default=None, help="Legacy initial canvas height")
    dev_parser.add_argument("--port", "-p", type=int, default=8080, help="Server port (default: 8080)")
    dev_parser.add_argument("--optimize", action="store_true", help="Optimize PNG and audio assets (requires pngquant and ffmpeg)")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect game packaging decisions")
    inspect_parser.add_argument("game_dir", nargs="?", default=".", help="Game project directory")
    inspect_parser.add_argument("--config", help="Configuration file (default: GAME_DIR/rayport.toml)")
    inspect_parser.add_argument("--excluded", action="store_true", help="Show excluded files too")
    inspect_parser.add_argument("--explain", metavar="PATH", help="Explain the decision for one relative path")

    args = parser.parse_args()
    try:
        if args.command == "build":
            cmd_build(args)
        elif args.command == "dev":
            cmd_dev(args)
        elif args.command == "inspect":
            cmd_inspect(args)
        else:
            parser.print_help()
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
