import zmq


class WmApi:
    def __init__(self):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect("tcp://localhost:5557")

    def set_fullscreen(self, fullscreen: bool):
        self._socket.send_json({"fullscreen": fullscreen}, zmq.NOBLOCK)
