import json
import uuid
import logging
from datetime import datetime
import os 
import base64

class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {
            'hisan': {'nama': 'Hisan', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'heru': {'nama': 'Heru', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'daffa': {'nama': 'Daffa', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'baihaqi': {'nama': 'Baihaqi', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'arfi': {'nama': 'Arfi', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'ulya': {'nama': 'Ulya', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
        }
        self.groups = {
            'group1': ['hisan', 'heru', 'daffa'],
            'group2': ['baihaqi', 'arfi', 'ulya'],
        }

    def proses(self, data):
        j = data.split(" ")
        try:
            command = j[0].strip()
            if command == 'auth':
                username = j[1].strip()
                password = j[2].strip()
                return self.autentikasi_user(username, password)
            elif command == 'register':
                username = j[1].strip()
                password = j[2].strip()
                return self.register_user(username, password)
            elif command == 'send':
                sessionid = j[1].strip()
                if sessionid not in self.sessions:
                    return {'status': 'ERROR', 'message': 'Invalid session'}
                usernameto = j[2].strip()
                message = " ".join(j[3:])
                usernamefrom = self.sessions[sessionid]['username']
                return self.send_message(usernamefrom, usernameto, message)
            elif command == 'inbox':
                sessionid = j[1].strip()
                if sessionid not in self.sessions:
                    return {'status': 'ERROR', 'message': 'Invalid session'}
                username = self.sessions[sessionid]['username']
                logging.warning(f"User {username} requested inbox")
                return self.get_inbox(username)
            elif command == 'listusers':
                return self.list_users()
            elif command == 'creategroup':
                sessionid = j[1].strip()
                if sessionid not in self.sessions:
                    return {'status': 'ERROR', 'message': 'Invalid session'}
                group_name = j[2].strip()
                members = j[3:]
                return self.create_group(group_name, members)
            elif command == 'listgroups':
                return self.list_groups()
            elif command == 'sendgroup':
                sessionid = j[1].strip()
                if sessionid not in self.sessions:
                    return {'status': 'ERROR', 'message': 'Invalid session'}
                group_name = j[2].strip()
                message = " ".join(j[3:])
                usernamefrom = self.sessions[sessionid]['username']
                return self.send_group_message(usernamefrom, group_name, message)
            else:
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
        except KeyError as e:
            logging.error(f"KeyError in proses: {str(e)}")
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError as e:
            logging.error(f"IndexError in proses: {str(e)}")
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}
        except Exception as e:
            logging.error(f"Exception in proses: {str(e)}")
            return {'status': 'ERROR', 'message': 'Terjadi kesalahan pada server'}

    def autentikasi_user(self, username, password):
        if username not in self.users:
            return {'status': 'ERROR', 'message': 'User Tidak Ada'}
        if self.users[username]['password'] != password:
            return {'status': 'ERROR', 'message': 'Password Salah'}
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {'username': username, 'userdetail': self.users[username]}
        logging.warning(f"User {username} authenticated with session {tokenid}")
        return {'status': 'OK', 'tokenid': tokenid}

    def register_user(self, username, password):
        if username in self.users:
            return {'status': 'ERROR', 'message': 'User Already Exists'}
        self.users[username] = {'nama': username, 'password': password, 'incoming': {}, 'outgoing': {}}
        logging.warning(f"User {username} registered successfully")
        return {'status': 'OK', 'message': 'User Registered Successfully'}

    def list_users(self):
        return {'status': 'OK', 'users': list(self.users.keys())}

    def create_group(self, group_name, members):
        if group_name in self.groups:
            return {'status': 'ERROR', 'message': 'Group Already Exists'}
        self.groups[group_name] = members
        logging.warning(f"Group {group_name} created with members {members}")
        return {'status': 'OK', 'message': 'Group Created'}

    def list_groups(self):
        return {'status': 'OK', 'groups': list(self.groups.keys())}

    def send_message(self, username_from, username_dest, message):
        if username_from not in self.users or username_dest not in self.users:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        timestamp = datetime.now().isoformat()
        msg = {'msg_from': username_from, 'msg_to': username_dest, 'msg': message, 'timestamp': timestamp}
        if username_dest not in self.users[username_from]['outgoing']:
            self.users[username_from]['outgoing'][username_dest] = []
        if username_from not in self.users[username_dest]['incoming']:
            self.users[username_dest]['incoming'][username_from] = []
        self.users[username_dest]['incoming'][username_from].append(msg)
        self.users[username_from]['outgoing'][username_dest].append(msg)
        logging.warning(f"Sent message from {username_from} to {username_dest}: {msg}")
        logging.warning(f"Current incoming for {username_dest}: {self.users[username_dest]['incoming']}")
        logging.warning(f"Current outgoing for {username_from}: {self.users[username_from]['outgoing']}")
        return {'status': 'OK', 'message': 'Message Sent'}

    def send_file(self, username_from, username_dest, file_name, file_content):
        if username_from not in self.users or username_dest not in self.users:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        
        file_dir = os.path.join(os.path.dirname(__file__), 'file')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        
        file_path = os.path.join(file_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        timestamp = datetime.now().isoformat()
        msg = {'msg_from': username_from, 'msg_to': username_dest, 'file': file_name, 'timestamp': timestamp}
        
        if username_dest not in self.users[username_from]['outgoing']:
            self.users[username_from]['outgoing'][username_dest] = []
        if username_from not in self.users[username_dest]['incoming']:
            self.users[username_dest]['incoming'][username_from] = []
        self.users[username_dest]['incoming'][username_from].append(msg)
        self.users[username_from]['outgoing'][username_dest].append(msg)
        
        logging.warning(f"Sent file from {username_from} to {username_dest}: {msg}")
        logging.warning(f"Current incoming for {username_dest}: {self.users[username_dest]['incoming']}")
        logging.warning(f"Current outgoing for {username_from}: {self.users[username_from]['outgoing']}")
        return {'status': 'OK', 'message': 'File Sent'}

    def get_inbox(self, username):
        incoming = self.users[username]['incoming']
        outgoing = self.users[username]['outgoing']
        all_msgs = []

        for sender, messages in incoming.items():
            all_msgs.extend(messages)
        for receiver, messages in outgoing.items():
            all_msgs.extend(messages)
            
        all_msgs.sort(key=lambda x: x['timestamp'])
        logging.warning(f"Inbox for {username} - All Messages: {all_msgs}")
        return {'status': 'OK', 'messages': all_msgs}
    
        logging.warning(f"Inbox for {username} - All Messages: {all_msgs}")
        return {'status': 'OK', 'messages': all_msgs}

    def send_group_message(self, username_from, group_name, message):
        if group_name not in self.groups:
            return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
        for member in self.groups[group_name]:
            if member != username_from:
                self.send_message(username_from, member, message)
        return {'status': 'OK', 'message': 'Message Sent to Group'}
