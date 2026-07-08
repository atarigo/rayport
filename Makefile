include build.conf

CPYTHON_SRC    = .cache/cpython-src
BUILD_NATIVE   = $(CPYTHON_SRC)/builddir/build/python.exe
BUILD_WASM_DIR = $(CPYTHON_SRC)/builddir/emscripten-browser
BUILD_WASM     = $(BUILD_WASM_DIR)/python.wasm

RUNTIME_FILES  = python.wasm python.js python.data python.html python.worker.js

export EM_CONFIG = $(EMSDK_PATH)/.emscripten
export EMSDK     = $(EMSDK_PATH)
export PATH     := $(EMSDK_PATH):$(EMSDK_PATH)/upstream/emscripten:$(PATH)

.PHONY: runtime clean clean-runtime

runtime: $(BUILD_WASM)
	@mkdir -p runtime
	cp $(addprefix $(BUILD_WASM_DIR)/, $(RUNTIME_FILES)) runtime/

$(BUILD_WASM): $(BUILD_NATIVE)
	cd $(CPYTHON_SRC) && python3 Tools/wasm/wasm_build.py emscripten-browser

$(BUILD_NATIVE): $(CPYTHON_SRC)/configure
	cd $(CPYTHON_SRC) && python3 Tools/wasm/wasm_build.py build

$(CPYTHON_SRC)/configure:
	@mkdir -p .cache
	git clone --depth 1 --branch $(CPYTHON_VERSION) $(CPYTHON_REPO) $(CPYTHON_SRC)

clean:
	rm -rf .cache

clean-runtime:
	rm -f $(addprefix runtime/, $(RUNTIME_FILES))
