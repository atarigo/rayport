# =============================================================================
# Rayport runtime build
#
# Produces a WebAssembly binary containing CPython, raylib, and CFFI bindings.
# Build flow: clone sources -> build native Python -> cross-compile wasm ->
#             compile raylib -> generate CFFI bindings -> compile modules ->
#             patch config.c -> install Python files -> link -> copy package data
# =============================================================================

# --- Configuration defaults (overridable in build.conf) ---
-include build.conf

EMSDK_PATH       ?= /tmp/rayport-emsdk
EMSDK_VERSION    ?= 3.1.61
EMSDK_REPO       ?= https://github.com/emscripten-core/emsdk.git
CPYTHON_VERSION  ?= v3.12.11
CPYTHON_REPO     ?= https://github.com/python/cpython.git
RAYLIB_VERSION   ?= 5.5
RAYLIB_REPO      ?= https://github.com/raysan5/raylib.git
RAYLIB_CFFI_REPO ?= https://github.com/electronstudio/raylib-python-cffi.git

# --- Emscripten tool paths (override stale emsdk shell variables) ---
export EM_CONFIG     = $(EMSDK_PATH)/.emscripten
export EMSDK         = $(EMSDK_PATH)
export EMSDK_PYTHON := python3
export EMSDK_NODE   :=
unexport SSL_CERT_FILE
export PATH         := $(EMSDK_PATH):$(EMSDK_PATH)/upstream/emscripten:$(PATH)
EMCC                 = $(EMSDK_PATH)/upstream/emscripten/emcc
EMAR                 = $(EMSDK_PATH)/upstream/emscripten/emar

# --- Directory and file variables ---
CACHE           = .cache
CPYTHON_SRC     = $(CACHE)/cpython-src
RAYLIB_SRC      = $(CACHE)/raylib-src/src
RAYLIB_CFFI_SRC = $(CACHE)/raylib-python-cffi
CFFI_SRC        = $(CACHE)/cffi-src/src/c
LIBFFI_INC      = $(CFFI_SRC)/libffi_arm64/include
BUILD_DIR       = $(CPYTHON_SRC)/builddir/emscripten-browser
BUILD_NATIVE    = $(CPYTHON_SRC)/builddir/build/python.exe
RAYLIB_LIB      = $(RAYLIB_SRC)/libraylib.a
CFFI_C          = $(CACHE)/_raylib_cffi.c
STUBS           = stubs
PRELOAD_RAYLIB  = $(BUILD_DIR)/usr/local/lib/python3.12/raylib
RUNTIME_DIR     = src/rayport/runtime

# --- Local development defaults ---
GAME            ?= examples/breakout
OUTPUT          ?= build/rayport-dev
PORT            ?= 8080

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands
	@awk 'BEGIN { \
		printf "Usage: make <target>\n\nAvailable targets:\n"; \
	} \
	/^[a-zA-Z_-]+:.*##/ { \
		split($$0, parts, /:.*## /); \
		printf "  \033[36m%-20s\033[0m %s\n", parts[1], parts[2]; \
		count++; \
	} \
	END { \
		printf "\n%d available targets.\n", count; \
	}' $(MAKEFILE_LIST)

.PHONY: test
test: ## Run Python tests
	uv run python -m unittest discover -s tests -v

.PHONY: dev
dev: ## Start the example development server (GAME, OUTPUT, and PORT are configurable)
	uv run rayport dev $(GAME) --output $(OUTPUT) --port $(PORT)

# =============================================================================
# Main target: build the complete runtime and copy it into package data
# =============================================================================

.PHONY: runtime
runtime: link ## Build the complete WebAssembly runtime and copy it into the Python package
	mkdir -p $(RUNTIME_DIR)
	cp $(BUILD_DIR)/main.wasm $(BUILD_DIR)/main.js $(BUILD_DIR)/main.data $(RUNTIME_DIR)/

# =============================================================================
# Emscripten SDK download
# =============================================================================

$(EMCC):
	test -d $(EMSDK_PATH) || git clone --depth 1 $(EMSDK_REPO) $(EMSDK_PATH)
	cd $(EMSDK_PATH) && ./emsdk install $(EMSDK_VERSION)
	cd $(EMSDK_PATH) && ./emsdk activate $(EMSDK_VERSION)

# =============================================================================
# Source downloads (skipped when the destination already exists)
# =============================================================================

# CPython source
$(CPYTHON_SRC)/configure:
	mkdir -p $(CACHE)
	git clone --depth 1 --branch $(CPYTHON_VERSION) $(CPYTHON_REPO) $(CPYTHON_SRC)

# raylib source
$(RAYLIB_SRC)/raylib.h:
	mkdir -p $(CACHE)
	git clone --depth 1 --branch $(RAYLIB_VERSION) $(RAYLIB_REPO) $(CACHE)/raylib-src

# raylib-python-cffi source
$(RAYLIB_CFFI_SRC)/raylib/__init__.py:
	mkdir -p $(CACHE)
	git clone --depth 1 $(RAYLIB_CFFI_REPO) $(RAYLIB_CFFI_SRC)

# cffi source (download and extract the sdist through pip)
$(CFFI_SRC)/_cffi_backend.c:
	mkdir -p $(CACHE)/cffi-download
	pip3 download cffi --no-binary :all: -d $(CACHE)/cffi-download
	cd $(CACHE) && tar xzf cffi-download/cffi-*.tar.gz && mv cffi-[0-9]*/ cffi-src

# =============================================================================
# Build targets
# =============================================================================

# Build native Python as a prerequisite for WebAssembly cross-compilation
$(BUILD_NATIVE): $(CPYTHON_SRC)/configure
	cd $(CPYTHON_SRC) && python3 Tools/wasm/wasm_build.py build

# Cross-compile the initial CPython WebAssembly runtime without raylib
$(BUILD_DIR)/python.wasm: $(BUILD_NATIVE) | $(EMCC)
	cd $(CPYTHON_SRC) && python3 Tools/wasm/wasm_build.py emscripten-browser

# Compile the Web version of raylib with -fPIC
$(RAYLIB_LIB): $(RAYLIB_SRC)/raylib.h | $(EMCC)
	cd $(RAYLIB_SRC) && make PLATFORM=PLATFORM_WEB -B \
	  "CFLAGS=-Wall -D_GNU_SOURCE -DPLATFORM_WEB -DGRAPHICS_API_OPENGL_ES2 -Wno-missing-braces -Werror=pointer-arith -fno-strict-aliasing -std=gnu99 -Os -fPIC"

# Generate the CFFI C bindings
$(CFFI_C): $(RAYLIB_SRC)/raylib.h $(RAYLIB_CFFI_SRC)/raylib/__init__.py
	uv run python $(STUBS)/gen_cffi.py

# Compile the _cffi_backend module
$(BUILD_DIR)/Modules/_cffi_backend.o: $(CFFI_SRC)/_cffi_backend.c $(BUILD_DIR)/python.wasm
	$(EMCC) -c -O3 \
	  -I$(CPYTHON_SRC)/Include -I$(CPYTHON_SRC)/Include/internal \
	  -I$(BUILD_DIR) -I$(BUILD_DIR)/Include \
	  -I$(CFFI_SRC) -I$(LIBFFI_INC) \
	  -DFFI_BUILDING -D_CFFI_NO_LIMITED_API \
	  -o $@ $(CFFI_SRC)/_cffi_backend.c

# Compile the raylib CFFI bindings
$(BUILD_DIR)/Modules/_raylib_cffi.o: $(CFFI_C) $(BUILD_DIR)/python.wasm
	$(EMCC) -c -O3 \
	  -I$(CPYTHON_SRC)/Include -I$(CPYTHON_SRC)/Include/internal \
	  -I$(BUILD_DIR) -I$(BUILD_DIR)/Include \
	  -I$(RAYLIB_SRC) \
	  -o $@ $(CFFI_C)

# Compile the libffi stubs
$(CACHE)/ffi_type_stubs.o: $(STUBS)/ffi_type_stubs.c $(CFFI_SRC)/_cffi_backend.c | $(EMCC)
	$(EMCC) -c -O3 -I$(LIBFFI_INC) -o $@ $(STUBS)/ffi_type_stubs.c

# Compile the Web stubs
$(CACHE)/web_stubs.o: $(STUBS)/web_stubs.c $(RAYLIB_SRC)/raylib.h | $(EMCC)
	$(EMCC) -c -O3 -I$(RAYLIB_SRC) -o $@ $(STUBS)/web_stubs.c

# =============================================================================
# Patch config.c to register _cffi_backend and _raylib_cffi as built-in modules
# =============================================================================

.PHONY: patch-config
patch-config: $(BUILD_DIR)/python.wasm ## Patch config.c to register the built-in CFFI modules
	@if grep -q '_raylib_cffi' $(BUILD_DIR)/Modules/config.c; then \
	  echo "config.c already patched, skipping"; \
	else \
	  sed -i '' 's|/\* -- ADDMODULE MARKER 1 -- \*/|extern PyObject* PyInit__cffi_backend(void); extern PyObject* PyInit__raylib_cffi(void); /* -- ADDMODULE MARKER 1 -- */|' $(BUILD_DIR)/Modules/config.c; \
	  sed -i '' 's|/\* Sentinel \*/|{"_cffi_backend", PyInit__cffi_backend}, {"_raylib_cffi", PyInit__raylib_cffi}, /* Sentinel */|' $(BUILD_DIR)/Modules/config.c; \
	  cd $(BUILD_DIR) && $(abspath $(EMCC)) -c -O3 -fvisibility=hidden \
	    -I$(abspath $(CPYTHON_SRC))/Include/internal \
	    -IObjects -IInclude -IPython -I. -I$(abspath $(CPYTHON_SRC))/Include \
	    -fPIC -DPy_BUILD_CORE \
	    -o Modules/config.o Modules/config.c && \
	  $(abspath $(EMAR)) r libpython3.12.a Modules/config.o; \
	fi

# =============================================================================
# Install the raylib Python package into the preload directory
# =============================================================================

# __init__.py wraps the built-in _raylib_cffi module as the raylib package
define RAYLIB_INIT_PY
import sys
import _raylib_cffi

sys.modules['raylib._raylib_cffi'] = _raylib_cffi
ffi = _raylib_cffi.ffi
rl = _raylib_cffi.lib

for _name in dir(_raylib_cffi.lib):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_raylib_cffi.lib, _name)

from raylib.colors import *
from raylib.defines import *
endef
export RAYLIB_INIT_PY

.PHONY: install-raylib-py
install-raylib-py: $(BUILD_DIR)/python.wasm $(RAYLIB_CFFI_SRC)/raylib/__init__.py ## Install the raylib Python package into the preload directory
	mkdir -p $(PRELOAD_RAYLIB)
	cp $(RAYLIB_CFFI_SRC)/raylib/colors.py \
	   $(RAYLIB_CFFI_SRC)/raylib/defines.py \
	   $(RAYLIB_CFFI_SRC)/raylib/enums.py \
	   $(RAYLIB_CFFI_SRC)/raylib/version.py \
	   $(PRELOAD_RAYLIB)/
	printf '%s\n' "$$RAYLIB_INIT_PY" > $(PRELOAD_RAYLIB)/__init__.py
	cp $(STUBS)/launcher.py $(BUILD_DIR)/usr/local/lib/python3.12/launcher.py
	mkdir -p $(BUILD_DIR)/usr/local/game

# =============================================================================
# Final link: produce python.wasm with raylib
# =============================================================================

.PHONY: link
link: patch-config install-raylib-py $(BUILD_DIR)/Modules/_cffi_backend.o $(BUILD_DIR)/Modules/_raylib_cffi.o $(CACHE)/ffi_type_stubs.o $(CACHE)/web_stubs.o $(RAYLIB_LIB) ## Link the final python.wasm with raylib
	$(EMAR) r $(BUILD_DIR)/libpython3.12.a \
	  $(BUILD_DIR)/Modules/_cffi_backend.o \
	  $(BUILD_DIR)/Modules/_raylib_cffi.o
	cd $(BUILD_DIR) && $(abspath $(EMCC)) -sUSE_GLFW=3 -sASYNCIFY -sASYNCIFY_STACK_SIZE=65536 -sALLOW_MEMORY_GROWTH -sTOTAL_MEMORY=20971520 -sWASM_BIGINT \
	  -sFORCE_FILESYSTEM -lidbfs.js -lnodefs.js -lproxyfs.js -lworkerfs.js \
	  --preload-file=./usr/local -O2 -g0 \
	  -o main.js \
	  Programs/python.o \
	  libpython3.12.a \
	  $(realpath $(RAYLIB_LIB)) \
	  $(realpath $(CACHE)/web_stubs.o) \
	  $(realpath $(CACHE)/ffi_type_stubs.o) \
	  Modules/_decimal/libmpdec/libmpdec.a \
	  -sUSE_ZLIB -sUSE_BZIP2 \
	  Modules/_hacl/libHacl_Hash_SHA2.a \
	  Modules/expat/libexpat.a \
	  -sUSE_SQLITE3 \
	  -lm -ldl -lpthread

# =============================================================================
# Cleanup
# =============================================================================

.PHONY: clean
clean: ## Delete the .cache build directory
	rm -rf $(CACHE)

.PHONY: clean-runtime
clean-runtime: ## Delete runtime artifacts from the Python package
	rm -f $(RUNTIME_DIR)/main.wasm $(RUNTIME_DIR)/main.js $(RUNTIME_DIR)/main.data
