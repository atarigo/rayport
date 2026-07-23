# Module 03: Game Loop

## Purpose

Allow a Python game loop such as `while not WindowShouldClose()` to continue
running in the browser without freezing the page.

## Problem

Browser JavaScript is single-threaded. If a Python `while` loop continuously
occupies that thread, the browser cannot update the display or process input,
and the page freezes.

## Solution: ASYNCIFY

raylib's C code calls `emscripten_sleep(12)` inside `WindowShouldClose()`,
pausing for 12 milliseconds and returning control to the browser. Emscripten's
ASYNCIFY feature saves the complete C call stack, including CPython's
`ceval.c` evaluation loop, and restores it after the pause.

Linker flags: `-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536`.

The user's Python game code requires no changes. A standard raylib loop runs
directly:

```python
while not WindowShouldClose():
    BeginDrawing()
    ClearBackground(RAYWHITE)
    DrawText(b"Hello", 10, 10, 20, RED)
    EndDrawing()
```

## Prerequisite

ASYNCIFY requires static linking. Module 01 removed `-sMAIN_MODULE` in favor of
fully static linking, allowing ASYNCIFY to cross CPython's interpreter loop.
With dynamic linking, ASYNCIFY cannot track the call stack across modules.

## Related Files

- `Makefile` (`link` target): the
  `-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536` linker flags.
