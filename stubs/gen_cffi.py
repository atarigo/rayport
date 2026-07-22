# Portions adapted from raylib-python-cffi's raylib/build.py.
# Copyright (c) 2021 Richard Smith and others.
# Licensed under the Eclipse Public License 2.0.
# SPDX-License-Identifier: EPL-2.0

import sys, os, subprocess, re
from cffi import FFI

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
RAYLIB_SRC = os.path.join(PROJECT_ROOT, ".cache", "raylib-src", "src")

def pre_process_header(filepath, remove_function_bodies=False):
    text = open(filepath).read()
    text = "\n".join(line for line in text.splitlines() if "#include" not in line)
    result = subprocess.run(
        ["gcc", "-CC", "-P", "-undef", "-nostdinc",
         "-DRL_MATRIX_TYPE", "-DRL_QUATERNION_TYPE", "-DRL_VECTOR4_TYPE",
         "-DRL_VECTOR3_TYPE", "-DRL_VECTOR2_TYPE",
         "-DRLAPI=", "-DRMAPI=",
         "-dDI", "-E", "-"],
        text=True, input=text, stdout=subprocess.PIPE
    )
    text = result.stdout.replace("va_list", "void *")
    if remove_function_bodies:
        text = re.sub(r'\n{\n(.|\n)*?\n}\n', ';', text)
    text = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    return text

ffi = FFI()
ffi.cdef(pre_process_header(os.path.join(RAYLIB_SRC, "raylib.h")))
ffi.cdef(pre_process_header(os.path.join(RAYLIB_SRC, "rlgl.h")))
ffi.cdef(pre_process_header(os.path.join(RAYLIB_SRC, "raymath.h"), True))

ffi.set_source(
    "raylib._raylib_cffi",
    """
    #include "raylib.h"
    #include "rlgl.h"
    #include "raymath.h"
    """,
    include_dirs=[RAYLIB_SRC],
)

out = os.path.join(PROJECT_ROOT, ".cache", "_raylib_cffi.c")
ffi.emit_c_code(out)
print(f"Generated {out}")
