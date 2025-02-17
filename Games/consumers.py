from channels.generic.websocket import WebsocketConsumer
from autapp.models import MyUser, game, Ballance
from asgiref.sync import async_to_sync
import time
import hashlib
import json
import random
import threading

room_with_50 = []
room_with_100 = []
room_with_500 = []
game_states = {}  # Class-level dictionary to maintain game states

def generate_unique_number(username):
    timestamp = str(time.time())
    seed = username + timestamp
    hash_object = hashlib.sha256(seed.encode())
    unique_number = int(hash_object.hexdigest(), 16) % 1000000
    return str(unique_number).zfill(6)

def generate_unique_4_numbers():
    numbers = random.sample(range(10), 4)
    return numbers

class Crack_the_CodeConsumer(WebsocketConsumer):
    game_states = {} 
    timer_thread = None  # Shared timer thread
    timer_event = threading.Event()  # Shared event to reset the timer
    timer_lock = threading.Lock() # Class-level dictionary to maintain game states
    
    def connect(self):
        self.username = self.scope['user'].username
        amount = int(self.scope['url_route']['kwargs']['amount'])
        user = MyUser.objects.get(username=self.username)
        ballance = Ballance.objects.get(user=user).ballance
        self.timer = None
        self.Game_state = None
        self.win = False
        self.warning = 0
        
        if ballance < amount:
            self.close()
        else:
            self.room_number = generate_unique_number(self.username)
            if amount == 50:
                self.handle_room_connection(room_with_50, amount)

    def handle_room_connection(self, room_list, amount):
        if len(room_list) == 0 or room_list[0]["players_amount"] == 2:
            self.create_new_room(room_list, amount)
        else:
            self.join_existing_room(room_list, amount)

    def create_new_room(self, room_list, amount):
        self.players = 1
        self.code = generate_unique_4_numbers()
        self.data = {
            "proceed": True,
            "players_amount": self.players,
            "amount": amount,
            "room_number": self.room_number,
            'code': self.code,
            "player1": self.username,
            "player2": None,
            f"{self.username}": True,
            "timer": 0  
        }
        room_list.append(self.data)
        self.room = self.room_number
        Crack_the_CodeConsumer.game_states[self.room] = self.data  # Store game state

        async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
        self.accept()

    def join_existing_room(self, room_list, amount):
        self.room = room_list[0]["room_number"]
        room_list[0]["players_amount"] += 1
        room_list[0]["player2"] = self.username
        room_list[0][f"{self.username}"] = False
        Crack_the_CodeConsumer.game_states[self.room] = room_list[0]  # Update game state

        async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
        self.accept()

        if room_list[0]["players_amount"] == 2:
            self.Game_state = Crack_the_CodeConsumer.game_states[self.room]  # Retrieve game state
            self.player_1 = self.Game_state["player1"]
            self.player_2 = self.Game_state["player2"]

            room_list.pop(0)
            
            async_to_sync(self.channel_layer.group_send)(
                self.room,
                {"type": "turns", f"{self.player_1}": True, f"{self.player_2}": False}
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room,
                {
                    "type": "start_game",
                    "player_1": self.player_1,
                    "player_2": self.player_2,
                    "amount": self.Game_state["amount"],
                    "players_amount": 2
                }
            )
            
            self.start_timer()

    def change_turn(self):
        if not Crack_the_CodeConsumer.game_states.get(self.room):
            return  

        self.Game_state = Crack_the_CodeConsumer.game_states[self.room]
        player1 = self.Game_state["player1"]
        player2 = self.Game_state["player2"]

        current_player = player1 if self.Game_state[player1] else player2
        next_player = player2 if current_player == player1 else player1

        self.Game_state[current_player] = False
        self.Game_state[next_player] = True

        async_to_sync(self.channel_layer.group_send)(
            self.room,
            {"type": "turns", player1: self.Game_state[player1], player2: self.Game_state[player2]}
        )
    
    def forced_change_turn(self):
        self.change_turn()
        self.start_timer()

    

  # Lock to avoid race conditions

    def start_timer(self):
        """Starts or resets the game timer using a single persistent thread."""
        with self.timer_lock:  # Prevent race conditions
            self.timer_event.set()  # Signal any running timer to reset
            self.timer_event.clear()  # Allow a fresh countdown

            if not Crack_the_CodeConsumer.timer_thread or not Crack_the_CodeConsumer.timer_thread.is_alive():
                Crack_the_CodeConsumer.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
                Crack_the_CodeConsumer.timer_thread.start()

    def run_timer(self):
        """Runs a background loop to handle the game timer."""
        while True:
            print(f"⏳ Timer started for 30 seconds. Active threads: {threading.active_count()}")
            if self.timer_event.wait(30):  # If event is set before 30s, reset timer
                continue  # Go back to waiting for another move
            self.forced_change_turn()  # If 30s pass without reset, force turn change



    def receive(self, text_data):
        with self.timer_lock:  # Prevent simultaneous access
            self.timer_event.set()  # Reset the timer
            self.timer_event.clear()  # Allow a fresh countdown

        text_data_json = json.loads(text_data)
        guess = text_data_json["guess"]
        IntGuess = [int(i) for i in str(guess)]
        self.Game_state = Crack_the_CodeConsumer.game_states.get(self.room, {})

        if not self.win and self.Game_state[self.username]:  
            Position = sum(1 for i in range(4) if IntGuess[i] == self.Game_state["code"][i])
            Correct = sum(1 for i in range(4) if IntGuess[i] in self.Game_state["code"])

            if Correct == 4 and Position == 4:
                self.win = True
                self.handle_game_win()
            else:
                async_to_sync(self.channel_layer.group_send)(
                    self.room,
                    {
                        "type": "OnGame",
                        "guess": guess,
                        "player": self.username,
                        "correct": Correct,
                        "position": Position
                    }
                )

                self.change_turn()
                self.start_timer()  # 🔥 Restart timer properly


    def timer_limit(self, event):
        self.send(json.dumps(event))

    def Game_Over(self, event):
        self.send(json.dumps(event))

    def OnGame(self, event):
        self.send(json.dumps(event))

    def turns(self, event):
        self.send(json.dumps(event))

    def start_game(self, event):
        self.send(json.dumps(event))
