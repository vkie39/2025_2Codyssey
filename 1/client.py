# client.py
import socket
import threading

ENCODING = 'utf-8'
BUFF_SIZE = 1024

def recv_messages(sock):
    while True:
        try:
            data = sock.recv(BUFF_SIZE)
            if not data:
                break
            print(data.decode(ENCODING), end='')
        except ConnectionAbortedError:
            break

def main():
    host = '127.0.0.1'
    port = 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    thread = threading.Thread(target=recv_messages, args=(sock,), daemon=True)
    thread.start()

    try:
        while True:
            msg = input()
            sock.sendall(msg.encode(ENCODING))
            if msg == '/종료':
                break
    finally:
        sock.close()

if __name__ == '__main__':
    main()
