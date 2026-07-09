import http.server
import json
import os
import shutil
import threading
import time
import webbrowser
from pathlib import Path

from rayport.packager import pack_game
from rayport.html_generator import generate_html

LIVERELOAD_SCRIPT = """<script>
(function() {
    var v = 0;
    setInterval(function() {
        fetch("/__reload").then(function(r) { return r.json(); }).then(function(data) {
            if (data.v > v) { v = data.v; location.reload(); }
        }).catch(function() {});
    }, 1000);
})();
</script>"""

reload_version = 0


def make_handler(serve_dir):
    class DevHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=serve_dir, **kwargs)

        extensions_map = {
            **http.server.SimpleHTTPRequestHandler.extensions_map,
            ".wasm": "application/wasm",
        }

        def end_headers(self):
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            super().end_headers()

        def do_GET(self):
            if self.path == "/__reload" or self.path.startswith("/__reload?"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"v": reload_version}).encode())
                return

            if self.path == "/" or self.path == "/index.html":
                filepath = Path(self.directory) / "index.html"
                if filepath.exists():
                    content = filepath.read_text()
                    content = content.replace("</body>", LIVERELOAD_SCRIPT + "\n</body>")
                    data = content.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return

            super().do_GET()

        def log_message(self, format, *args):
            if "/__reload" not in str(args[0]):
                super().log_message(format, *args)

    return DevHandler


class FileWatcher:
    def __init__(self, watch_dir, callback, interval=1.0):
        self.watch_dir = Path(watch_dir).resolve()
        self.callback = callback
        self.interval = interval
        self._stop = threading.Event()
        self._mtimes = self._scan()

    def _scan(self):
        mtimes = {}
        for root, dirs, files in os.walk(self.watch_dir):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "venv"}]
            for f in files:
                p = Path(root) / f
                try:
                    mtimes[str(p)] = p.stat().st_mtime
                except OSError:
                    pass
        return mtimes

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        while not self._stop.is_set():
            time.sleep(self.interval)
            new_mtimes = self._scan()
            changed = []
            for path, mtime in new_mtimes.items():
                if path not in self._mtimes or self._mtimes[path] != mtime:
                    changed.append(path)
            for path in self._mtimes:
                if path not in new_mtimes:
                    changed.append(path)
            if changed:
                self._mtimes = new_mtimes
                self.callback(changed)

    def stop(self):
        self._stop.set()


def run_dev(game_dir, output_dir="build", title="rayport game", width=800, height=450, port=8080):
    global reload_version

    game_path = Path(game_dir).resolve()
    output_path = Path(output_dir).resolve()
    runtime_dir = Path(__file__).parent.parent.parent / "runtime"

    print(f"Building from {game_path}...")
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)

    pack_game(str(game_path), str(output_path / "game.tar.gz"))
    generate_html(str(output_path / "index.html"), title=title, width=width, height=height)
    for fname in ["main.wasm", "main.js", "main.data"]:
        src = runtime_dir / fname
        if not src.exists():
            raise FileNotFoundError(f"Runtime file not found: {src}\nRun 'make runtime' first.")
        shutil.copy2(src, output_path / fname)

    print("Build complete.")

    def on_change(changed):
        global reload_version
        rel_paths = [str(Path(p).relative_to(game_path)) for p in changed if str(game_path) in p]
        if rel_paths:
            print(f"Changed: {', '.join(rel_paths[:5])}")
        pack_game(str(game_path), str(output_path / "game.tar.gz"))
        reload_version += 1
        print(f"Repacked. Browser will reload. (v{reload_version})")

    watcher = FileWatcher(str(game_path), on_change)
    watcher.start()
    print(f"Watching {game_path} for changes...")

    url = f"http://localhost:{port}"
    print(f"Serving at {url}")
    webbrowser.open(url)

    handler = make_handler(str(output_path))
    server = http.server.HTTPServer(("", port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dev server.")
        watcher.stop()
        server.shutdown()
