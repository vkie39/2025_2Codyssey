from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from pathlib import Path

PORT = 8080
INDEX_FILE = 'index.html'

class SpacePirateHandler(BaseHTTPRequestHandler):
    def log_access(self) -> None:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]
        print(f'접속 시간: {now} | IP Address: {client_ip}')

    def send_html(self, content: bytes) -> None:
        self.send_response(200)  # message 생략(ASCII 필요 문제 회피)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        self.log_access()

        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        if self.path in ('/', '/index.html'):
            html_path = Path(INDEX_FILE)
            if not html_path.exists():
                # message=는 ASCII만! 한글은 explain으로
                self.send_error(404, message='Not Found', explain='index.html 파일을 찾을 수 없습니다.')
                return

            content = html_path.read_bytes()
            self.send_html(content)
            return

        # 다른 경로 404
        self.send_error(404, message='Not Found', explain='요청한 경로를 찾을 수 없습니다.')

def run_server() -> None:
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SpacePirateHandler)
    print(f'HTTP 서버 시작: http://localhost:{PORT} (Ctrl+C 종료)')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n서버 종료 요청 수신')
    finally:
        httpd.server_close()
        print('서버가 정상 종료되었습니다.')

if __name__ == '__main__':
    run_server()
