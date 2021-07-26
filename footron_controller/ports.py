from __future__ import annotations

# TODO: Determine if this is a bad port to start with
from typing import Optional

START_PORT = 8080

_port_manager: Optional[PortManager] = None


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
        self._bound_ports.remove(port)


def get_port_manager():
    global _port_manager
    if _port_manager is None:
        _port_manager = PortManager()

    return _port_manager
