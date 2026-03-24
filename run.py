import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local Aziro L&D UI server."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to serve the UI (default: 8000 or $PORT).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    ui_dir = repo_root / "apps" / "frontend" / "dashboard"

    if not ui_dir.exists():
        raise SystemExit(
            f"UI directory not found: {ui_dir}\n"
            "Expected the UI at apps/frontend/dashboard."
        )

    class RootRedirectHandler(SimpleHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - match base class signature
            if self.path in ("", "/"):
                self.path = "/pages/login.html"
            return super().do_GET()

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
    print("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    main()
