import logging
import subprocess
import urllib.parse
from typing import Dict, Optional

from aiohttp import web
from aiohttp.web_log import AccessLogger
from aiohttp.web_runner import AppRunner, TCPSite

# Probably shouldn't do global state like this
_bound_http_ports = []


class BrowserRunner:
    _url: str
    _port: int
    _browser_process: Optional[subprocess.Popen]
    _runner = Optional[AppRunner]
    _site = Optional[TCPSite]

    def __init__(self, routes: Dict[str, str], url: str):
        self._app = web.Application()
        self._app.add_routes(
            [web.static(url, filepath) for (url, filepath) in routes.items()]
        )
        self._url = url

    def _start_browser(self):
        command = [
            "google-chrome",
            "--kiosk",
            f"--user-data-dir=/tmp/footron-chrome-data/{self.id}",
            # Prevent popup asking to make Chrome your default browser
            "--no-first-run",
            # Allow videos to play without user interaction
            "--autoplay-policy=no-user-gesture-required",
            # Allow cross-origin requests
            "--disable-web-security",
            urllib.parse.urljoin(f"http://localhost:{self._port}", self._url),
        ]
        self._browser_process = subprocess.Popen(command)

    async def _start_static_server(self):
        self._port = _reserve_port(_bound_http_ports, 8080)
        self._runner = AppRunner(
            self._app,
            handle_signals=True,
            access_log_class=AccessLogger,
            access_log_format=AccessLogger.LOG_FORMAT,
            access_log=logging.getLogger("footron.browser_runner"),
        )

        await self._runner.setup()

        self._site = TCPSite(
            self._runner,
            port=self._port,
        )

        await self._site.start()

    def _stop_browser(self):
        self._browser_process.terminate()

    def _stop_static_server(self):
        await self._site.stop()
        await self._runner.cleanup()
        _release_port(self._port, _bound_http_ports)

    async def start(self):
        await self._start_static_server()
        self._start_browser()

    async def stop(self):
        self._stop_static_server()
        self._stop_browser()


def _reserve_port(port_list, default_port):
    # TODO: Consider actually checking if another application has reserved this port
    #  on the OS. Not sure if this would be a problem since we have a lot of control
    #  over the OS
    if not len(port_list):
        port = default_port
    else:
        port = port_list[-1] + 1

    port_list.append(port)
    return port


def _release_port(port, port_list):
    port_list.remove(port)
