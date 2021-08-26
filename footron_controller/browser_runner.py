import logging
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, Optional

from aiohttp import web
from aiohttp.web_log import AccessLogger
from aiohttp.web_runner import AppRunner, TCPSite

# Probably shouldn't do global state like this
from .util import mercilessly_kill_process
from .data.ports import get_port_manager
from .constants import BASE_DATA_PATH, BASE_MESSAGING_URL

_bound_http_ports = []

BASE_CHROME_PROFILE_PATH = BASE_DATA_PATH / "base-chrome-profile"
CHROME_PROFILE_PATH = BASE_DATA_PATH / "chrome-data"


class BrowserRunner:
    _id: str
    _url: str
    _port: int
    _app: web.Application
    _routes: Dict[str, str]
    _profile_path: Path
    _browser_process: Optional[subprocess.Popen]
    _runner = Optional[AppRunner]
    _site = Optional[TCPSite]
    _ports = get_port_manager()

    def __init__(self, id: str, routes: Dict[str, str], url: str = "/"):
        self._id = id
        self._app = web.Application(middlewares=[self.static_serve])
        self._routes = {route.rstrip("/"): path for route, path in routes.items()}
        self._url = url
        self._browser_process = None
        self._profile_path = CHROME_PROFILE_PATH / self._id

    def _create_profile_path(self):
        if not CHROME_PROFILE_PATH.exists():
            CHROME_PROFILE_PATH.mkdir(parents=True)

        if not self._profile_path.exists() and BASE_CHROME_PROFILE_PATH.exists():
            shutil.copytree(BASE_CHROME_PROFILE_PATH, self._profile_path)

    def _create_url(self):
        base_url = urllib.parse.urljoin(f"http://localhost:{self._port}", self._url)
        parsed_url = urllib.parse.urlsplit(base_url)
        query_params = urllib.parse.parse_qsl(parsed_url.query)
        query_params.append(
            ("ftMsgUrl", urllib.parse.urljoin(BASE_MESSAGING_URL, self._id))
        )
        query_str = urllib.parse.urlencode(query_params)
        return urllib.parse.urlunsplit(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                query_str,
                parsed_url.fragment,
            )
        )

    def _start_browser(self):
        self._create_profile_path()
        command = [
            "google-chrome",
            "--kiosk",
            f"--user-data-dir={self._profile_path}",
            # Prevent popup asking to make Chrome your default browser
            "--no-first-run",
            # Allow videos to play without user interaction
            "--autoplay-policy=no-user-gesture-required",
            # Allow cross-origin requests
            "--disable-web-security",
            # Try to avoid white flash with dark mode settings
            "--force-dark-mode",
            "--enable-features=WebUIDarkMode",
            self._create_url(),
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

    async def _stop_browser(self):
        if not self._browser_process:
            return

        await mercilessly_kill_process(self._browser_process)

    async def _stop_static_server(self):
        if not self._runner or not self._site:
            return

        try:
            await self._runner.cleanup()
            logging.info("Cleaned up website")
        except RuntimeError as e:
            logging.error("Error while stopping static server:")
            logging.exception(e)
        # TODO: Figure out what we have to do to get aiohttp to let go of its ports
        # self._ports.release_port(self._port)

    async def start(self):
        await self._start_static_server()
        self._start_browser()

    async def stop(self):
        await self._stop_browser()
        await self._stop_static_server()
