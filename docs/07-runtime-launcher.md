# Module 07: Runtime Launcher

## Purpose

Configure the environment and run the user's game after the CPython
interpreter starts inside WebAssembly.

## How It Works

`launcher.py` performs three tasks:

1. Change the working directory to `/usr/local/game/`, where game files are
   extracted.
2. Add `/usr/local/game/` to `sys.path`, allowing game code to import other
   modules from the same directory.
3. Execute the game entry point with
   `runpy.run_path("main.py", run_name="__main__")`.

During the build, `launcher.py` is copied to the preload directory at
`/usr/local/lib/python3.12/` and embedded in `main.data`. The HTML shell sets
Emscripten's `Module.arguments` to
`["/usr/local/lib/python3.12/launcher.py"]`, causing CPython to execute the
launcher directly instead of entering the REPL.

## Related Files

- `stubs/launcher.py`: launcher source.
- `Makefile` (`install-raylib-py` target): copies `launcher.py` into the preload
  directory.
- `src/rayport/templates/index.html`: `Module.arguments` configuration.
