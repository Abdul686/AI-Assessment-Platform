import argparse
import json
import os
import socket
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


APP_HEALTHCHECK_TIMEOUT_SECONDS = 1.0
PORT_SCAN_WINDOW = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local Aziro L&D app on a single port."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to serve both UI and API (default: 8000 or $PORT).",
    )
    return parser.parse_args()


def is_app_running(port: int) -> bool:
    try:
        with urlopen(  # noqa: S310 - local loopback health check only
            f"http://127.0.0.1:{port}/api/health",
            timeout=APP_HEALTHCHECK_TIMEOUT_SECONDS,
        ) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, URLError, ValueError, json.JSONDecodeError):
        return False

    return payload.get("service") == "Aziro L&D Assessment API"


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(APP_HEALTHCHECK_TIMEOUT_SECONDS)
        if client.connect_ex(("127.0.0.1", port)) == 0:
            return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("0.0.0.0", port))
            probe.listen(1)
        except OSError:
            return False

    return True


def resolve_port(requested_port: int) -> tuple[int, str | None, bool]:
    if is_port_available(requested_port):
        return requested_port, None, False

    if is_app_running(requested_port):
        message = (
            f"Port {requested_port} is already serving the app. "
            f"Reusing the existing server at http://127.0.0.1:{requested_port}/"
        )
        return requested_port, message, True

    for candidate_port in range(requested_port + 1, requested_port + PORT_SCAN_WINDOW + 1):
        if is_port_available(candidate_port):
            message = (
                f"Port {requested_port} is already in use. "
                f"Starting the app on http://127.0.0.1:{candidate_port}/ instead."
            )
            return candidate_port, message, False

    raise SystemExit(
        f"Port {requested_port} is in use, and no free port was found "
        f"between {requested_port + 1} and {requested_port + PORT_SCAN_WINDOW}."
    )


def build_app(port: int):
    repo_root = Path(__file__).resolve().parent
    ui_dir = repo_root / "apps" / "frontend" / "dashboard"

    if not ui_dir.exists():
        raise SystemExit(
            f"UI directory not found: {ui_dir}\n"
            "Expected the UI at apps/frontend/dashboard."
        )

    os.environ["PORT"] = str(port)
    os.environ.setdefault("PUBLIC_TEST_BASE_URL", f"http://127.0.0.1:{port}/take_test.html")

    from apps.backend import api as backend_api

    app = backend_api.app
    if getattr(app.state, "single_port_ui_attached", False):
        return app

    route_map = {
        "/": "pages/login.html",
        "/index.html": "pages/login.html",
        "/login.html": "pages/login.html",
        "/dashboard.html": "pages/dashboard.html",
        "/dahsboard.html": "pages/dahsboard.html",
        "/create_test.html": "pages/create_test.html",
        "/review_test.html": "pages/review_test.html",
        "/take_test.html": "pages/take_test.html",
        "/generated_tests.html": "pages/generated_tests.html",
        "/evaluation.html": "pages/evaluation.html",
        "/reports.html": "pages/reports.html",
    }

    @app.middleware("http")
    async def disable_ui_caching(request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path == "/" or path.endswith(".html") or path.startswith(("/css/", "/js/", "/assets/", "/pages/")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    def create_page_handler(file_path: Path):
        async def serve_page() -> FileResponse:
            return FileResponse(file_path)

        return serve_page

    for public_path, relative_path in route_map.items():
        app.add_api_route(
            public_path,
            create_page_handler(ui_dir / relative_path),
            methods=["GET"],
            include_in_schema=False,
            name=f"ui_{public_path.strip('/').replace('.', '_') or 'root'}",
        )

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> RedirectResponse:
        return RedirectResponse(url="/assets/images/logo.avif")

    app.mount("/assets", StaticFiles(directory=str(ui_dir / "assets")), name="assets")
    app.mount("/css", StaticFiles(directory=str(ui_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(ui_dir / "js")), name="js")
    app.mount("/pages", StaticFiles(directory=str(ui_dir / "pages")), name="pages")

    app.state.single_port_ui_attached = True
    return app


def main() -> None:
    args = parse_args()
    actual_port, port_message, already_running = resolve_port(args.port)

    if port_message:
        print(port_message)

    if already_running:
        print(f"Open: http://127.0.0.1:{actual_port}/")
        print(f"API health: http://127.0.0.1:{actual_port}/api/health")
        return

    app = build_app(actual_port)

    print("Single-port app server started.")
    print(f"Open: http://127.0.0.1:{actual_port}/")
    print(f"API health: http://127.0.0.1:{actual_port}/api/health")
    print("Press Ctrl+C to stop.")

    uvicorn.run(app, host="0.0.0.0", port=actual_port, log_level="warning")


if __name__ == "__main__":
    main()
