#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
from typing import Dict, Tuple


ENCODING = 'utf-8'
BUFF_SIZE = 1024
HOST = '0.0.0.0'
PORT = 5000


class ChatServer:
    '''멀티스레드 TCP 채팅 서버. 표준 라이브러리만 사용.'''

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.server_sock: socket.socket | None = None
        # 접속 클라이언트 관리: {conn: (addr, nickname)}
        self.clients: Dict[socket.socket, Tuple[Tuple[str, int], str]] = {}
        self.clients_lock = threading.Lock()

    def start(self) -> None:
        '''서버를 시작하고 접속을 수락한다.'''
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 빠른 재시작을 위해 주소 재사용
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()

        print(f'Chat server listening on {self.host}:{self.port}')

        try:
            while True:
                conn, addr = self.server_sock.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True,
                )
                thread.start()
        except KeyboardInterrupt:
            print('\n서버를 종료합니다.')
        finally:
            self._shutdown()

    def _broadcast(self, message: str, exclude: socket.socket | None = None) -> None:
        '''모든 클라이언트에 메시지를 전송한다. 필요한 경우 보낸 사람 제외.'''
        data = (message + '\n').encode(ENCODING, errors='ignore')
        dead: list[socket.socket] = []
        with self.clients_lock:
            for conn in list(self.clients.keys()):
                if exclude is not None and conn is exclude:
                    continue
                try:
                    conn.sendall(data)
                except OSError:
                    dead.append(conn)
            # 전송 실패 소켓 정리
            for d in dead:
                self._remove_client(d)

    def _register_client(self, conn: socket.socket, addr: Tuple[str, int], nickname: str) -> None:
        '''클라이언트를 등록한다.'''
        with self.clients_lock:
            self.clients[conn] = (addr, nickname)

    def _remove_client(self, conn: socket.socket) -> None:
        '''클라이언트 연결을 정리하고 목록에서 제거한다.'''
        with self.clients_lock:
            info = self.clients.pop(conn, None)
        try:
            conn.close()
        except OSError:
            pass
        if info is not None:
            _, nickname = info
            self._broadcast(f'{nickname}님이 퇴장하셨습니다.')

    def _handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        '''개별 클라이언트 스레드 루틴.'''
        try:
            conn.sendall('닉네임을 입력하세요: '.encode(ENCODING))
            raw = conn.recv(BUFF_SIZE)
            if not raw:
                conn.close()
                return

            nickname = raw.decode(ENCODING, errors='ignore').strip()
            if not nickname:
                nickname = f'{addr[0]}:{addr[1]}'

            self._register_client(conn, addr, nickname)
            self._broadcast(f'{nickname}님이 입장하셨습니다.')

            while True:
                data = conn.recv(BUFF_SIZE)
                if not data:
                    break
                message = data.decode(ENCODING, errors='ignore').strip()
                if not message:
                    continue
                if message == '/종료':
                    conn.sendall('연결을 종료합니다.\n'.encode(ENCODING))
                    break
                self._broadcast(f'{nickname}> {message}')
        except ConnectionResetError:
            # 클라이언트가 비정상 종료한 경우
            pass
        finally:
            self._remove_client(conn)

    def _shutdown(self) -> None:
        '''서버 소켓과 모든 클라이언트를 정리한다.'''
        if self.server_sock is not None:
            try:
                self.server_sock.close()
            except OSError:
                pass
        with self.clients_lock:
            conns = list(self.clients.keys())
        for c in conns:
            self._remove_client(c)


def main() -> None:
    server = ChatServer(HOST, PORT)
    server.start()


if __name__ == '__main__':
    main()
