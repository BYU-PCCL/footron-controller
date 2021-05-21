import http.server


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '../apps/clock'

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

