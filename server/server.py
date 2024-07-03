from socket import *
import socket
import threading
import json
import logging
from chat import Chat
import os 
import base64
import http.server
import socketserver
from threading import Thread

chatserver = Chat()

PORT = 8000
DIRECTORY = "server/file"

class FileRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_http_server():
    os.makedirs(DIRECTORY, exist_ok=True)
    handler = FileRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    print(f"Serving files at http://localhost:{PORT}")
    httpd.serve_forever()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        while True:
            data = self.connection.recv(2048)
            if data:
                d = data.decode()
                rcv = rcv + d
                if rcv.startswith("sendfile"):
                    logging.warning("data dari client (file): {}".format(rcv))
                    hasil = self.handle_sendfile(rcv)
                    logging.warning("balas ke client (file): {}".format(hasil))
                    hasil = json.dumps(hasil)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                    rcv = ""
                elif rcv.startswith("sendgroupfile"):
                    logging.warning("data dari client (group file): {}".format(rcv))
                    hasil = self.handle_sendgroupfile(rcv)
                    logging.warning("balas ke client (group file): {}".format(hasil))
                    hasil = json.dumps(hasil)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                    rcv = ""
                elif rcv[-2:] == '\r\n':
                    logging.warning("data dari client: {}".format(rcv))
                    hasil = chatserver.proses(rcv)
                    logging.warning("balas ke client: {}".format(hasil))
                    hasil = json.dumps(hasil)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                    rcv = ""
            else:
                break
        self.connection.close()

    def handle_sendfile(self, data):
        try:
            parts = data.split("\r\n\r\n")
            metadata = parts[0].split()
            file_content = base64.b64decode(parts[1])
            sessionid, usernameto, file_name = metadata[1], metadata[2], metadata[3]
            if sessionid not in chatserver.sessions:
                return {'status': 'ERROR', 'message': 'Invalid session'}
            usernamefrom = chatserver.sessions[sessionid]['username']
            return chatserver.send_file(usernamefrom, usernameto, file_name, file_content)
        except Exception as e:
            logging.error(f"Error handling file upload: {str(e)}")
            return {'status': 'ERROR', 'message': 'File upload failed'}

    def handle_sendgroupfile(self, data):
        try:
            parts = data.split("\r\n\r\n")
            metadata = parts[0].split()
            file_content = base64.b64decode(parts[1])
            sessionid, group_name, file_name = metadata[1], metadata[2], metadata[3]
            if sessionid not in chatserver.sessions:
                return {'status': 'ERROR', 'message': 'Invalid session'}
            usernamefrom = chatserver.sessions[sessionid]['username']
            return chatserver.send_group_file(usernamefrom, group_name, file_name, file_content)
        except Exception as e:
            logging.error(f"Error handling group file upload: {str(e)}")
            return {'status': 'ERROR', 'message': 'Group file upload failed'}

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 8889))
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning("connection from {}".format(self.client_address))
            
            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    logging.basicConfig(level=logging.WARNING)
    print("Server is running...")
    svr = Server()
    svr.start()

if __name__ == "__main__":
    Thread(target=start_http_server, daemon=True).start()
    main()
