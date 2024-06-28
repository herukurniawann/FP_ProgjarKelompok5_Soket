import sys
import os
import json
import uuid
import logging
from queue import Queue
import threading
import socket

class RealmThreadCommunication(threading.Thread):
    def __init__(self, chats, realm_dest_address, realm_dest_port):
        self.chats = chats
        self.chat = {}
        self.realm_dest_address = realm_dest_address
        self.realm_dest_port = realm_dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.sock.connect((self.realm_dest_address, self.realm_dest_port))
        except Exception as e:
            logging.error(f"Failed to connect to realm: {str(e)}")

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if (data):
                    receivedmsg = "{}{}" . format(receivedmsg, data.decode())
                    if receivedmsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}
    
    def put(self, message):
        dest = message['msg_to']
        try:
            self.chat[dest].put(message)
        except KeyError:
            self.chat[dest]=Queue()
            self.chat[dest].put(message)

class Chat:
    def __init__(self):
        self.sessions={}
        self.users = {}
        self.users['messi']={ 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming' : {}, 'outgoing': {}}
        self.users['henderson']={ 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        self.users['lineker']={ 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.realms = {}
        
    def proses(self, data):
        j = data.split(" ")
        try:
            command = j[0].strip()
            if command == 'auth':
                username = j[1].strip()
                password = j[2].strip()
                logging.info(f"AUTH: auth {username}")
                return self.autentikasi_user(username, password)
            elif command == 'register':
                username = j[1].strip()
                password = j[2].strip()
                logging.info(f"REGISTER: register {username}")
                return self.register_user(username, password)
            elif command == 'send':
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                message = " ".join(j[3:])
                usernamefrom = self.sessions[sessionid]['username']
                logging.info(f"SEND: session {sessionid} send message from {usernamefrom} to {usernameto}")
                return self.send_message(sessionid, usernamefrom, usernameto, message)
            elif command == 'inbox':
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                logging.info(f"INBOX: {sessionid}")
                return self.get_inbox(username)
            elif command == 'sendgroup':
                sessionid = j[1].strip()
                group_name = j[2].strip()
                message = " ".join(j[3:])
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}".format(sessionid, usernamefrom, group_name))
                return self.send_group_message(sessionid, usernamefrom, group_name, message)
            elif command == 'sendrealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                usernameto = j[3].strip()
                message = " ".join(j[4:])
                logging.warning("SENDREALM: session {} send message from {} to {} in realm {}".format(sessionid, self.sessions[sessionid]['username'], usernameto, realm_name))
                return self.send_realm_message(sessionid, usernameto, message)
            elif command == 'sendgrouprealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                group_name = j[3].strip()
                message = " ".join(j[4:])
                logging.warning("SENDGROUPREALM: session {} send message from {} to {} in realm {}".format(sessionid, self.sessions[sessionid]['username'], group_name, realm_name))
                return self.send_group_realm_message(sessionid, group_name, message)
            elif command == 'getrealminbox':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                logging.warning("GETREALMINBOX: {} from realm {}".format(sessionid, realm_name))
                return self.get_realm_inbox(sessionid)
            else:
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
        except KeyError:
            logging.error(f"KeyError: {str(sys.exc_info()[1])}")
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError:
            logging.error(f"IndexError: {str(sys.exc_info()[1])}")
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
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
        self.users[username] = {'nama': username, 'negara': 'Unknown', 'password': password, 'incoming': {}, 'outgoing': {}}
        
        return {'status': 'OK', 'message': 'User Registered Successfully'}

    def get_user(self, username):
        return self.users.get(username, False)

    def send_message(self, sessionid, username_from, username_dest, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if not s_fr or not s_to:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = {'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message}
        try:
            s_fr['outgoing'].setdefault(username_from, Queue()).put(message)
            s_to['incoming'].setdefault(username_from, Queue()).put(message)
        except KeyError:
            s_fr['outgoing'][username_from] = Queue()
            s_to['incoming'][username_from] = Queue()
            s_fr['outgoing'][username_from].put(message)
            s_to['incoming'][username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}

    def get_inbox(self, username):
        s_fr = self.get_user(username)
        incoming = s_fr['incoming']
        msgs = {users: [] for users in incoming}
        for users in incoming:
            while not incoming[users].empty():
                msgs[users].append(s_fr['incoming'][users].get_nowait())
        return {'status': 'OK', 'messages': msgs}

    def send_group_message(self, sessionid, username_from, group_name, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        if not s_fr:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        if group_name == "pemain_bola":
            pemain_bola = ['messi', 'henderson', 'lineker']
            for username_dest in pemain_bola:
                if username_dest != username_from:
                    s_to = self.get_user(username_dest)
                    if not s_to:
                        continue
                    notif = {'msg_from': s_fr['nama'], 'msg_on_group': group_name, 'msg': message}
                    s_fr['outgoing'].setdefault(username_from, Queue()).put(notif)
                    s_to['incoming'].setdefault(username_from, Queue()).put(notif)
        return {'status': 'OK', 'message': 'Message Sent'}

    def send_realm_message(self, sessionid, username_to, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        username_from = self.sessions[sessionid]['username']
        message = {'msg_from': username_from, 'msg_to': username_to, 'msg': message}
        self.realm.put(message)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}

    def send_group_realm_message(self, sessionid, group_name, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        username_from = self.sessions[sessionid]['username']
        if group_name == "pemain_bola":
            pemain_bola = ['messi', 'henderson', 'lineker']
            for username_dest in pemain_bola:
                if username_dest != username_from:
                    notif = {'msg_from': username_from, 'msg_on_group': group_name, 'msg': message}
                    self.realm.put(notif)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def get_realm_inbox(self, sessionid):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        msgs = []
        return {'status': 'OK', 'messages': msgs}