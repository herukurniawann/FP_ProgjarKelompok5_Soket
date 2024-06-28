import flet as ft
from client import ChatClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = ChatClient("127.0.0.1", 8889)

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
        user_list_button = ft.ElevatedButton(text="User List", on_click=lambda _: navigate_to('/user_list'))
        group_list_button = ft.ElevatedButton(text="Group List", on_click=lambda _: navigate_to('/group_list'))
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

    def user_list_page():
        user_list = ft.ListView(expand=1, spacing=10, padding=20)

        def load_users():
            response = client.list_users()
            if response['status'] == 'OK':
                user_list.controls.clear()
                for user in response['users']:
                    user_list.controls.append(
                        ft.Container(
                            content=ft.TextButton(
                                text=user,
                                on_click=lambda e, user=user: navigate_to_chat_room(user)
                            ),
                            bgcolor=ft.colors.LIGHT_BLUE_100,
                            border_radius=8,
                            padding=10
                        )
                    )
                user_list.update()

        # Load users after view is rendered
        page.views.append(ft.View("/user_list", controls=[
            ft.Column(
                controls=[
                    ft.Text("User List", size=24, weight=ft.FontWeight.BOLD),
                    user_list,
                    ft.TextButton(text="Back", on_click=lambda _: navigate_to('/chat_type'))
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]))
        page.update()
        load_users()

    def group_list_page():
        group_list = ft.ListView(expand=1, spacing=10, padding=20)

        def load_groups():
            response = client.list_groups()
            if response['status'] == 'OK':
                group_list.controls.clear()
                for group in response['groups']:
                    group_list.controls.append(
                        ft.Container(
                            content=ft.TextButton(
                                text=group,
                                on_click=lambda e, group=group: navigate_to_chat_room_group(group)
                            ),
                            bgcolor=ft.colors.LIGHT_GREEN_100,
                            border_radius=8,
                            padding=10
                        )
                    )
                group_list.update()

        # Load groups after view is rendered
        page.views.append(ft.View("/group_list", controls=[
            ft.Column(
                controls=[
                    ft.Text("Group List", size=24, weight=ft.FontWeight.BOLD),
                    group_list,
                    ft.TextButton(text="Back", on_click=lambda _: navigate_to('/chat_type'))
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]))
        page.update()
        load_groups()

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

    def chat_room_page(chat_id):
        chat_list = ft.ListView(expand=1, spacing=10, padding=20)
        chat_message = ft.TextField(label="Message", expand=1)

        def send_message(e):
            if chat_message.value:
                response = client.send_message(chat_id, chat_message.value)
                chat_list.controls.append(ft.Container(
                    content=ft.Text(f"You: {chat_message.value}"),
                    bgcolor=ft.colors.BLUE_GREY_100,
                    border_radius=8,
                    padding=10
                ))
                chat_message.value = ""
                chat_message.update()
                chat_list.update()
                logging.info(f"SEND MESSAGE response: {response}")

        send_button = ft.ElevatedButton(text="Send", on_click=send_message)
        
        def refresh_inbox(e):
            inbox = client.get_inbox()
            if inbox['status'] == 'OK':
                messages = inbox['messages'].get(chat_id, [])
                chat_list.controls.clear()
                for msg in messages:
                    chat_list.controls.append(ft.Container(
                        content=ft.Text(f"{msg['msg_from']}: {msg['msg']}"),
                        bgcolor=ft.colors.BLUE_GREY_50 if msg['msg_from'] != chat_id else ft.colors.BLUE_GREY_100,
                        border_radius=8,
                        padding=10
                    ))
                chat_list.update()
                logging.info(f"REFRESH INBOX response: {inbox}")

        refresh_button = ft.ElevatedButton(text="Refresh", on_click=refresh_inbox)
        back_button = ft.TextButton(text="Back", on_click=lambda _: navigate_to('/user_list'))

        return ft.Column(
            controls=[
                ft.Row([ft.Text(f"Chat Room with {chat_id}", size=24, weight=ft.FontWeight.BOLD), refresh_button]),
                chat_list,
                ft.Row(
                    controls=[chat_message, send_button]
                ),
                back_button
            ]
        )

    def chat_room_group_page(group_id):
        chat_list = ft.ListView(expand=1, spacing=10, padding=20)
        chat_message = ft.TextField(label="Message", expand=1)

        def send_group_message(e):
            if chat_message.value:
                response = client.send_group_message(group_id, chat_message.value)
                chat_list.controls.append(ft.Container(
                    content=ft.Text(f"You: {chat_message.value}"),
                    bgcolor=ft.colors.GREEN_100,
                    border_radius=8,
                    padding=10
                ))
                chat_message.value = ""
                chat_message.update()
                chat_list.update()
                logging.info(f"SEND GROUP MESSAGE response: {response}")

        send_button = ft.ElevatedButton(text="Send", on_click=send_group_message)
        
        def refresh_inbox(e):
            inbox = client.get_inbox()
            if inbox['status'] == 'OK':
                messages = []
                for msg_list in inbox['messages'].values():
                    for msg in msg_list:
                        if msg['msg_to'] == group_id:
                            messages.append(msg)
                chat_list.controls.clear()
                for msg in messages:
                    chat_list.controls.append(ft.Container(
                        content=ft.Text(f"{msg['msg_from']}: {msg['msg']}"),
                        bgcolor=ft.colors.GREEN_50 if msg['msg_from'] != group_id else ft.colors.GREEN_100,
                        border_radius=8,
                        padding=10
                    ))
                chat_list.update()
                logging.info(f"REFRESH GROUP INBOX response: {inbox}")

        refresh_button = ft.ElevatedButton(text="Refresh", on_click=refresh_inbox)
        back_button = ft.TextButton(text="Back", on_click=lambda _: navigate_to('/group_list'))

        return ft.Column(
            controls=[
                ft.Row([ft.Text(f"Group Chat Room {group_id}", size=24, weight=ft.FontWeight.BOLD), refresh_button]),
                chat_list,
                ft.Row(
                    controls=[chat_message, send_button]
                ),
                back_button
            ]
        )

    def route_change(route):
        page.views.clear()
        if route.route == "/register":
            page.views.append(ft.View("/register", controls=[register_page()]))
        elif route.route == "/login":
            page.views.append(ft.View("/login", controls=[login_page()]))
        elif route.route == "/chat_type":
            page.views.append(ft.View("/chat_type", controls=[chat_type_page()]))
        elif route.route == "/user_list":
            user_list_page()
        elif route.route == "/group_list":
            group_list_page()
        elif route.route == "/group_create":
            page.views.append(ft.View("/group_create", controls=[group_create_page()]))
        elif route.route.startswith("/chat_room/"):
            chat_id = route.route.split('/')[-1]
            page.views.append(ft.View(f"/chat_room/{chat_id}", controls=[chat_room_page(chat_id)]))
        elif route.route.startswith("/chat_room_group/"):
            group_id = route.route.split('/')[-1]
            page.views.append(ft.View(f"/chat_room_group/{group_id}", controls=[chat_room_group_page(group_id)]))
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
