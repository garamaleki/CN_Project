from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
import threading
import time


class MyApp(App):

    def __init__(self, buffer, title):
        super().__init__()
        self.buffer = buffer
        self.widget = TextInput(multiline=True)
        self.title = title

    def log(self, m):
        self.widget.text += ">>> " + str(m) + "\n"

    def build(self):

        layout = GridLayout(cols=1, row_force_default=False, row_default_height=40)
        semi_layout_1 = GridLayout(cols=2, row_force_default=True, row_default_height=40, height=40, size_hint_y=None)
        s = TextInput(multiline=False)

        def advertise_action(button):
            self.buffer.append("Advertise")

        def register_action(button):
            self.buffer.append("Register")

        def message_action(button):
            message = "SendMessage " + s.text
            self.buffer.append(message)
            s.text = ""

        semi_layout_1.add_widget(s)
        semi_layout_1.add_widget(Button(text='SendMessage', on_press=message_action))
        layout.add_widget(semi_layout_1)
        semi_layout_2 = GridLayout(cols=2, row_force_default=True, row_default_height=40, height=40, size_hint_y=None)
        semi_layout_2.add_widget(Button(text='Register', on_press=register_action))
        semi_layout_2.add_widget(Button(text='Advertise', on_press=advertise_action))
        layout.add_widget(semi_layout_2)
        layout.add_widget(self.widget)
        return layout


class UserInterface(threading.Thread):

    def __init__(self, title):
        super().__init__()
        self.buffer = []
        self.app = None
        self.title = title

    def run(self):
        self.app = MyApp(self.buffer, self.title)
        self.app.run()

    def add_log(self, m):
        self.app.log(m)

    def read_buffer(self):
        return self.buffer
