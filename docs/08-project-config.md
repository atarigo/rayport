# Module 08: Game Project Configuration

## Configuration File Location

Rayport looks for `rayport.toml` in the game root. Use `--config PATH` to
select another file.

```toml
config-version = 1

[web]
title = "My Game"
presentation = "stretch"
background = "#1a1a2e"

[package]
exclude = ["tests/**", "debug/**", "demo/**"]
include = ["tests/runtime_data/**"]
```

Configuration precedence is: CLI options, `rayport.toml`, then Rayport
defaults. Unknown fields, invalid types, unsupported versions, and unknown
presentation modes fail the build immediately so spelling mistakes are not
silently ignored.

## Web Configuration

- `title`: HTML page title.
- `presentation`: `stretch`, `fit`, `pixel-perfect`, or `native`.
- `background`: CSS color name or hexadecimal color.

Rayport does not infer `InitWindow()` values from Python source or rewrite the
canvas render target from JavaScript. The game code is the only source of the
render resolution; `presentation` controls only the CSS display size.

## Package Configuration

- `exclude`: glob patterns applied after the default exclusion rules.
- `include`: glob patterns that take precedence over all exclusion rules.

`rayport.toml` is not included in the game package by default. Inspect each
file decision without repeatedly extracting the tar archive:

```bash
rayport inspect ./game --excluded
rayport inspect ./game --explain debug/overlay.py
```

After changing the configuration, run `rayport build` again or restart
`rayport dev`.
