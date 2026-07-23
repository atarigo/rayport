from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

from playwright.sync_api import Page, sync_playwright


class SmokeHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
    }

    def end_headers(self) -> None:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def save_screenshot(page: Page, path: Path) -> None:
    try:
        page.screenshot(path=path, full_page=True)
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()

    output = args.output.resolve()
    artifacts = args.artifacts.resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "main.wasm", "main.js", "main.data", "game.tar.gz"):
        if not (output / filename).is_file():
            raise FileNotFoundError(f"Missing browser build file: {filename}")

    handler = partial(SmokeHandler, directory=str(output))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"

    failures: list[str] = []
    console_messages: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--enable-unsafe-swiftshader"],
            )
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()

            def record_console(message: object) -> None:
                entry = f"console.{message.type}: {message.text}"
                console_messages.append(entry)
                if message.type == "error":
                    failures.append(entry)

            page.on("console", record_console)
            page.on("pageerror", lambda error: failures.append(f"pageerror: {error}"))
            page.on(
                "requestfailed",
                lambda request: failures.append(
                    f"request failed: {request.method} {request.url}: {request.failure}"
                ),
            )
            page.on(
                "response",
                lambda response: failures.append(
                    f"HTTP {response.status}: {response.url}"
                )
                if response.status >= 400
                else None,
            )

            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                if response is None or not response.ok:
                    raise AssertionError(f"Page request failed: {response}")
                page.wait_for_function(
                    """() => {
                        const canvas = document.getElementById("canvas");
                        return canvas
                            && getComputedStyle(canvas).display !== "none"
                            && canvas.width === 800
                            && canvas.height === 600
                            && typeof Module !== "undefined"
                            && Module.calledRun === true
                            && typeof GLFW !== "undefined"
                            && GLFW.active
                            && GLFW.active.width === 800
                            && GLFW.active.height === 600;
                    }""",
                    timeout=60_000,
                )
                page.wait_for_function(
                    """() => {
                        const canvas = document.getElementById("canvas");
                        const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
                        if (!gl) return false;
                        const pixel = new Uint8Array(4);
                        gl.readPixels(50, 540, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
                        window.__rayportSmokePixel = Array.from(pixel);
                        return pixel[0] > 100 && pixel[1] < 100 && pixel[2] < 100;
                    }""",
                    timeout=10_000,
                )
                page.wait_for_timeout(1_000)
                save_screenshot(page, artifacts / "browser-smoke.png")
                if failures:
                    raise AssertionError("\n".join(failures))
                pixel = page.evaluate("() => window.__rayportSmokePixel")
                print(
                    "Chromium loaded WebAssembly and rendered Breakout at 800x600 "
                    f"(brick pixel {pixel})."
                )
            except Exception:
                save_screenshot(page, artifacts / "browser-smoke-failure.png")
                raise
            finally:
                (artifacts / "browser-console.log").write_text(
                    "\n".join(console_messages) + ("\n" if console_messages else "")
                )
                context.tracing.stop(path=artifacts / "browser-smoke-trace.zip")
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
