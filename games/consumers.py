from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import hashlib
import time

def generate_unique_number(username):
    # Get the current time in seconds
    current_time = str(int(time.time()))
    # Combine the username and the current time
    seed = username + current_time
    # Create a hash of the combined seed
    hash_object = hashlib.sha256(seed.encode())
    # Convert the hash to an integer
    hash_int = int(hash_object.hexdigest(), 16)
    # Get the last 6 digits of the integer and pad with leading zeros if necessary
    unique_number = str(hash_int % 1000000).zfill(6)
    return unique_number
class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.username= self.scope['user'].username
        self.generated_room=generate_unique_number(self.username)
        self.room_name = self.scope