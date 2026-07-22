# Third-party notices

This file lists software that is copied into or linked into Rayport's default
WebAssembly runtime. Build-only tools that do not enter the distributed files
are not listed. Full license texts are in `LICENSE` and
`third_party_licenses/`.

## Runtime inventory

| Component | Version used by the checked-in runtime | Source | License | Distribution form |
|---|---|---|---|---|
| Rayport | 0.2.1 | https://github.com/atarigo/rayport | EPL-2.0 | Python package, launcher and generated web files |
| raylib-python-cffi | 6.0.1.1, commit `caf21da0692693d00a07dab243acc3430f741e43` | https://github.com/electronstudio/raylib-python-cffi | EPL-2.0 | Four Python files in `main.data`; `gen_cffi.py` is adapted from its build script |
| raylib | 5.5, commit `c1ab645ca298a2801097931d1079b10ff7eb9df8` | https://github.com/raysan5/raylib | Zlib | Statically linked into `main.wasm` |
| CPython | 3.12.11, commit `55fee9cf216abe4ec0d1139f94b1930fbd0c7644` | https://github.com/python/cpython | PSF-2.0 and historical Python licenses | Interpreter in `main.wasm`; standard library in `main.data` |
| CFFI | 2.1.0 | https://github.com/python-cffi/cffi | MIT-0 | `_cffi_backend` compiled into `main.wasm` |
| libffi headers | 3.4.2 vendored by CFFI | https://github.com/libffi/libffi | MIT | Type declarations used to compile Rayport's local stubs; libffi itself is not linked |
| Emscripten | 3.1.61, commit `67fa4c16496b157a7fc3377afd69ee0445e8a6e3` | https://github.com/emscripten-core/emscripten | MIT or NCSA; Rayport uses MIT | Generated JavaScript, WebAssembly support code and system libraries |
| musl libc | bundled with Emscripten 3.1.61 | https://musl.libc.org | MIT and compatible notices | Linked into `main.wasm` by Emscripten |
| compiler-rt | bundled with Emscripten 3.1.61 | https://compiler-rt.llvm.org | Apache-2.0 WITH LLVM-exception | Compiler support routines linked into `main.wasm` |
| zlib | 1.2.13 | https://github.com/madler/zlib | Zlib | Linked through Emscripten `USE_ZLIB` |
| bzip2 | 1.0.6 | https://sourceware.org/bzip2/ | bzip2 license | Linked through Emscripten `USE_BZIP2` |
| SQLite | 3.39.0 | https://www.sqlite.org | Public domain | Linked through Emscripten `USE_SQLITE3` |
| Expat | 2.7.1, bundled with CPython 3.12.11 | https://github.com/libexpat/libexpat | MIT | Statically linked into `main.wasm` |
| libmpdec | 2.5.1, bundled with CPython 3.12.11 | https://www.bytereef.org/mpdecimal/ | BSD-2-Clause | Statically linked into `main.wasm` |
| HACL* SHA-2 | bundled with CPython 3.12.11 | https://github.com/hacl-star/hacl-star | MIT | Statically linked into `main.wasm` |
| raylib bundled external libraries | bundled with raylib 5.5 | raylib `src/external` | MIT, MIT-0, Zlib, public-domain alternatives and WTFPL-2.0 | Compiled into raylib according to Rayport's default raylib configuration |

The checked-in runtime files were rebuilt in Rayport commit `d15b31f` using
the versions configured by the Makefile. Their SHA-256 values are:

- `main.wasm`: `75298c5476aa6ad652a57ede1f691683d1a8235c8c8279dff973dfc8e2345790`
- `main.js`: `a316de2b61478761a5d117d63d615f50660e74f28ae69190106bd981301ca639`
- `main.data`: `e81804f022f629f0b12cdc0a8e39b5c2abd0173fed3f4a5c0b1c35bd5191669d`

## raylib-python-cffi notice

Copyright (c) 2021 Richard Smith and others.

Rayport's `stubs/gen_cffi.py` is adapted from
`raylib-python-cffi/raylib/build.py`. The runtime build copies `colors.py`,
`defines.py`, `enums.py`, and `version.py` from raylib-python-cffi.

These portions are distributed under the Eclipse Public License 2.0. The full
license is included in `LICENSE`. Source code for Rayport's EPL-covered
components is available at https://github.com/atarigo/rayport. The upstream
source is available from the raylib-python-cffi repository listed above.

## raylib notice

Copyright (c) 2013-2024 Ramon Santamaria (@raysan5).

This software is provided "as-is", without any express or implied warranty. In
no event will the authors be held liable for any damages arising from the use
of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it freely,
subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not claim
   that you wrote the original software. If you use this software in a product,
   an acknowledgment in the product documentation would be appreciated but is
   not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.

The licenses and notices for external single-file libraries compiled as part
of raylib are reproduced in `third_party_licenses/raylib-external.txt`.

## Scope

These notices apply to Rayport and its bundled runtime. They do not change the
license of an independent game merely packaged by Rayport. A custom runtime may
contain a different component set and must provide notices matching that
runtime.
