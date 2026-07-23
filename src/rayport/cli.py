import argparse
from importlib.metadata import version as package_version
from pathlib import Path

from rayport.config import ConfigError, PRESENTATION_MODES, load_config, validate_web_values
from rayport.packager import pack_game
from rayport.packager import decide_file, inspect_game
from rayport.html_generator import generate_html
from rayport.dev_server import run_dev
from rayport.runtime_files import copy_runtime_distribution, find_runtime_dir
from rayport.output import output_ignore_paths, prepare_output_dir


def cmd_build(args):
    game_dir = Path(args.game_dir).resolve()
    output_dir = Path(args.output).resolve()
    config = load_config(game_dir, args.config)
    title = args.title if args.title is not None else config.web.title
    presentation = args.presentation if args.presentation is not None else config.web.presentation
    background = args.background if args.background is not None else config.web.background
    validate_web_values(title, presentation, background)
    if not (game_dir / "main.py").is_file():
        raise FileNotFoundError(f"main.py not found in {game_dir}")
    runtime_dir = find_runtime_dir()

    ignored_output = output_ignore_paths(game_dir, output_dir)

    if (args.width is None) != (args.height is None):
        raise ConfigError("--width and --height must be provided together")

    if args.list_files:
        for decision in inspect_game(
            str(game_dir),
            exclude=config.package.exclude,
            include=config.package.include,
            ignore_paths=ignored_output,
        ):
            if decision.included:
                print(decision.path)

    prepare_output_dir(game_dir, output_dir, force=args.force_output)

    print(f"Packing game from {game_dir}...")
    dependencies = pack_game(
        str(game_dir),
        str(output_dir / "game.tar.gz"),
        exclude=config.package.exclude,
        include=config.package.include,
        ignore_paths=ignored_output,
    )
    if dependencies:
        names = ", ".join(
            f"{dependency.import_name} "
            f"({dependency.distribution_name} {dependency.version})"
            for dependency in dependencies
        )
        print(f"Bundled Python dependencies: {names}")
        for dependency in dependencies:
            if dependency.skipped_native_files:
                print(
                    f"  {dependency.distribution_name}: skipped "
                    f"{len(dependency.skipped_native_files)} native extension file(s)"
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
    copy_runtime_distribution(runtime_dir, output_dir)

    print(f"Build complete: {output_dir}/")
    print("  index.html, main.wasm, main.js, main.data, game.tar.gz")
    print("  rayport-licenses/LICENSE, rayport-licenses/THIRD_PARTY_NOTICES.md")


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
        presentation=presentation,
        background=background,
        exclude=config.package.exclude,
        include=config.package.include,
        force_output=args.force_output,
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

    decisions = inspect_game(
        str(game_dir),
        exclude=config.package.exclude,
        include=config.package.include,
    )
    if args.sizes:
        if args.limit < 1:
            raise ConfigError("--limit must be at least 1")
        included = sorted(
            (decision for decision in decisions if decision.included),
            key=lambda decision: (-decision.size, decision.path),
        )
        print("Included files by source size:")
        for decision in included[:args.limit]:
            print(f"  {format_size(decision.size):>9}  {decision.path}")
        total = sum(decision.size for decision in included)
        print(f"\n{len(included)} files, {format_size(total)} total before gzip.")

        large = [decision for decision in included if decision.size >= 5 * 1024 * 1024]
        if large:
            print("\nLarge files to review manually (Rayport does not modify assets):")
            for decision in large:
                print(f"  {format_size(decision.size):>9}  {decision.path}")
        return

    for decision in decisions:
        if decision.included or args.excluded:
            state = "include" if decision.included else "exclude"
            print(f"{state:7} {decision.path}  # {decision.reason}")


def format_size(size):
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


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
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version('rayport')}",
    )
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build a game for web deployment")
    build_parser.add_argument("game_dir", nargs="?", default=".", help="Game project directory (default: current directory)")
    build_parser.add_argument("--output", "-o", default="build", help="Output directory (default: build)")
    add_shared_options(build_parser)
    build_parser.add_argument("--width", "-W", type=int, default=None, help="Legacy initial canvas width")
    build_parser.add_argument("--height", "-H", type=int, default=None, help="Legacy initial canvas height")
    build_parser.add_argument("--force-output", action="store_true", help="Replace a non-Rayport output directory")
    build_parser.add_argument("--list-files", action="store_true", help="List packaged files before building")

    dev_parser = subparsers.add_parser("dev", help="Start dev server with live reload")
    dev_parser.add_argument("game_dir", nargs="?", default=".", help="Game project directory (default: current directory)")
    dev_parser.add_argument("--output", "-o", default="build", help="Output directory (default: build)")
    add_shared_options(dev_parser)
    dev_parser.add_argument("--width", "-W", type=int, default=None, help="Legacy initial canvas width")
    dev_parser.add_argument("--height", "-H", type=int, default=None, help="Legacy initial canvas height")
    dev_parser.add_argument("--port", "-p", type=int, default=8080, help="Server port (default: 8080)")
    dev_parser.add_argument("--force-output", action="store_true", help="Replace a non-Rayport output directory")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect game packaging decisions")
    inspect_parser.add_argument("game_dir", nargs="?", default=".", help="Game project directory")
    inspect_parser.add_argument("--config", help="Configuration file (default: GAME_DIR/rayport.toml)")
    inspect_parser.add_argument("--excluded", action="store_true", help="Show excluded files too")
    inspect_parser.add_argument("--explain", metavar="PATH", help="Explain the decision for one relative path")
    inspect_parser.add_argument("--sizes", action="store_true", help="Report included source file sizes")
    inspect_parser.add_argument("--limit", type=int, default=20, help="Maximum files shown by --sizes (default: 20)")

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
