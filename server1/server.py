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

class RealmServerThread(threading.Thread):
    def __init__(self, realm_port, other_realm_address):
        super().__init__()
        self.realm_port = realm_port
        self.other_realm_address = other_realm_address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', realm_port))
        self.sock.listen(1)
        self.connection = None
        self.client_address = None

    def run(self):
        while True:
            self.connection, self.client_address = self.sock.accept()
            try:
                data = self.connection.recv(2048)
                if data:
                    self.handle_realm_message(data.decode())
            finally:
                self.connection.close()

    def handle_realm_message(self, data):
        logging.warning(f"Received realm message: {data}")
        hasil = chatserver.proses(data)
        if self.connection:
            self.connection.sendall(json.dumps(hasil).encode() + b'\r\n\r\n')

    def send_realm_message(self, message):
        try:
            logging.warning(f"Connecting to other realm server at {self.other_realm_address}")
            with socket.create_connection(self.other_realm_address) as sock:
                logging.warning(f"Sending realm message: {message}")
                sock.sendall(message.encode())
                response = sock.recv(2048)
                logging.warning(f"Received response from realm server: {response}")
                return response.decode()
        except Exception as e:
            logging.error(f"Error sending realm message: {str(e)}")
            return None

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
                elif rcv.startswith("sendrealm") or rcv.startswith("sendgrouprealm"):
                    logging.warning("data dari client (realm): {}".format(rcv))
                    hasil = self.handle_realm_message(rcv)
                    logging.warning("balas ke client (realm): {}".format(hasil))
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

    def handle_realm_message(self, data):
        try:
            if data.startswith("sendrealm"):
                parts = data.split(" ")
                sessionid = parts[1].strip()
                usernameto = parts[2].strip()
                message = " ".join(parts[3:])
                
                usernamefrom = chatserver.get_username_from_session(sessionid)
                if usernamefrom:
                    realm_message = f"sendrealm {usernamefrom} {usernameto} {message}"
                    response = realm_server.send_realm_message(realm_message)
                    chatserver.proses(realm_message)
                    return json.loads(response)
                else:
                    return {'status': 'ERROR', 'message': 'Invalid session ID'}
                
            elif data.startswith("sendgrouprealm"):
                parts = data.split(" ")
                sessionid = parts[1].strip()
                group_name = parts[2].strip()
                message = " ".join(parts[3:])
                
                usernamefrom = chatserver.get_username_from_session(sessionid)
                if usernamefrom:
                    realm_message = f"sendgrouprealm {usernamefrom} {group_name} {message}"
                    response = realm_server.send_realm_message(realm_message)
                    chatserver.proses(realm_message)
                    return json.loads(response)
                else:
                    return {'status': 'ERROR', 'message': 'Invalid session ID'}
                
        except Exception as e:
            logging.error(f"Error handling realm message: {str(e)}")
            return {'status': 'ERROR', 'message': 'Realm message failed'}

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
    realm_server = RealmServerThread(8890, ('127.0.0.1', 8891))
    realm_server.start()
    Thread(target=start_http_server, daemon=True).start()
    main()
