from rest_framework.views import APIView
from .serializers import ChatSerializer
from .models import Chat
from rest_framework.response import Response
from rest_framework import permissions, status
from userauth.models import UserProfile
from django.shortcuts import Http404


class BoardChatView(APIView):
    def get_board(self,board_id):
        try:
            return user.member_in_boards.get(id=board_id)
        except:
            raise Http404
    def get(self, request,board_id):
        user = request.user.profile
        board = self.get_board(board_id)
        queryset = list(board.chats.all()[:50])
        serializer = ChatSerializer(queryset,many=True,context={'request':request})
        return Response(serializer.data)

    def post(self, request,board_id):
        sender  = request.user.profile
        board = self.get_board(board_id)
        data = request.data
        data['sender'] = sender.id
        data['board'] = board.id
        serializer = ChatSerializer(data=request.data,context={'request' : request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED) 