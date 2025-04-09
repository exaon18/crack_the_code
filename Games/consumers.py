from channels.generic.websocket import WebsocketConsumer
from autapp.models import MyUser, Ballance, GameHistory, InGame
from asgiref.sync import async_to_sync
import time
import hashlib
import json
import random
import threading
from decimal import Decimal
from urllib.parse import parse_qs
import numpy as np

room_with_25 = []
room_with_50 = []
room_with_100 = []
players_in_game = []
players_in_game_bingo = []
bingo_room_with_25 = []
bingo_room_with_50 = []
bingo_room_with_100 = []

def generate_unique_number(username):
    timestamp = str(time.time())
    seed = username + timestamp
    hash_object = hashlib.sha256(seed.encode())
    unique_number = int(hash_object.hexdigest(), 16) % 1000000
    return str(unique_number).zfill(6)

def generate_unique_4_numbers():
    return random.sample(range(10), 4)

class Crack_the_CodeConsumer(WebsocketConsumer):
    game_states = {}  
    games_finished = {}  # New dictionary to track finished games per room
    timer_event = threading.Event()  
    timer_lock = threading.Lock()
    active_threads = {}  
    active_players = {}  
    

    def connect(self):
        self.username = self.scope['user'].username
        amount = int(self.scope['url_route']['kwargs']['amount'])
        user = MyUser.objects.get(username=self.username)
        ballance = Ballance.objects.get(user=user).ballance

        self.win = False
        self.game_over = False  
        self.game_ended = False  

        if ballance < amount:
            self.send(json.dumps({"proceed": False, "message": "Insufficient balance"}))
            self.close()
        else:
            self.room_number = generate_unique_number(self.username)
            if amount == 25:
                self.room_list=25
                self.handle_room_connection(room_with_25, amount)
            elif amount == 50:
                self.room_list=50
                self.handle_room_connection(room_with_50, amount)
            elif amount == 100:
                self.room_list=100
                self.handle_room_connection(room_with_100, amount)

    def handle_room_connection(self, room_list, amount):
        if len(room_list) == 0 or room_list[0]["players_amount"] == 2:
            self.create_new_room(room_list, amount)
        else:
            self.join_existing_room(room_list, amount)

    def create_new_room(self, room_list, amount):
        self.code = generate_unique_4_numbers()
        self.data = {
            "proceed": True,
            "players_amount": 1,
            "amount": amount,
            "room_number": self.room_number,
            "code": self.code,
            "player1": self.username,
            "player2": None,
            "player1_channel": self.channel_name,
            f"{self.username}": True,
            "timer": 0,
            "status":"waiting",
        }
        room_list.append(self.data)
        self.room = self.room_number
        Crack_the_CodeConsumer.game_states[self.room] = self.data  
        Crack_the_CodeConsumer.active_players[self.room] = 1  

        async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
        self.accept()
        players_in_game.append(self.username)
        print("created new room")

    def join_existing_room(self, room_list, amount):
        self.room = room_list[0]["room_number"]
        
        if self.username != room_list[0]["player1"]:
            room_list[0]["players_amount"] += 1
            room_list[0]["player2"] = self.username
            room_list[0]["player2_channel"] = self.channel_name
            room_list[0][f"{self.username}"] = False
            room_list[0]["status"] = "playing"

            Crack_the_CodeConsumer.game_states[self.room] = room_list[0]  
            Crack_the_CodeConsumer.active_players[self.room] += 1  

            async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
            self.accept()
            if room_list[0]["players_amount"] == 2:
                self.Game_state = Crack_the_CodeConsumer.game_states[self.room]  
                self.player_1 = self.Game_state["player1"]
                self.player_2 = self.Game_state["player2"]
                room_list.pop(0)
                async_to_sync(self.channel_layer.group_send)(
                    self.room, 
                    {"type": "turns", f"{self.player_1}": True, f"{self.player_2}": False}
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.room, 
                    {"type": "start_game", "player_1": self.player_1, "player_2": self.player_2, "amount": self.Game_state["amount"], "players_amount": 2}
                )
                self.start_timer()
                print("joined existing room")
        else:
            room_list.pop(0)
            players_in_game.remove(self.username)
            self.create_new_room(room_list, amount)

    def start_timer(self):
        """Starts or resets the game timer using a single persistent thread."""
        with self.timer_lock:  # Prevent race conditions
            self.timer_event.set()  # Signal any running timer to reset
            self.timer_event.clear()  # Allow a fresh countdown

            if self.room not in Crack_the_CodeConsumer.active_threads:
                Crack_the_CodeConsumer.active_threads[self.room] = threading.Thread(target=self.run_timer, daemon=True)
                Crack_the_CodeConsumer.active_threads[self.room].start()

            async_to_sync(self.channel_layer.group_send)(
                self.room, 
                {"type": "timer_limit", "timer": 45}
            )

    def run_timer(self):
        """Runs background timer and exits when game ends."""
        while not self.game_ended:
            if not Crack_the_CodeConsumer.active_players.get(self.room, 0):
                print(f"🚨 No active players. Stopping timer for room {self.room}.")
                break

            print(f"⏳ Timer running for room {self.room}...")

            if self.timer_event.wait(45):  # Reset signal received
                continue

            print(f"🕰️ Timer expired for room {self.room}. Forcing turn change.")
            self.forced_change_turn()

        print(f"🛑 Timer stopped for room {self.room}.")

    def forced_change_turn(self):
        if self.Game_state[self.username]:
            async_to_sync(self.channel_layer.group_send)(
                self.room, 
                {"type": "Forced",  "player": self.username, "message": f"{self.username} missed a move due to time out." }
            )
        else:
            if self.Game_state["player1"] == self.username:
                player = self.Game_state["player2"]
            else:
                player = self.Game_state["player1"]
            async_to_sync(self.channel_layer.group_send)(
                self.room, 
                {"type": "Forced",  "player": player, "message": f"{player} missed a move due to time out." }
            )
        self.change_turn()
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
    
    def handle_game_win(self, winner, loser, amount):
        """Handles game win, ensuring correct balance update and preventing duplicate deductions."""
        if Crack_the_CodeConsumer.games_finished.get(self.room, False):
            print(f"⚠️ Game in room {self.room} already ended. Ignoring duplicate call.")
            return  

        Crack_the_CodeConsumer.games_finished[self.room] = True  

        self.win = True
        self.game_ended = True  
        self.jackpot = Decimal(amount) * Decimal(97.5) / Decimal(100)
        self.fee = Decimal(amount) * Decimal(2.5) / Decimal(100)

        print(f"🏆 Winner: {winner} | ❌ Loser: {loser} | Jackpot: {self.jackpot} | Fee: {self.fee}")

        winner_obj = MyUser.objects.get(username=winner)
        loser_obj = MyUser.objects.get(username=loser)
        winner_balance = Ballance.objects.get(user=winner_obj)
        loser_balance = Ballance.objects.get(user=loser_obj)
        winner_history = GameHistory.objects.get(user=winner_obj)
        losser_history = GameHistory.objects.get(user=loser_obj)
        winner_history.TotalWin+=1
        winner_history.TotalEarning+=Decimal(amount)
        winner_history.TotalPlayed+=1
        losser_history.TotalPlayed+=1
        losser_history.Totaloss+=1
        winner_history.save()
        losser_history.save()
        points = {25: 7, 50: 20, 100: 45}.get(amount, 0)
        winner_obj.points += points
        loser_obj.points = max(0, loser_obj.points - points)

        winner_balance.ballance += self.jackpot
        loser_balance.ballance -= Decimal(amount)

        winner_balance.save()
        loser_balance.save()
        winner_obj.save()
        loser_obj.save()
        print(f"winner ppoints {winner_obj.points}")
        print(f"losser points {loser_obj.points}")

        async_to_sync(self.channel_layer.group_send)(
            self.room,
            {
                "type": "Game_Over",
                "winner": winner,
                "loser": loser,
                "winningAmount": str(self.jackpot),
                "betAmount":str(amount)
            }
        )

        print(f"✅ Balance updated: {winner} +{self.jackpot} | {loser} -{amount}")

    def receive(self, text_data): 
        with self.timer_lock:
            self.timer_event.set()  
            self.timer_event.clear()

        text_data_json = json.loads(text_data)
        guess = text_data_json["guess"]
        print(f"guess {guess}")
        IntGuess = [int(i) for i in str(guess)]
        self.Game_state = Crack_the_CodeConsumer.game_states.get(self.room, {})

        if not self.win and self.Game_state.get(self.username, False):
            print(f"{self.Game_state['code']}")
            Position = sum(1 for i in range(4) if IntGuess[i] == self.Game_state["code"][i])
            Correct = sum(1 for i in range(4) if IntGuess[i] in self.Game_state["code"])

            if Correct == 4 and Position == 4:
                amount = self.Game_state["amount"]
                if self.username == self.Game_state['player1']:
                    loser = self.Game_state["player2"]
                else:
                    loser = self.Game_state["player1"]

                self.handle_game_win(self.username, loser, amount)
            else:
                async_to_sync(self.channel_layer.group_send)(
                    self.room, 
                    {"type": "OnGame", "guess": guess, "player": self.username, "correct": Correct, "position": Position}
                )
                self.change_turn()
                self.start_timer()

    def Forced(self, event):
        self.send(json.dumps(event))

    def timer_limit(self, event):
        self.send(json.dumps(event))

    def Game_Over(self, event):
        self.send(json.dumps(event))
        self.disconnect(close_code=1000)

    def OnGame(self, event):
        self.send(json.dumps(event))

    def turns(self, event):
        self.send(json.dumps(event))

    def start_game(self, event):
        self.send(json.dumps(event))

    def Game_over(self, event):
        self.send(json.dumps(event))

    def disconnect(self, close_code):
        print(f"🔌 Disconnecting: {self.username}")
        
        room_state = Crack_the_CodeConsumer.game_states.get(self.room)
        
        # Check if room state exists before trying to access it
        if room_state and room_state.get("status") == "waiting":
            print("user waiting")
            Crack_the_CodeConsumer.active_players[self.room] = None
            if self.room_list == 25:
                room_with_25.pop(0)
            elif self.room_list == 50:
                room_with_50.pop(0)
            elif self.room_list == 100:
                room_with_100.pop(0)
            self.clean_up_room()
        elif room_state and not Crack_the_CodeConsumer.games_finished.get(self.room, False):
            # If game hasn't finished, declare the other player as winner
            print("game hasnt finished")
            remaining_player=""
            if self.username==room_state["player1"]:
                remaining_player=room_state["player2"]
            else:
                remaining_player=room_state["player1"]

            print(f"🚨 {self.username} left. Declaring {remaining_player} as winner.")
            self.handle_game_win(winner=remaining_player, loser=self.username, amount=room_state["amount"])
        
        # Final cleanup (if not already cleaned up)
        self.clean_up_room()

    def clean_up_room(self):
        Crack_the_CodeConsumer.game_states.pop(self.room, None)
        Crack_the_CodeConsumer.active_players.pop(self.room, None)
        Crack_the_CodeConsumer.games_finished.pop(self.room, None)

        if self.room in Crack_the_CodeConsumer.active_threads:
            Crack_the_CodeConsumer.timer_event.set()
            Crack_the_CodeConsumer.active_threads[self.room].join()
            del Crack_the_CodeConsumer.active_threads[self.room]

        async_to_sync(self.channel_layer.group_discard)(self.room, self.channel_name)
        self.close()
class BingoConsumer(WebsocketConsumer):
    game_states = {}
    active_players = {}
    games_finished = {}  # New dictionary to track finished games per room
    timer_event = threading.Event()  
    timer_lock = threading.Lock()  
    active_threads = {}
    
    def connect(self):
        self.username = self.scope['user'].username
        self.amount = int(self.scope['url_route']['kwargs']['amount'])
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        board = query_params.get('board', [''])[0]
        self.Game_state={}  # Get board as string
        
        if board:
            self.board_numbers = list(map(int, board.split(',')))  # Convert to list of numbers
            print("Received board:", self.board_numbers)  # Debugging

        
        
        user = MyUser.objects.get(username=self.username)
        ballance = Ballance.objects.get(user=user).ballance

        self.win = False
        self.game_over = False  
        self.game_ended = False  

        if ballance < self.amount:
            self.send(json.dumps({"proceed": False, "message": "Insufficient balance"}))
            self.close()
        else:
            self.room_number = generate_unique_number(self.username)
            if self.amount == 25:
                self.room_list = 25
                self.handle_room_connection(bingo_room_with_25, self.amount)
                print("connected to bingo 25")
            elif self.amount == 50:
                self.room_list = 50
                self.handle_room_connection(bingo_room_with_50, self.amount)
            elif self.amount == 100:
                self.room_list = 100
                self.handle_room_connection(bingo_room_with_100, self.amount)
    def start_timer(self):
        """Starts or resets the game timer using a single persistent thread."""
        with self.timer_lock:  # Prevent race conditions
            self.timer_event.set()  # Signal any running timer to reset
            self.timer_event.clear()  # Allow a fresh countdown

            if self.room not in Crack_the_CodeConsumer.active_threads:
                Crack_the_CodeConsumer.active_threads[self.room] = threading.Thread(target=self.run_timer, daemon=True)
                Crack_the_CodeConsumer.active_threads[self.room].start()

            async_to_sync(self.channel_layer.group_send)(
                self.room, 
                {"type": "timer_limit", "timer": 45}
            ) 
    def run_timer(self):
        """Runs background timer and exits when game ends."""
        while not self.game_ended:
            if not Crack_the_CodeConsumer.active_players.get(self.room, 0):
                print(f"🚨 No active players. Stopping timer for room {self.room}.")
                break

            print(f"⏳ Timer running for room {self.room}...")

            if self.timer_event.wait(45):  # Reset signal received
                continue

            print(f"🕰️ Timer expired for room {self.room}. Forcing turn change.")
            self.forced_change_turn()

        print(f"🛑 Timer stopped for room {self.room}.")
  
   
    def handle_room_connection(self, room_list, amount):
        if len(room_list) == 0 or room_list[0]["players_amount"] == 2:
            self.create_new_room(room_list, amount)
        else:
            self.join_existing_room(room_list, amount)

    def create_new_room(self, room_list, amount):
        self.code = generate_unique_4_numbers()
        self.data = {
            "proceed": True,
            "players_amount": 1,
            "amount": amount,
            "room_number": self.room_number,
            "player1_board": self.board_numbers,
            "player1": self.username,
            "player2": None,
            "player1_channel": self.channel_name,
            "player1_comp": 0,
            "player2_comp": 0,
            f"{self.username}": True,
            "timer": 0,
            "status": "waiting",
            "bingo":False
        }
        # Set the attribute for later use.
        self.player1_board = self.board_numbers

        room_list.append(self.data)
        self.room = self.room_number
        BingoConsumer.game_states[self.room] = self.data  
        BingoConsumer.active_players[self.room] = 1  

        async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
        self.accept()
        players_in_game.append(self.username)
        async_to_sync(self.channel_layer.send)(
            BingoConsumer.game_states[self.room]["player1_channel"],
            {
                "type":"myusername",
                "username":self.username
            }
            
        )
        print("created new room")

    def join_existing_room(self, room_list, amount):
        self.room = room_list[0]["room_number"]
        
        if self.username != room_list[0]["player1"]:
            room_list[0]["players_amount"] += 1
            room_list[0]["player2"] = self.username
            room_list[0]["player2_channel"] = self.channel_name
            room_list[0][f"{self.username}"] = False
            room_list[0]["status"] = "playing"
            room_list[0]["player2_board"]= self.board_numbers

            BingoConsumer.game_states[self.room] = room_list[0]
           
            BingoConsumer.active_players[self.room] += 1  

            async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
            self.accept()
            if room_list[0]["players_amount"] == 2:
                self.Game_state = BingoConsumer.game_states[self.room]  
                self.player_1 = self.Game_state["player1"]
                self.player_2 = self.Game_state["player2"]
                self.player1_channel=self.Game_state["player1_channel"]
                self.player2_channel=self.Game_state["player2_channel"]
                self.player1_board=self.Game_state["player1_board"]
                self.player2_board=self.Game_state["player2_board"]
                player1_turn=self.Game_state[self.player_1]
                player2_turn=self.Game_state[self.player_2]
                print(f"type {type(self.player1_board)}")
                async_to_sync(self.channel_layer.send)(
                    self.player1_channel,
                    {
                        "type":"send.board",
                        "board":self.player1_board,
                        "start":True
                    }
                )

                async_to_sync(self.channel_layer.send)(
                    self.player2_channel,
                    {
                        "type":"send.board",
                        "board":self.player2_board,
                        "start":True
                    }
                )
                room_list.pop(0)
                print(self.Game_state)
                async_to_sync(self.channel_layer.send)(
                    self.player1_channel, 
                    {"type": "turns", f"myturn": player1_turn}
                )
                async_to_sync(self.channel_layer.send)(
                    self.player2_channel, 
                    {"type": "turns", f"myturn": player2_turn}
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.room, 
                    {"type": "start_game",
                      "player_1": self.player_1,
                        "player_2": self.player_2, 
                        "amount": self.Game_state["amount"], 
                        "players_amount": 2}
                )
                self.start_timer()
                async_to_sync(self.channel_layer.send)(
            self.Game_state["player2_channel"],
            {
                "type":"myusername",
                "username":self.username
            }
            
        )
                print("joined existing room")
        else:
            room_list.pop(0)
            players_in_game.remove(self.username)
            self.create_new_room(room_list, amount)
    def count_completed_lines(self, board):
        completed = 0
        size = len(board)

        # Check rows
        for row in board:
            if all(cell == 0 for cell in row):
                completed += 1

        # Check columns
        for j in range(size):
            if all(board[i][j] == 0 for i in range(size)):
                completed += 1

        # Check main diagonal
        if all(board[i][i] == 0 for i in range(size)):
            completed += 1

        # Check anti-diagonal
        if all(board[i][size - 1 - i] == 0 for i in range(size)):
            completed += 1

        return completed
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        data = text_data_json

        game_state = BingoConsumer.game_states[self.room]
        print("Received data:", data)
        if data["type"]=="bingo" and game_state["bingo"] == False:
            if self.username==game_state["player1"]:
                if game_state["player1_comp"]>=5:
                    game_state["bingo"]==False
                    return Crack_the_CodeConsumer.handle_game_win(self, winner=self.username, loser=game_state["player2"], amount=game_state["amount"])
                
                    
                else:
                    return async_to_sync(self.channel_layer.group_send)(
                        self.room, 
                        {"type": "warning", "message": "You have not completed a line yet. if you call bingo again you will lose the game by penality"}
                        
                    )
            else:
                if game_state["player2_comp"]>=5:
                    game_state["bingo"]==False
                    return Crack_the_CodeConsumer.handle_game_win(self, winner=self.username, loser=game_state["player1"], amount=game_state["amount"])
                else:
                    return async_to_sync(self.channel_layer.group_send)(
                        self.room, 
                        {"type": "warning", "message": "You have not completed a line yet. if you call bingo again you will lose the game by penality"}
                        
                    )
        else:

        
            called_num = data["number"]
            
            # Convert boards to matrices
            player1_matrix = np.array(game_state["player1_board"]).reshape(5, 5)
            player2_matrix = np.array(game_state["player2_board"]).reshape(5, 5)
            
            # Debug: print boards before processing
            print("Player1 matrix before:", player1_matrix)
            print("Player2 matrix before:", player2_matrix)
            
            # Use .any() for the NumPy array membership check
            if game_state[self.username]:
                if called_num in self.player1_board and (player2_matrix == called_num).any():
                    p1result = np.where(player1_matrix == called_num)
                    p2result = np.where(player2_matrix == called_num)
                    
                    if p1result[0].size > 0 and p2result[0].size > 0:
                        row, col = p1result[0][0], p1result[1][0]
                        row2, col2 = p2result[0][0], p2result[1][0]
                        print(f"Player1: {called_num} found at row {row}, column {col}")
                        print(f"Player2: {called_num} found at row {row2}, column {col2}")
                        
                        # Mark the cell by assignment
                        player1_matrix[row][col] = 0
                        player2_matrix[row2][col2] = 0
                        
                        # Update the persistent board state
                        self.player1_board = player1_matrix.flatten().tolist()
                        game_state["player1_board"] = player1_matrix.flatten().tolist() 
                        game_state["player2_board"] = player2_matrix.flatten().tolist()
                        
                        # Recalculate completed lines
                        p1comp = self.count_completed_lines(player1_matrix)
                        p2comp = self.count_completed_lines(player2_matrix)
                        print(f"Player1 completed lines: {p1comp}")
                        print(f"Player2 completed lines: {p2comp}")
                        
                        # Update the game state
                        game_state["player1_comp"] = p1comp
                        game_state["player2_comp"] = p2comp
                        
                        print(f"Updated gstate1: {game_state['player1_comp']}")
                        print(f"Updated gstate2: {game_state['player2_comp']}")
                        
                        async_to_sync(self.channel_layer.send)(
                            game_state["player1_channel"],
                            {
                                "type": "result",
                                "called": called_num,
                                "completed": game_state["player1_comp"]
                            }
                        )
                        async_to_sync(self.channel_layer.send)(
                            game_state["player2_channel"],
                            {
                                "type": "result",
                                "called": called_num,
                                "completed": game_state["player2_comp"]
                            }
                        )
                        
                        # Switch turns
                        game_state[self.username] = False
                        if self.username == game_state["player1"]:
                            game_state[game_state["player2"]] = True
                        else:
                            game_state[game_state["player1"]] = True
                        
                        print(f"Turn - Player1: {game_state[game_state['player1']]}, Player2: {game_state[game_state['player2']]}")
                        
                        async_to_sync(self.channel_layer.send)(
                            game_state["player1_channel"],
                            {
                                "type": "turns",
                                "myturn": game_state[game_state["player1"]]
                            }
                        )
                        async_to_sync(self.channel_layer.send)(
                            game_state["player2_channel"],
                            {
                                "type": "turns",
                                "myturn": game_state[game_state["player2"]]
                            }
                        )
                    
                    # Debug: print boards after processing
                    print("Player1 matrix after:", 
                        player1_matrix)
                    print("Player2 matrix after:", 
                        player2_matrix)

    def result(self,event):
        self.send(json.dumps(event))
    def turns(self, event):
        self.send(json.dumps(event))
    def send_board(self,event):
        self.send(json.dumps(event))
    def start_game(self, event):
        self.send(json.dumps(event))
    def OnGame(self, event):
        self.send(json.dumps(event))
    
    def Forced(self, event):
        self.send(json.dumps(event))

    def timer_limit(self, event):
        self.send(json.dumps(event))
    def Game_Over(self, event):
        self.send(json.dumps(event))
        self.disconnect(1000)
    def myusername(self, event):
        self.send(json.dumps(event))