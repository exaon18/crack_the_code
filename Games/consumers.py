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
    game_states = {}  # Class-level dictionary to maintain game states

    def connect(self):
        self.username = self.scope['user'].username
        amount = int(self.scope['url_route']['kwargs']['amount'])
        user = MyUser.objects.get(username=self.username)
        ballance = Ballance.objects.get(user=user).ballance
        self.timer=None
        
        self.win = False
        self.warning = 0
        self.Game_turn_validator = {}  # Initialize Game_turn_validator here
        print(f"Balance: {ballance}")

        if ballance < amount:
            self.close()
        else:
            self.room_number = generate_unique_number(self.username)
            if amount == 50:
                print(f"all rooms : {room_with_50}")
                self.handle_room_connection(room_with_50, amount)

    def handle_room_connection(self, room_list, amount):
        if len(room_list) == 0 or room_list[0]["players_amount"] == 2:
            self.create_new_room(room_list, amount)
        else:
            self.join_existing_room(room_list, amount)
    
        self.num=0
    def change_turn(self):
        self.num+=1
        """Switches turn to the next player and starts a new timer."""
        print(f"change {self.num}")
        self.Game_state = Crack_the_CodeConsumer.game_states.get(self.room, {})
        if not self.Game_state:
            print("Game state not found!")
            return

        player1 = self.Game_state["player1"]
        player2 = self.Game_state["player2"]

        # Identify current player and next player
        current_player = player1 if self.Game_state[player1] else player2
        next_player = player2 if current_player == player1 else player1

        # Update game state to switch turns
        self.Game_state[current_player] = False
        self.Game_state[next_player] = True

        # Notify both players
        async_to_sync(self.channel_layer.group_send)(
            self.room,
            {
                "type": "turns",
                player1: self.Game_state[player1],
                player2: self.Game_state[player2],
                "message": f"{current_player} ran out of time! It's now {next_player}'s turn."
            }
        )

        print(f"Turn switched: {current_player} -> {next_player}")

        # Start a new timer for the next player
        self.start_turn_timer()

    def start_turn_timer(self, time_limit=30):
        """ Start a timer for the player's turn. Only player 1 controls it. """
        if self.timer:
            self.timer.cancel()  # ✅ Cancel any existing timer before starting a new one

        self.timer = threading.Timer(time_limit, self.change_turn)
        self.timer.start()

        # 🔥 Send one message to update the frontend timer
        self.send(json.dumps({"type": "turns", "timer": time_limit}))


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
            
        }
        room_list.append(self.data)
        self.room = self.room_number
        Crack_the_CodeConsumer.game_states[self.room] = self.data  # Store game state

        async_to_sync(self.channel_layer.group_add)(
            self.room,
            self.channel_name
        )
        print(f"Room with {amount}: {room_list}")
        print(self.room)
        print(self.scope['user'].username)
        self.accept()
        self.Turn = self.username == self.data["player1"]
        
    def join_existing_room(self, room_list, amount):
        self.room = room_list[0]["room_number"]
        room_list[0]["players_amount"] += 1
        room_list[0]["player2"] = self.username
        room_list[0][f"{self.username}"] = False
        Crack_the_CodeConsumer.game_states[self.room] = room_list[0]  # Update game state

        async_to_sync(self.channel_layer.group_add)(
            self.room,
            self.channel_name
        )
        self.accept()
        print(f"Room with {amount}: {room_list}")
        if room_list[0]["players_amount"] == 2:
            print("Room is now full")
            self.Game_state = Crack_the_CodeConsumer.game_states[self.room]  # Retrieve game state
            self.player_1 = self.Game_state["player1"]
            self.player_2 = self.Game_state["player2"]
            self.code = self.Game_state["code"]
            self.money = self.Game_state["amount"]
            self.player_1_turn = self.Game_state[self.player_1]
            self.player_2_turn = self.Game_state[self.player_2]
            print(f"Assigned Game_state: {self.Game_state}")
            print(f"Assigned player_1: {self.player_1}, player_2: {self.player_2}")

            room_list.pop(0)
            
            async_to_sync(self.channel_layer.group_send)(
                self.room,
                {
                    "type":"turns",
                    f"{self.player_1}": self.player_1_turn,
                    f"{self.player_2}": self.player_2_turn
                }
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room,
                {
                    "type": "start_game",
                    "player_1": self.player_1,
                    "player_2": self.player_2,
                    "amount": self.money,
                    "players_amount": 2
                }
            )
            self.start_turn_timer()
            print(f"Room with {amount}: {room_list}")

    def start_game(self, event):
        
        print("Game started and timer started")
        self.send(json.dumps(event))

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        guess = text_data_json["guess"]
        IntGuess = [int(i) for i in str(guess)]
        self.Game_state = Crack_the_CodeConsumer.game_states.get(self.room, {})  # Retrieve game state
        player1=self.Game_state["player1"]
        player2=self.Game_state["player2"]
        
        if not self.win:
            # Check if the username key exists in Game_turn_validator before accessing it
            if self.Game_state[self.username]:
                Position = 0
                Correct = 0
                for i in range(len(IntGuess)):
                    if IntGuess[i] in self.Game_state["code"]:
                        Correct += 1
                        if IntGuess[i] == self.Game_state["code"][i]:
                            Position += 1

                if Correct == 4 and Position == 4:
                    self.win = True
                    winner = self.username.strip()  # Strip any whitespace
                    loser = self.Game_state["player1"].strip() if winner == self.Game_state["player2"].strip() else self.Game_state["player2"].strip()
                    
                    try:
                        Winner_obj = MyUser.objects.get(username=winner)
                    except MyUser.DoesNotExist:
                        return  # Handle the case where the winner does not exist

                    try:
                        Loser_obj = MyUser.objects.get(username=loser)
                    except MyUser.DoesNotExist:
                        return  # Handle the case where the loser does not exist

                    Winner_Ballance = Ballance.objects.get(user=Winner_obj)
                    Loser_Ballance = Ballance.objects.get(user=Loser_obj)

                    Winner_Ballance.ballance += self.Game_state["amount"]
                    Loser_Ballance.ballance -= self.Game_state["amount"]

                    Winner_Ballance.save()
                    Loser_Ballance.save()

                    async_to_sync(self.channel_layer.group_send)(
                        self.room,
                        {
                            "type": "Game_Over",
                            "player_1": self.Game_state["player1"],
                            "player_2": self.Game_state["player2"],
                            "amount": self.Game_state["amount"],
                            "players_amount": 2,
                            "winner": winner,
                            "loser": loser
                        }
                    )
                    async_to_sync(self.channel_layer.group_discard)(
                        self.room,
                        self.channel_name
                    )
                else:
                    
                    async_to_sync(self.channel_layer.group_send)(
                        self.room,
                        {
                            "type": "OnGame",
                            "guess":guess,
                            "player":self.username,
                            "correct": Correct,
                            "position": Position
                        }
                    )
                # Switch the turn and notify both players
                self.change_turn()
                self.start_turn_timer()
                
            else:
                self.warning += 1
                self.send(json.dumps({
                    "type": "warning",
                    "message": f"you are sending moves even though it's not your turn, warning {self.warning}"
                }))

    def turns(self, event):
        self.send(json.dumps(event))

    def OnGame(self, event):
        correct = event["correct"]
        position = event["position"]
        player = event["player"]
        guess=event["guess"]
        if player==self.username:
            self.send(json.dumps({
                "type": "OnGame",
                "guess":guess,
                "correct": correct,
                "position": position,
                "player": player
            }))
        else:
            self.send(json.dumps({
                "type": "OnGame",
                
                "correct": correct,
                "position": position,
                "player": player
            }))


    def Game_Over(self, event):
        self.send(json.dumps(event))

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room,
            self.channel_name
        )
