import logging
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, Optional

from aiohttp import web
from aiohttp.web_log import AccessLogger
from aiohttp.web_runner import AppRunner, TCPSite

# Probably shouldn't do global state like this
from .ports import get_port_manager
from .constants import BASE_DATA_PATH

_bound_http_ports = []

CHROME_PROFILE_PATH = BASE_DATA_PATH / "chrome-data"


class BrowserRunner:
    _profile_key: str
    _url: str
    _port: int
    _app: web.Application
    _routes: Dict[str, str]
    _browser_process: Optional[subprocess.Popen]
    _runner = Optional[AppRunner]
    _site = Optional[TCPSite]
    _ports = get_port_manager()

    def __init__(self, profile_key: str, routes: Dict[str, str], url: str = "/"):
        self._profile_key = profile_key
        self._app = web.Application(middlewares=[self.static_serve])
        self._routes = {route.rstrip("/"): path for route, path in routes.items()}
        self._url = url

    @staticmethod
    def _create_profile_path():
        if CHROME_PROFILE_PATH.exists():
            return
        CHROME_PROFILE_PATH.mkdir(parents=True)

    def _start_browser(self):
        self._create_profile_path()
        command = [
            "google-chrome",
            "--kiosk",
            f"--user-data-dir={CHROME_PROFILE_PATH / self._profile_key}",
            # Prevent popup asking to make Chrome your default browser
            "--no-first-run",
            # Allow videos to play without user interaction
            "--autoplay-policy=no-user-gesture-required",
            # Allow cross-origin requests
            "--disable-web-security",
            urllib.parse.urljoin(f"http://localhost:{self._port}", self._url),
        ]
        self._browser_process = subprocess.Popen(command)

    # Based on https://github.com/aio-libs/aiohttp/issues/1220#issuecomment-546572413
    @web.middleware
    async def static_serve(self, request, handler):
        matching_route, root_path = next(
            (route, Path(path))
            for route, path in self._routes.items()
            if request.path.startswith(route)
        )
        relative_file_path = Path(request.path.replace(matching_route, "")).relative_to(
            "/"
        )
        file_path = root_path / relative_file_path
        if not file_path.exists():
            return web.HTTPNotFound()
        if file_path.is_dir():
            file_path /= "index.html"
            if not file_path.exists():
                return web.HTTPNotFound()
        return web.FileResponse(file_path)

    async def _start_static_server(self):
        self._port = self._ports.reserve_port()
        self._runner = AppRunner(
            self._app,
            handle_signals=True,
            access_log_class=AccessLogger,
            access_log_format=AccessLogger.LOG_FORMAT,
            access_log=logging.getLogger(__name__),
        )

        await self._runner.setup()

        self._site = TCPSite(
            self._runner,
            port=self._port,
        )

        await self._site.start()

    def _stop_browser(self):
        if not self._browser_process:
            return

        self._browser_process.terminate()

    async def _stop_static_server(self):
        if not self._runner or not self._site:
            return

        await self._site.stop()
        await self._runner.cleanup()
        self._ports.release_port(self._port)

    async def start(self):
        await self._start_static_server()
        self._start_browser()

    async def stop(self):
        self._stop_browser()
        await self._stop_static_server()
