from userauth.models import UserProfile
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import Chat 
from .serializers import ChatSerializer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        user = self.scope['user'].profile
        print(self.room_name)
        try:
            self.scope['board'] = user.member_in_boards.get(slug__iexact=self.room_name).id
        except:
            self.close()
        self.accept()
        self.room_group_name = 'chat_%s' % self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        self.save_message(message)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'send_to_others_message',
                'message': message,
                'sender' : self.scope['user'].profile.name
            }
        )
    def save_message(self,message):
        print(message)
        data = {
            'board' : self.scope['board'],
            'sender' : self.scope['user'].profile.id,
            'text' : message
        }
        serializer = ChatSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)

    def send_to_others_message(self, event):
        message = event['message']
        sender = event['sender']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'sender' : sender
        }))