import flet as ft
from client import ChatClient
from datetime import datetime
import logging
import asyncio
import os 
import base64
import webbrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = ChatClient("127.0.0.1", 8888)

class UserList(ft.UserControl):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.user_list = ft.ListView(expand=True, spacing=10, padding=20)

    def did_mount(self):
        self.load_users()

    def load_users(self):
        response = client.list_users()
        if response['status'] == 'OK':
            self.user_list.controls.clear()
            for user in response['users']:
                if user != client.username:
                    self.user_list.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.PERSON),
                            title=ft.Text(f"{user}"),
                            on_click=lambda e, user=user: self.navigate_to_chat_room(user),
                        )
                    )
            self.user_list.update()

    def navigate_to_chat_room(self, chat_id):
        self.page.go(f'/chat_room/{chat_id}')

    def build(self):
        return ft.View(
            route="/user_list",
            controls=[
                ft.Row([ft.Text("Private Chat", size=24, weight=ft.FontWeight.BOLD)]),
                self.user_list,
                ft.TextButton(text="Back", on_click=lambda _: self.page.go('/chat_type'))
            ]
        )

class GroupList(ft.UserControl):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.group_list = ft.ListView(expand=True, spacing=10, padding=20)

    def did_mount(self):
        self.load_groups()

    def load_groups(self):
        response = client.list_groups()
        if response['status'] == 'OK':
            self.group_list.controls.clear()
            for group in response['groups']:
                self.group_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.GROUP),
                        title=ft.Text(f"{group}"),
                        on_click=lambda e, group=group: self.navigate_to_chat_room_group(group),
                    )
                )
            self.group_list.update()

    def navigate_to_chat_room_group(self, group_id):
        self.page.go(f'/chat_room_group/{group_id}')

    def build(self):
        return ft.View(
            route="/group_list",
            controls=[
                ft.Row([ft.Text("Group Chat", size=24, weight=ft.FontWeight.BOLD)]),
                self.group_list,
                ft.TextButton(text="Back", on_click=lambda _: self.page.go('/chat_type'))
            ]
        )

def chat_room_page(page, chat_id):
    chat_list = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    chat_message = ft.TextField(label="Message", expand=1, on_submit=lambda e: send_message())
    send_button = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=lambda e: send_message())
    send_realm_button = ft.IconButton(icon=ft.icons.SEND_OUTLINED, on_click=lambda e: send_realm_message())
    file_picker = ft.FilePicker(on_result=lambda e: send_file(e))
    file_button = ft.IconButton(icon=ft.icons.ATTACH_FILE, on_click=lambda e: file_picker.pick_files())
    back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/user_list'))

    page.overlay.append(file_picker)

    def send_message():
        if chat_message.value:
            response = client.send_message(chat_id, chat_message.value)
            add_message_to_chat_list("You", chat_message.value, datetime.now().isoformat(), is_sender=True)
            chat_message.value = ""
            chat_message.update()
            chat_list.update()
            logging.info(f"SEND MESSAGE response: {response}")
    
    def send_realm_message():
        if chat_message.value:
            response = client.send_realm_message(chat_id, chat_message.value)
            add_message_to_chat_list("You", chat_message.value, datetime.now().isoformat(), is_sender=True)
            chat_message.value = ""
            chat_message.update()
            chat_list.update()
            logging.info(f"SEND REALM MESSAGE response: {response}")

    def send_file(file_event):
        if file_event.files:
            file_path = file_event.files[0].path
            response = client.send_file(chat_id, file_path)
            file_name = file_event.files[0].name
            add_message_to_chat_list("You", f"Sent file: {file_name}", datetime.now().isoformat(), is_sender=True)
            chat_list.update()
            logging.info(f"SEND FILE response: {response}")

    def refresh_inbox(e=None):
        inbox = client.get_inbox()
        if inbox['status'] == 'OK':
            messages = inbox['messages']
            chat_list.controls.clear()
            for msg in messages:
                if msg['msg_to'] == chat_id or msg['msg_from'] == chat_id:
                    is_sender = (msg['msg_from'] == client.username)
                    if 'file' in msg:
                        add_message_to_chat_list(msg['msg_from'], f"Received file: {msg['file']}", msg['timestamp'], is_sender)
                    else:
                        add_message_to_chat_list(msg['msg_from'], msg['msg'], msg['timestamp'], is_sender)
            chat_list.update()
            logging.info(f"REFRESH INBOX response: {inbox}")

    def add_message_to_chat_list(sender, message, timestamp, is_sender):
        timestamp_dt = datetime.fromisoformat(timestamp)
        if timestamp_dt.date() == datetime.today().date():
            formatted_time = timestamp_dt.strftime('%H:%M:%S')
        else:
            formatted_time = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')

        bubble_color = ft.colors.GREEN if is_sender else ft.colors.GREY
        text_color = ft.colors.WHITE if is_sender else ft.colors.BLACK
        alignment = ft.alignment.center_right if is_sender else ft.alignment.center_left

        if "Received file:" in message:
            file_name = message.split("Received file: ")[1]
            file_url = f"http://localhost:8000/{file_name}"
            chat_bubble = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"{sender} sent a file:"),
                        ft.TextButton(text=file_name, on_click=lambda e: webbrowser.open(file_url)),
                    ],
                    spacing=5,
                ),
                bgcolor=bubble_color,
                border_radius=10,
                padding=10,
                alignment=alignment
            )
        else:
            chat_bubble = ft.Container(
                content=ft.Text(message, color=text_color),
                bgcolor=bubble_color,
                border_radius=10,
                padding=10,
                alignment=alignment
            )

        timestamp_text = ft.Text(formatted_time, size=10, color=ft.colors.GREY, text_align="right" if is_sender else "left")

        message_with_timestamp = ft.Container(
            content=ft.Column(
                controls=[
                    chat_bubble,
                    timestamp_text
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.END if is_sender else ft.CrossAxisAlignment.START
            ),
            padding=10,
            margin=10,
            alignment=alignment
        )

        chat_list.controls.append(message_with_timestamp)

    async def auto_refresh():
        while True:
            await asyncio.sleep(0.5)
            refresh_inbox()

    refresh_button = ft.ElevatedButton(text="Refresh", on_click=refresh_inbox)
    header = ft.Row([ft.Text(f"Chat Room with {chat_id}", size=24, weight=ft.FontWeight.BOLD), refresh_button])

    view = ft.View(
        route=f"/chat_room/{chat_id}",
        controls=[
            header,
            chat_list,
            ft.Row(controls=[chat_message, send_button, send_realm_button, file_button]),
            back_button
        ]
    )

    page.views.append(view)
    page.update()

    try:
        asyncio.get_running_loop().create_task(auto_refresh())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(auto_refresh())
        loop.run_forever()

    refresh_inbox()

def chat_room_group_page(page, group_id):
    chat_list = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    chat_message = ft.TextField(label="Message", expand=1, on_submit=lambda e: send_group_message())
    send_button = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=lambda e: send_group_message())
    send_realm_button = ft.IconButton(icon=ft.icons.SEND_OUTLINED, on_click=lambda e: send_realm_group_message())
    file_picker = ft.FilePicker(on_result=lambda e: send_group_file(e))
    file_button = ft.IconButton(icon=ft.icons.ATTACH_FILE, on_click=lambda e: file_picker.pick_files())
    back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/group_list'))

    page.overlay.append(file_picker)

    def send_group_message():
        if chat_message.value:
            response = client.send_group_message(group_id, chat_message.value)
            add_message_to_chat_list("You", chat_message.value, datetime.now().isoformat(), is_sender=True)
            chat_message.value = ""
            chat_message.update()
            chat_list.update()
            logging.info(f"SEND GROUP MESSAGE response: {response}")

    def send_realm_group_message():
        if chat_message.value:
            response = client.send_group_realm_message(group_id, chat_message.value)
            add_message_to_chat_list("You", chat_message.value, datetime.now().isoformat(), is_sender=True)
            chat_message.value = ""
            chat_message.update()
            chat_list.update()
            logging.info(f"SEND GROUP MESSAGE response: {response}")

    def send_group_file(file_event):
        if file_event.files:
            file_path = file_event.files[0].path
            response = client.send_group_file(group_id, file_path)
            file_name = file_event.files[0].name
            add_message_to_chat_list("You", f"Sent file: {file_name}", datetime.now().isoformat(), is_sender=True)
            chat_list.update()
            logging.info(f"SEND FILE response: {response}")

    def refresh_inbox(e=None):
        response = client.get_group_inbox(group_id)
        if response['status'] == 'OK':
            messages = response['messages']
            chat_list.controls.clear()
            for msg in messages:
                is_sender = (msg['msg_from'] == client.username)
                if 'file' in msg:
                    add_message_to_chat_list(msg['msg_from'], f"Received file: {msg['file']}", msg['timestamp'], is_sender)
                else:
                    add_message_to_chat_list(msg['msg_from'], msg['msg'], msg['timestamp'], is_sender)
            chat_list.update()
            logging.info(f"REFRESH GROUP INBOX response: {response}")

    def add_message_to_chat_list(sender, message, timestamp, is_sender):
        timestamp_dt = datetime.fromisoformat(timestamp)
        if timestamp_dt.date() == datetime.today().date():
            formatted_time = timestamp_dt.strftime('%H:%M:%S')
        else:
            formatted_time = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')

        bubble_color = ft.colors.GREEN if is_sender else ft.colors.GREY
        text_color = ft.colors.WHITE if is_sender else ft.colors.BLACK
        alignment = ft.alignment.center_right if is_sender else ft.alignment.center_left

        if "Received file:" in message:
            file_name = message.split("Received file: ")[1]
            file_url = f"http://localhost:8000/{file_name}"
            chat_bubble = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"{sender} sent a file:"),
                        ft.TextButton(text=file_name, on_click=lambda e: webbrowser.open(file_url)),
                    ],
                    spacing=5,
                ),
                bgcolor=bubble_color,
                border_radius=10,
                padding=10,
                alignment=alignment
            )
        else:
            chat_bubble = ft.Container(
                content=ft.Text(message, color=text_color),
                bgcolor=bubble_color,
                border_radius=10,
                padding=10,
                alignment=alignment
            )

        timestamp_text = ft.Text(formatted_time, size=10, color=ft.colors.GREY, text_align="right" if is_sender else "left")

        message_with_timestamp = ft.Container(
            content=ft.Column(
                controls=[
                    chat_bubble,
                    timestamp_text
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.END if is_sender else ft.CrossAxisAlignment.START
            ),
            padding=10,
            margin=10,
            alignment=alignment
        )

        chat_list.controls.append(message_with_timestamp)

    async def auto_refresh():
        while True:
            await asyncio.sleep(0.5)
            refresh_inbox()

    refresh_button = ft.ElevatedButton(text="Refresh", on_click=refresh_inbox)
    header = ft.Row([ft.Text(f"Group Chat Room {group_id}", size=24, weight=ft.FontWeight.BOLD), refresh_button])

    view = ft.View(
        route=f"/chat_room_group/{group_id}",
        controls=[
            header,
            chat_list,
            ft.Row(controls=[chat_message, send_button, send_realm_button, file_button]),
            back_button
        ]
    )

    page.views.append(view)
    page.update()

    try:
        asyncio.get_running_loop().create_task(auto_refresh())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(auto_refresh())
        loop.run_forever()

    refresh_inbox()

def main(page: ft.Page):
    page.title = "Chat Application"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def navigate_to(page_name):
        page.go(page_name)

    def navigate_to_chat_room(chat_id):
        page.go(f'/chat_room/{chat_id}')

    def navigate_to_chat_room_group(group_id):
        page.go(f'/chat_room_group/{group_id}')
    
    def register_page():
        username = ft.TextField(label="Username", width=300)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        register_status = ft.Text()

        def register(e):
            response = client.register(username.value, password.value)
            register_status.value = response.get('message', 'Registration failed')
            register_status.update()
            logging.info(f"REGISTER response: {response}")
            if response['status'] == 'OK':
                page.snack_bar = ft.SnackBar(content=ft.Text("Registration successful!"))
                page.snack_bar.open = True
                page.update()
                navigate_to('/login')

        register_button = ft.ElevatedButton(text="Register", on_click=register)
        login_button = ft.TextButton(text="Already registered? Login", on_click=lambda _: navigate_to('/login'))
        back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/login'))

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Register", size=32, weight=ft.FontWeight.BOLD),
                    username,
                    password,
                    register_button,
                    register_status,
                    login_button,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.alignment.center
        )
    
    def login_page():
        username = ft.TextField(label="Username", width=300)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        login_status = ft.Text()

        def login(e):
            response = client.login(username.value, password.value)
            login_status.value = response.get('message', 'Login failed')
            login_status.update()
            logging.info(f"LOGIN response: {response}")
            if response['status'] == 'OK':
                page.snack_bar = ft.SnackBar(content=ft.Text("Login successful!"))
                page.snack_bar.open = True
                page.update()
                navigate_to('/chat_type')

        login_button = ft.ElevatedButton(text="Login", on_click=login)
        register_button = ft.TextButton(text="Register", on_click=lambda _: navigate_to('/register'))
        back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/register'))

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Login", size=32, weight=ft.FontWeight.BOLD),
                    username,
                    password,
                    login_button,
                    login_status,
                    register_button,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.alignment.center
        )
    
    def chat_type_page():
        user_list_button = ft.ElevatedButton(text="Private Chat", on_click=lambda _: navigate_to('/user_list'))
        group_list_button = ft.ElevatedButton(text="Group Chat", on_click=lambda _: navigate_to('/group_list'))
        create_group_button = ft.ElevatedButton(text="Create Group", on_click=lambda _: navigate_to('/group_create'))
        logout_button = ft.ElevatedButton(text="Logout", on_click=lambda _: logout())
        back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/login'))

        def logout():
            client.logout()
            navigate_to('/login')

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Select Chat Type", size=24, weight=ft.FontWeight.BOLD),
                    user_list_button,
                    group_list_button,
                    create_group_button,
                    logout_button,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.alignment.center
        )

    def group_create_page():
        group_name = ft.TextField(label="Group Name", width=300)
        members = ft.TextField(label="Members (comma separated)", width=300)
        status = ft.Text()

        def create_group(e):
            member_list = members.value.split(',')
            response = client.create_group(group_name.value, member_list)
            status.value = response.get('message', 'Group creation failed')
            status.update()
            if response['status'] == 'OK':
                page.snack_bar = ft.SnackBar(content=ft.Text("Group created successfully!"))
                page.snack_bar.open = True
                page.update()

        create_button = ft.ElevatedButton(text="Create Group", on_click=create_group)
        back_button = ft.TextButton(text="Back", on_click=lambda _: navigate_to('/chat_type'))

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Create Group", size=24, weight=ft.FontWeight.BOLD),
                    group_name,
                    members,
                    create_button,
                    status,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.alignment.center
        )

    def route_change(route):
        page.views.clear()
        if route.route == "/register":
            page.views.append(
                ft.View(
                    route="/register",
                    controls=[register_page()],
                )
            )
        elif route.route == "/login":
            page.views.append(
                ft.View(
                    route="/login",
                    controls=[login_page()],
                )
            )
        elif route.route == "/chat_type":
            page.views.append(
                ft.View(
                    route="/chat_type",
                    controls=[chat_type_page()],
                )
            )
        elif route.route == "/user_list":
            user_list_view = UserList(page)
            view = user_list_view.build()
            page.views.append(view)
            page.update()
            user_list_view.did_mount()
        elif route.route == "/group_list":
            group_list_view = GroupList(page)
            view = group_list_view.build()
            page.views.append(view)
            page.update()
            group_list_view.did_mount() 
        elif route.route == "/group_create":
            page.views.append(
                ft.View(
                    route="/group_create",
                    controls=[group_create_page()],
                )
            )
        elif route.route.startswith("/chat_room/"):
            chat_id = route.route.split('/')[-1]
            page.views.append(
                ft.View(
                    route=f"/chat_room/{chat_id}",
                    controls=[chat_room_page(page, chat_id)],
                )
            )
        elif route.route.startswith("/chat_room_group/"):
            group_id = route.route.split('/')[-1]
            page.views.append(
                ft.View(
                    route=f"/chat_room_group/{group_id}",
                    controls=[chat_room_group_page(page, group_id)],
                )
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

if __name__ == "__main__":
    ft.app(target=main)
