# Third-party notices

Rayport distributes and builds upon the following software.

## raylib-python-cffi

- Project: https://github.com/electronstudio/raylib-python-cffi
- License: Eclipse Public License 2.0
- Copyright: Copyright (c) 2021 Richard Smith and others

Rayport's `stubs/gen_cffi.py` is adapted from
`raylib-python-cffi/raylib/build.py`. The prebuilt runtime also contains
`colors.py`, `defines.py`, `enums.py`, and `version.py` copied from
raylib-python-cffi during the runtime build.

The complete Eclipse Public License 2.0 is included in `LICENSE`. Source code
for Rayport's EPL-covered components is available at
https://github.com/atarigo/rayport. The corresponding upstream source is
available from the raylib-python-cffi project above.

## raylib

- Project: https://github.com/raysan5/raylib
- Default runtime version: 5.5
- License: zlib/libpng license
- Copyright: Copyright (c) 2013-2024 Ramon Santamaria (@raysan5)

Rayport links raylib into its WebAssembly runtime. The raylib license follows:

> This software is provided "as-is", without any express or implied warranty.
> In no event will the authors be held liable for any damages arising from the
> use of this software.
>
> Permission is granted to anyone to use this software for any purpose,
> including commercial applications, and to alter it and redistribute it
> freely, subject to the following restrictions:
>
> 1. The origin of this software must not be misrepresented; you must not claim
>    that you wrote the original software. If you use this software in a
>    product, an acknowledgment in the product documentation would be
>    appreciated but is not required.
> 2. Altered source versions must be plainly marked as such, and must not be
>    misrepresented as being the original software.
> 3. This notice may not be removed or altered from any source distribution.

These notices describe components distributed by Rayport. They do not change
the license of an independent game merely packaged by Rayport.
