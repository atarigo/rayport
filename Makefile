# =============================================================================
# rayport runtime 建置
#
# 產出一個包含 CPython + raylib + CFFI bindings 的 WebAssembly binary。
# 建置流程：clone 原始碼 -> 建置 native Python -> 交叉編譯 wasm ->
#           編譯 raylib -> 產生 CFFI bindings -> 編譯模組 ->
#           修補 config.c -> 安裝 Python 檔案 -> 最終連結 -> 複製到 runtime/
# =============================================================================

# --- 組態（缺少 build.conf 時不報錯）---
-include build.conf

# --- Emscripten 工具路徑 ---
export EM_CONFIG = $(EMSDK_PATH)/.emscripten
export EMSDK     = $(EMSDK_PATH)
export PATH     := $(EMSDK_PATH):$(EMSDK_PATH)/upstream/emscripten:$(PATH)
EMCC             = $(EMSDK_PATH)/upstream/emscripten/emcc
EMAR             = $(EMSDK_PATH)/upstream/emscripten/emar

# --- 目錄與檔案變數 ---
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

.DEFAULT_GOAL := runtime

.PHONY: help
help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# 主要目標：完整建置並將產物複製到 runtime/
# =============================================================================

.PHONY: runtime
runtime: link ## 建置完整 wasm runtime 並複製產物到 runtime/
	mkdir -p runtime
	cp $(BUILD_DIR)/main.wasm $(BUILD_DIR)/main.js $(BUILD_DIR)/main.data runtime/

# =============================================================================
# 原始碼取得（目錄已存在時不重複執行）
# =============================================================================

# CPython 原始碼
$(CPYTHON_SRC)/configure:
	mkdir -p $(CACHE)
	git clone --depth 1 --branch $(CPYTHON_VERSION) $(CPYTHON_REPO) $(CPYTHON_SRC)

# raylib 原始碼
$(RAYLIB_SRC)/raylib.h:
	mkdir -p $(CACHE)
	git clone --depth 1 --branch $(RAYLIB_VERSION) $(RAYLIB_REPO) $(CACHE)/raylib-src

# raylib-python-cffi 原始碼
$(RAYLIB_CFFI_SRC)/raylib/__init__.py:
	mkdir -p $(CACHE)
	git clone --depth 1 $(RAYLIB_CFFI_REPO) $(RAYLIB_CFFI_SRC)

# cffi 原始碼（透過 pip 下載 sdist 後解壓）
$(CFFI_SRC)/_cffi_backend.c:
	mkdir -p $(CACHE)/cffi-download
	pip3 download cffi --no-binary :all: -d $(CACHE)/cffi-download
	cd $(CACHE) && tar xzf cffi-download/cffi-*.tar.gz && mv cffi-[0-9]*/ cffi-src

# =============================================================================
# 建置目標
# =============================================================================

# 建置 native Python（交叉編譯 wasm 前的必要步驟）
$(BUILD_NATIVE): $(CPYTHON_SRC)/configure
	cd $(CPYTHON_SRC) && python3 Tools/wasm/wasm_build.py build

# 交叉編譯 CPython 為 wasm（初始版本，尚未含 raylib）
$(BUILD_DIR)/python.wasm: $(BUILD_NATIVE)
	cd $(CPYTHON_SRC) && python3 Tools/wasm/wasm_build.py emscripten-browser

# 以 -fPIC 編譯 raylib 的 web 版本
$(RAYLIB_LIB): $(RAYLIB_SRC)/raylib.h
	cd $(RAYLIB_SRC) && make PLATFORM=PLATFORM_WEB -B \
	  "CFLAGS=-Wall -D_GNU_SOURCE -DPLATFORM_WEB -DGRAPHICS_API_OPENGL_ES2 -Wno-missing-braces -Werror=pointer-arith -fno-strict-aliasing -std=gnu99 -Os -fPIC"

# 產生 CFFI C bindings
$(CFFI_C): $(RAYLIB_SRC)/raylib.h $(RAYLIB_CFFI_SRC)/raylib/__init__.py
	uv run python $(STUBS)/gen_cffi.py

# 編譯 _cffi_backend 模組
$(BUILD_DIR)/Modules/_cffi_backend.o: $(CFFI_SRC)/_cffi_backend.c $(BUILD_DIR)/python.wasm
	$(EMCC) -c -O3 \
	  -I$(CPYTHON_SRC)/Include -I$(CPYTHON_SRC)/Include/internal \
	  -I$(BUILD_DIR) -I$(BUILD_DIR)/Include \
	  -I$(CFFI_SRC) -I$(LIBFFI_INC) \
	  -DFFI_BUILDING -D_CFFI_NO_LIMITED_API \
	  -o $@ $(CFFI_SRC)/_cffi_backend.c

# 編譯 raylib 的 CFFI bindings
$(BUILD_DIR)/Modules/_raylib_cffi.o: $(CFFI_C) $(BUILD_DIR)/python.wasm
	$(EMCC) -c -O3 \
	  -I$(CPYTHON_SRC)/Include -I$(CPYTHON_SRC)/Include/internal \
	  -I$(BUILD_DIR) -I$(BUILD_DIR)/Include \
	  -I$(RAYLIB_SRC) \
	  -o $@ $(CFFI_C)

# 編譯 libffi stubs
$(CACHE)/ffi_type_stubs.o: $(STUBS)/ffi_type_stubs.c $(CFFI_SRC)/_cffi_backend.c
	$(EMCC) -c -O3 -I$(LIBFFI_INC) -o $@ $(STUBS)/ffi_type_stubs.c

# 編譯 web stubs
$(CACHE)/web_stubs.o: $(STUBS)/web_stubs.c $(RAYLIB_SRC)/raylib.h
	$(EMCC) -c -O3 -I$(RAYLIB_SRC) -o $@ $(STUBS)/web_stubs.c

# =============================================================================
# 修補 config.c：把 _cffi_backend 與 _raylib_cffi 註冊為內建模組
# =============================================================================

.PHONY: patch-config
patch-config: $(BUILD_DIR)/python.wasm ## 修補 config.c 註冊 CFFI 內建模組
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
# 安裝 raylib Python package 到 preload 目錄
# =============================================================================

# __init__.py 內容：把內建的 _raylib_cffi 模組包裝成 raylib package
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
install-raylib-py: $(BUILD_DIR)/python.wasm $(RAYLIB_CFFI_SRC)/raylib/__init__.py ## 安裝 raylib Python package 到 preload 目錄
	mkdir -p $(PRELOAD_RAYLIB)
	cp $(RAYLIB_CFFI_SRC)/raylib/colors.py \
	   $(RAYLIB_CFFI_SRC)/raylib/defines.py \
	   $(RAYLIB_CFFI_SRC)/raylib/enums.py \
	   $(RAYLIB_CFFI_SRC)/raylib/version.py \
	   $(PRELOAD_RAYLIB)/
	printf '%s\n' "$$RAYLIB_INIT_PY" > $(PRELOAD_RAYLIB)/__init__.py

# =============================================================================
# 最終連結：產生含 raylib 的 python.wasm
# =============================================================================

.PHONY: link
link: patch-config install-raylib-py $(BUILD_DIR)/Modules/_cffi_backend.o $(BUILD_DIR)/Modules/_raylib_cffi.o $(CACHE)/ffi_type_stubs.o $(CACHE)/web_stubs.o $(RAYLIB_LIB) ## 連結出含 raylib 的最終 python.wasm
	$(EMAR) r $(BUILD_DIR)/libpython3.12.a \
	  $(BUILD_DIR)/Modules/_cffi_backend.o \
	  $(BUILD_DIR)/Modules/_raylib_cffi.o
	cd $(BUILD_DIR) && $(abspath $(EMCC)) -sUSE_GLFW=3 -sALLOW_MEMORY_GROWTH -sTOTAL_MEMORY=20971520 -sWASM_BIGINT \
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
# 清理
# =============================================================================

.PHONY: clean
clean: ## 刪除 .cache 建置快取
	rm -rf $(CACHE)

.PHONY: clean-runtime
clean-runtime: ## 刪除 runtime/ 內的建置產物
	rm -f runtime/main.wasm runtime/main.js runtime/main.data
