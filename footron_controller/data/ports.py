from __future__ import annotations

import logging
from typing import Optional

# TODO: Determine if this is a bad port to start with
import rollbar

START_PORT = 8080

_port_manager: Optional[PortManager] = None

logger = logging.getLogger(__name__)


class PortManager:
    _bound_ports = []

    def reserve_port(self):
        if not len(self._bound_ports):
            port = START_PORT
        else:
            port = self._bound_ports[-1] + 1

        self._bound_ports.append(port)
        return port

    def release_port(self, port):
        try:
            self._bound_ports.remove(port)
        except ValueError:
            message = f"Attempted to release unregistered port {port}"
            logger.warning(message)
            rollbar.report_message(message)


def get_port_manager():
    global _port_manager
    if _port_manager is None:
        _port_manager = PortManager()

    return _port_manager
