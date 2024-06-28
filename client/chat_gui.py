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
        group_button = ft.ElevatedButton(text="Group Chat", on_click=lambda _: navigate_to('/chat_list/group'))
        private_button = ft.ElevatedButton(text="Private Chat", on_click=lambda _: navigate_to('/chat_list/private'))
        logout_button = ft.ElevatedButton(text="Logout", on_click=lambda _: logout())
        back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/login'))

        def logout():
            client.logout()
            navigate_to('/login')

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Select Chat Type", size=24, weight=ft.FontWeight.BOLD),
                    group_button,
                    private_button,
                    logout_button,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.alignment.center
        )

    def chat_list_page(chat_type):
        chat_list = ft.ListView(expand=1, spacing=10, padding=20)
        
        chats = client.get_inbox(chat_type)
        
        for chat in chats:
            chat_list.controls.append(
                ft.Container(
                    content=ft.TextButton(
                        text=chat['name'],
                        on_click=lambda _, c=chat: navigate_to(f'/chat_room/{c["id"]}')
                    ),
                    bgcolor=ft.colors.BLUE_GREY_100,
                    border_radius=8,
                    padding=10
                )
            )
        
        back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/chat_type'))

        return ft.Column(
            controls=[
                ft.Text(f"Chat List ({chat_type})", size=24, weight=ft.FontWeight.BOLD),
                chat_list,
                back_button
            ]
        )

    def chat_room_page(chat_id):
        chat_list = ft.ListView(expand=1, spacing=10, padding=20)
        chat_message = ft.TextField(label="Message", expand=1)

        def send_message(e):
            if chat_message.value:
                response = client.send_message(chat_id, chat_message.value)
                chat_list.controls.append(ft.Text(f"You: {chat_message.value}"))
                chat_message.value = ""
                chat_message.update()
                chat_list.update()
                logging.info(f"SEND MESSAGE response: {response}")

        send_button = ft.ElevatedButton(text="Send", on_click=send_message)
        
        def refresh_inbox(e):
            inbox = client.get_inbox(chat_id)
            if inbox['status'] == 'OK':
                messages = inbox['messages']
                for msg in messages:
                    chat_list.controls.append(ft.Text(f"{msg['sender']}: {msg['content']}"))
                chat_list.update()
                logging.info(f"REFRESH INBOX response: {inbox}")

        refresh_button = ft.ElevatedButton(text="Refresh", on_click=refresh_inbox)
        back_button = ft.TextButton(text="Back", on_click=lambda _: page.go('/chat_list/group'))

        return ft.Column(
            controls=[
                ft.Row([ft.Text("Chat Room", size=24, weight=ft.FontWeight.BOLD), refresh_button]),
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
        elif route.route.startswith("/chat_list/"):
            chat_type = route.route.split('/')[-1]
            page.views.append(ft.View(f"/chat_list/{chat_type}", controls=[chat_list_page(chat_type)]))
        elif route.route.startswith("/chat_room/"):
            chat_id = route.route.split('/')[-1]
            page.views.append(ft.View(f"/chat_room/{chat_id}", controls=[chat_room_page(chat_id)]))
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
