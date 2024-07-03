import socket
import json
import logging
import base64
import os 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatClient:
    def __init__(self, target_ip, target_port):
        self.server_address = (target_ip, target_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server_address)
        self.tokenid = ""
        self.username = ""

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            logging.info(f"Sent: {string.strip()}")
            receivemsg = ""
            while True:
                data = self.sock.recv(2048)
                if data:
                    receivemsg = "{}{}".format(receivemsg, data.decode())
                    if receivemsg[-4:] == '\r\n\r\n':
                        logging.info(f"Received: {receivemsg.strip()}")
                        return json.loads(receivemsg)
        except Exception as e:
            logging.error(f"Error in sendstring: {str(e)}")
            self.sock.close()
            return {'status': 'ERROR', 'message': 'Gagal'}

    def login(self, username, password):
        string = f"auth {username} {password} \r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            self.tokenid = result['tokenid']
            self.username = username
        return result

    def register(self, username, password):
        string = f"register {username} {password} \r\n"
        return self.sendstring(string)

    def send_message(self, usernameto, message):
        if not self.tokenid:
            return "Error, not authorized"
        string = f"send {self.tokenid} {usernameto} {message} \r\n"
        return self.sendstring(string)

    def send_file(self, usernameto, file_path):
        if not self.tokenid:
            return "Error, not authorized"
        
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        file_name = os.path.basename(file_path)
        file_content_encoded = base64.b64encode(file_content).decode()
        string = f"sendfile {self.tokenid} {usernameto} {file_name} \r\n\r\n{file_content_encoded}\r\n\r\n"
        
        return self.sendstring(string)

    def get_inbox(self):
        if not self.tokenid:
            return "Error, not authorized"
        string = f"inbox {self.tokenid} \r\n"
        return self.sendstring(string)

    def get_group_inbox(self, group_name):
        if not self.tokenid:
            return "Error, not authorized"
        string = f"groupinbox {self.tokenid} {group_name} \r\n"
        return self.sendstring(string)

    def list_users(self):
        string = "listusers \r\n"
        return self.sendstring(string)

    def create_group(self, group_name, members):
        if not self.tokenid:
            return "Error, not authorized"
        string = f"creategroup {self.tokenid} {group_name} " + " ".join(members) + " \r\n"
        return self.sendstring(string)

    def list_groups(self):
        string = "listgroups \r\n"
        return self.sendstring(string)

    def send_group_message(self, group_name, message):
        if not self.tokenid:
            return "Error, not authorized"
        string = f"sendgroup {self.tokenid} {group_name} {message} \r\n"
        return self.sendstring(string)

    def send_group_file(self, group_name, file_path):
        if not self.tokenid:
            return "Error, not authorized"
        
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        file_name = os.path.basename(file_path)
        file_content_encoded = base64.b64encode(file_content).decode()
        string = f"sendgroupfile {self.tokenid} {group_name} {file_name} \r\n\r\n{file_content_encoded}\r\n\r\n"
        
        return self.sendstring(string)
    
    def send_realm_message(self, username_to, message) :
        if not self.tokenid:
            return "Error, not authorized"
        string = f"sendrealm {username_to} {message} \r\n"
        return self.sendstring(string)
    
    def send_group_realm_message(self, group_name, message):
        if not self.tokenid:
            return "Error, not authorized"
        string = f"sendgrouprealm {group_name} {message}"
        return self.sendstring(string)

    def logout(self):
        self.tokenid = ""
        logging.info("User logged out")
