import argparse
import json
import os
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

import uvicorn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local Aziro L&D UI and API servers."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to serve the UI (default: 8000 or $PORT).",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=int(os.environ.get("API_PORT", "8011")),
        help="Port to serve the backend API (default: 8011 or $API_PORT).",
    )
    return parser.parse_args()


def api_health_url(api_port: int) -> str:
    return f"http://127.0.0.1:{api_port}/api/health"


def is_api_healthy(api_port: int) -> bool:
    try:
        with urlopen(api_health_url(api_port), timeout=1.5) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("service") == "Aziro L&D Assessment API"
    except (OSError, URLError, TimeoutError, json.JSONDecodeError):
        return False


def wait_for_api(api_port: int, timeout_seconds: float = 12.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if is_api_healthy(api_port):
            return True
        time.sleep(0.25)
    return False


def start_api_server(api_port: int) -> tuple[uvicorn.Server | None, Thread | None]:
    if is_api_healthy(api_port):
        print(f"API server already running: http://127.0.0.1:{api_port}/")
        return None, None

    config = uvicorn.Config(
        "apps.backend.api:app",
        host="127.0.0.1",
        port=api_port,
        log_level="warning",
        reload=False,
    )
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, name="aziro-api-server", daemon=True)
    thread.start()

    if not wait_for_api(api_port):
        server.should_exit = True
        thread.join(timeout=5)
        raise SystemExit(
            f"Failed to start the API server on port {api_port}. "
            "Install dependencies from requirements.txt and try again."
        )

    print(f"API server started: http://127.0.0.1:{api_port}/")
    return server, thread


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    ui_dir = repo_root / "apps" / "frontend" / "dashboard"

    if not ui_dir.exists():
        raise SystemExit(
            f"UI directory not found: {ui_dir}\n"
            "Expected the UI at apps/frontend/dashboard."
        )

    route_map = {
        "/": "/pages/login.html",
        "/login.html": "/pages/login.html",
        "/dashboard.html": "/pages/dashboard.html",
        "/dahsboard.html": "/pages/dahsboard.html",
        "/create_test.html": "/pages/create_test.html",
        "/review_test.html": "/pages/review_test.html",
        "/take_test.html": "/pages/take_test.html",
        "/generated_tests.html": "/pages/generated_tests.html",
        "/evaluation.html": "/pages/evaluation.html",
        "/reports.html": "/pages/reports.html",
    }
    favicon_path = "/assets/images/logo.avif"
    api_server = None
    api_thread = None

    class RootRedirectHandler(SimpleHTTPRequestHandler):
        def end_headers(self):  # noqa: N802 - match base class signature
            # Disable browser caching in local dev to prevent stale UI assets.
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()

        def do_GET(self):  # noqa: N802 - match base class signature
            parts = urlsplit(self.path)
            new_path = route_map.get(parts.path)
            if new_path is not None:
                self.path = urlunsplit(("", "", new_path, parts.query, parts.fragment))
            elif parts.path == "/favicon.ico":
                if (ui_dir / favicon_path.lstrip("/")).exists():
                    self.path = favicon_path
                else:
                    self.send_response(204)
                    self.end_headers()
                    return
            return super().do_GET()

    api_server, api_thread = start_api_server(args.api_port)

    handler = partial(RootRedirectHandler, directory=str(ui_dir))
    server_address = ("0.0.0.0", args.port)

    try:
        httpd = ThreadingHTTPServer(server_address, handler)
    except OSError as exc:
        raise SystemExit(
            f"Failed to start server on port {args.port}: {exc}"
        ) from exc

    print("UI server started.")
    print(f"Open: http://localhost:{args.port}/")
    print(f"API health: {api_health_url(args.api_port)}")
    print("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        if api_server is not None and api_thread is not None:
            api_server.should_exit = True
            api_thread.join(timeout=5)
        print("Server stopped.")


if __name__ == "__main__":
    main()
