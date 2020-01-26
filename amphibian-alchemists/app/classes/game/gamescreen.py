import os
from datetime import datetime
from random import sample
from string import ascii_uppercase

from enigma.machine import EnigmaMachine
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from requests import get

from .save_game import on_config_change, save_rotors, store_put

DATA_DIR = os.path.join(
    App.get_running_app().APP_DIR, os.path.normcase("data/gamestate.json")
)
CONFIG_DIR = os.path.join(
    App.get_running_app().APP_DIR, os.path.normcase("data/gameconfig.json")
)


def get_wiki_summary() -> str:
    endpoint = (
        "https://en.wikipedia.org/w/api.php?action=query&list=random&"
        "format=json&rnnamespace=0&rnlimit=1&origin=*"
    )
    response = get(endpoint)
    title = (response.json())["query"]["random"][0]["title"]
    endpoint = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    response1 = get(endpoint + title.replace(" ", "%20"))
    return response1.json()["extract"]


def get_encrypted_text(text: str, rotor_settings: str, plug_settings: str) -> str:
    machine = EnigmaMachine.from_key_sheet(
        rotors="I II III",
        reflector="B",
        ring_settings=[1, 20, 11],
        plugboard_settings=plug_settings,
    )
    machine.set_display(rotor_settings)
    return machine.process_text(text)


def setup_new_game_settings():
    store = JsonStore(DATA_DIR)
    current_game_id = store.get("latest_game_id")["id"]
    if current_game_id is None:
        store.put("latest_game_id", id=0)
    else:
        store.put("latest_game_id", id=int(current_game_id) + 1)
    # Setting up data
    game_id = store.get("latest_game_id")["id"]
    App.get_running_app().game_id = game_id
    plug_array = sample(ascii_uppercase, 20)
    plugs = []
    for i in range(10):
        plugs.append("".join(plug_array[i * 2 : i * 2 + 2]))  # noqa
    plug_settings = " ".join(x for x in plugs)
    rotors = sample(ascii_uppercase, 3)
    rotor_setting = "".join(rotors)

    # Setting defaults for the singleton machine
    # Need to re-instantiate the machine
    App.get_running_app().machine = EnigmaMachine.from_key_sheet(
        rotors="I II III",
        reflector="B",
        ring_settings=[1, 20, 11],
        plugboard_settings=plug_settings,
    )
    App.get_running_app().machine.set_display(rotor_setting)
    # Storing data
    rotors.append(None)
    rotors.append(None)
    text = get_wiki_summary()
    ciphered_text = get_encrypted_text(text, rotor_setting, plug_settings)
    store.put(
        game_id,
        game_title="Game {}".format(game_id),
        ciphered_text=ciphered_text,
        unciphered_text=get_encrypted_text(ciphered_text, rotor_setting, plug_settings),
        current_output_text="",
        last_saved_output_text="",
        created_date=datetime.now().isoformat(),
        last_saved_date=datetime.now().isoformat(),
        encrypted_state={"reflector": "B", "rotors": rotor_setting, "plugs": plugs},
        current_state={
            "reflector": "B",
            "rotors": ["A", "A", "A", None, None],
            "plugs": [],
        },
        last_saved_state={
            "reflector": "B",
            "rotors": ["A", "A", "A", None, None],
            "plugs": [],
        },
    )


class EnigmaOutput(TextInput):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == "backspace":
            return True

    def keyboard_on_key_up(self, window, keycode):
        if keycode[1] == "backspace":
            return True

    def insert_text(self, substring, from_undo=False):
        if substring.upper() in App.get_running_app().keys:
            # Autoinput
            letter = substring.upper()
            config_store = JsonStore(CONFIG_DIR)
            try:
                if config_store.get("auto_input")["value"] == 1:
                    game_id = App.get_running_app().game_id
                    store = JsonStore(DATA_DIR)
                    game = store.get(str(game_id))
                    current_output_text = game["current_output_text"]
                    ciphered_text = game["ciphered_text"]
                    letter = str(ciphered_text)[len(current_output_text)]
            except KeyError:
                config_store.put("auto_input", value=1)
            # Key press
            s = App.get_running_app().machine.key_press(letter)
            return super().insert_text(s, from_undo=from_undo)


class GameScreen(Screen):
    current_time = StringProperty("")

    Builder.load_file("kvs/game/enigmakeyboard.kv")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_key_down=self._on_key_down)

    def load_output_text(self):
        """On load of game from selector screen, put text in board"""
        game_id = App.get_running_app().game_id
        store = JsonStore(DATA_DIR)
        keyboard_output = store.get(str(game_id))["current_output_text"]
        if keyboard_output:
            self.ids.enigma_keyboard.ids.lamp_board.ids.board_output.text = (
                keyboard_output
            )
        else:
            self.ids.enigma_keyboard.ids.lamp_board.ids.board_output.text = ""

    def play_effect_sound(self, sound):
        sound_names = {
            "pop",
            "plug_in",
            "keyboard_click",
            "paper",
            "button_1",
            "swoosh",
            "button_2",
            "rotor",
        }
        if sound not in sound_names:
            return

        settings = JsonStore(CONFIG_DIR)

        volume = 1.0

        if settings.exists("effects_volume"):
            if settings.get("effects_volume")["value"] == 0:
                return
            else:
                volume = settings.get("effects_volume")["value"]

        sound = SoundLoader.load(
            "misc/" + sound + (".wav" if sound != "swoosh" else ".mp3")
        )
        sound.volume = volume
        sound.play()

    if not os.path.exists(DATA_DIR):
        store = JsonStore(DATA_DIR)
        store.put("latest_game_id", id=None)

    def on_enter(self, *args):
        store = JsonStore(DATA_DIR)
        game_id = App.get_running_app().game_id
        if game_id is None or store.exists(str(App.get_running_app().game_id)) is False:
            setup_new_game_settings()
        else:
            on_config_change()

        self.timer_clock = Clock.schedule_interval(self.handle_timer, 1)

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        if (
            self.manager.current == "game_screen"
            and isinstance(codepoint, str)
            and codepoint.upper() in App.get_running_app().keys
            and self.ids.enigma_keyboard.ids.lamp_board.ids.board_output.focus
        ):
            self.ids.enigma_keyboard.ids.keyboard.ids[
                codepoint.upper()
            ].trigger_action()

    def handle_key(self, key):
        """
        Here goes what we're gonna do whenever a key in the machine is pressed
        """

        self.play_effect_sound("keyboard_click")

        anim = Animation(_color=[1, 212 / 255, 42 / 255], duration=0.2) + Animation(
            _color=[1, 1, 1], duration=0.2
        )
        anim.start(self.ids.enigma_keyboard.ids.lamp_board.ids.lamp)

        # Auto-input invading key
        letter = key.name  # Saving in case auto-input disabled
        config_store = JsonStore(CONFIG_DIR)
        try:
            if config_store.get("auto_input")["value"] == 1:
                game_id = App.get_running_app().game_id
                store = JsonStore(DATA_DIR)
                game = store.get(str(game_id))
                current_output_text = game["current_output_text"]
                ciphered_text = game["ciphered_text"]
                letter = str(ciphered_text)[len(current_output_text)]
        except KeyError:
            config_store.put("auto_input", value=1)
        board_output = self.ids.enigma_keyboard.ids.lamp_board.ids.board_output
        if not board_output.focus:
            board_output.insert_text(letter)
        store_put(current_output_text=board_output.text)
        # Updating rotors
        new_rotors = App.get_running_app().machine.get_display()
        save_rotors(new_rotors[0], new_rotors[1], new_rotors[2])
        rotor_screen = self.manager.get_screen("rotor_screen")
        rotor_screen.rotor_section.ids.first_rotor.rotor_value.text = new_rotors[0]
        rotor_screen.rotor_section.ids.second_rotor.rotor_value.text = new_rotors[1]
        rotor_screen.rotor_section.ids.third_rotor.rotor_value.text = new_rotors[2]

    def load_old_game(self):
        game_id = App.get_running_app().game_id
        store = JsonStore(DATA_DIR)
        game = store.get(str(game_id))
        store_put(
            last_saved_date=datetime.now().isoformat(),
            current_state=game["last_saved_state"],
            current_output_text=game["last_saved_output_text"],
        )
        on_config_change()
        self.manager.get_screen("game_selector_screen").load_game(game_id)

    def save_game(self):
        game_id = App.get_running_app().game_id
        store = JsonStore(DATA_DIR)
        game = store.get(str(game_id))
        store_put(
            last_saved_date=datetime.now().isoformat(),
            last_saved_state=game["current_state"],
            last_saved_output_text=self.ids.enigma_keyboard.ids.lamp_board.ids.board_output.text,
        )

    def change_game_title(self, btn, title):
        if title != "" or title is not None:
            store_put(game_title=title)

    def handle_timer(self, dt):
        if int(self.current_time) == 0:
            self.timer_clock.cancel()
            Factory.TimesUp().open()
        else:
            self.current_time = str(int(self.current_time) - 1)
