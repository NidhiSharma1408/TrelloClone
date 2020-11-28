from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from boards.permissions import is_allowed_to_watch_or_star
from .serializers import ActivitySerializer
from boards.models import Board
from cards.models import Card
# Create your views here.
class BoardActivity(APIView):
    def get(self,request,board_id):
        try:
            board = Board.objects.get(id=board_id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request.user.profile,board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        queryset = board.activity.all()
        serializer = ActivitySerializer(queryset,many=True,context={"request":request})
        return Response(serializer.data)

class CardActivity(APIView):
    def get(self,request,card_id):
        try:
            card = Card.models.get(id=card_id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request.user.profile,card.list.board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        queryset = card.activity.all()
        serializer = ActivitySerializer(queryset,many=True,context={"request":request})
        return Response(serializer.data)
