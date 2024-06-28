import json
import uuid
import logging
from queue import Queue

class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {
            'messi': {'nama': 'Lionel Messi', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'henderson': {'nama': 'Jordan Henderson', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}},
            'lineker': {'nama': 'Gary Lineker', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        }
        self.groups = {
            'group1': ['messi', 'henderson', 'lineker']
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
                usernameto = j[2].strip()
                message = " ".join(j[3:])
                usernamefrom = self.sessions[sessionid]['username']
                return self.send_message(usernamefrom, usernameto, message)
            elif command == 'inbox':
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                return self.get_inbox(username)
            elif command == 'listusers':
                return self.list_users()
            elif command == 'creategroup':
                sessionid = j[1].strip()
                group_name = j[2].strip()
                members = j[3:]
                return self.create_group(group_name, members)
            elif command == 'listgroups':
                return self.list_groups()
            elif command == 'sendgroup':
                sessionid = j[1].strip()
                group_name = j[2].strip()
                message = " ".join(j[3:])
                usernamefrom = self.sessions[sessionid]['username']
                return self.send_group_message(usernamefrom, group_name, message)
            else:
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
        except KeyError:
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}
        except Exception as e:
            return {'status': 'ERROR', 'message': 'Terjadi kesalahan pada server'}

    def autentikasi_user(self, username, password):
        if username not in self.users:
            return {'status': 'ERROR', 'message': 'User Tidak Ada'}
        if self.users[username]['password'] != password:
            return {'status': 'ERROR', 'message': 'Password Salah'}
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {'username': username, 'userdetail': self.users[username]}
        return {'status': 'OK', 'tokenid': tokenid}

    def register_user(self, username, password):
        if username in self.users:
            return {'status': 'ERROR', 'message': 'User Already Exists'}
        self.users[username] = {'nama': username, 'password': password, 'incoming': {}, 'outgoing': {}}
        return {'status': 'OK', 'message': 'User Registered Successfully'}

    def list_users(self):
        return {'status': 'OK', 'users': list(self.users.keys())}

    def create_group(self, group_name, members):
        if group_name in self.groups:
            return {'status': 'ERROR', 'message': 'Group Already Exists'}
        self.groups[group_name] = members
        return {'status': 'OK', 'message': 'Group Created'}

    def list_groups(self):
        return {'status': 'OK', 'groups': list(self.groups.keys())}

    def send_message(self, username_from, username_dest, message):
        if username_from not in self.users or username_dest not in self.users:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = {'msg_from': username_from, 'msg_to': username_dest, 'msg': message}
        self.users[username_dest]['incoming'].setdefault(username_from, Queue()).put(message)
        self.users[username_from]['outgoing'].setdefault(username_dest, Queue()).put(message)
        return {'status': 'OK', 'message': 'Message Sent'}

    def get_inbox(self, username):
        incoming = self.users[username]['incoming']
        msgs = {users: [] for users in incoming}
        for users in incoming:
            while not incoming[users].empty():
                msgs[users].append(incoming[users].get_nowait())
        return {'status': 'OK', 'messages': msgs}

    def send_group_message(self, username_from, group_name, message):
        if group_name not in self.groups:
            return {'status': 'ERROR', 'message': 'Group Tidak Ditemukan'}
        for member in self.groups[group_name]:
            if member != username_from:
                self.send_message(username_from, member, message)
        return {'status': 'OK', 'message': 'Message Sent to Group'}
