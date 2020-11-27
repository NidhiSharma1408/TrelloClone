from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status,mixins
from rest_framework.response import Response
from userauth.models import UserProfile
from trello.emailfunc import send_email_to_object_watchers,send_email_to
from .models import List
from .serializers import ListSerializer
from boards.permissions import is_allowed_to_watch_or_star
# Create your views here.


class CreateListView(APIView):
    def get_board(self,request,id):
        try:
            return request.user.profile.member_in_boards.get(id=id)
        except:
            raise Http404
    def get(self,request,id):
        board = self.get_board(request,id)
        serializer = ListSerializer(board.lists,many=True,context={'request':request})
        return Response(serializer.data)
        
    def post(self,request,id,format=None):
        board = self.get_board(request,id)
        data = request.data
        data['board'] = board.id
        serializer = ListSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mail_body = f"{request.user.profile.name} created a list {data['name']} to the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
        mail_subject = f"A list was added in {board.name}(Board)"
        send_email_to_object_watchers(board,mail_body,mail_subject)
        return Response(serializer.data,status=status.HTTP_201_CREATED)       

def get_list(list_id):
    try:
        return List.objects.get(id=list_id)
    except:
        raise Http404

class EditListView(APIView):
    def put(self,request,list_id):
        list = get_list(list_id)
        if request.user.profile not in list.board.members.all():
            raise Http404
        data = request.data
        if 'board' in data:
            try:
                board = request.user.profile.member_in_boards.get(id=data['board'])
                data['board'] = board
            except:
                raise Http404
            if board.team != None:
                if request.profile.user not in board.admins.all():
                    return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ListSerializer(list)
        serializer.update(instance=list,validated_data=data)
        mail_body = f"{request.user.profile.name} edited the list {list.name} in the board {list.board.name}."
        if 'archived' in data:
            if data['archive'] == True:
                mail_body = f"{request.user.profile.name} archived the list {list.name} in the board {list.board.name}."
            else:
                mail_body = f"{request.user.profile.name} unarchived the list {list.name} in the board {list.board.name}."
        elif 'board' in data:
            mail_body = f"{request.user.profile.name} moved the list {list.name} to the board {list.board.name}."
        mail_subject = f"{list.board.name}(Board)"
        send_email_to_object_watchers(list.board,mail_body,mail_subject)
        mail_subject = f"{list.name}(List)"
        send_email_to_object_watchers(list,mail_body,mail_subject)
        return Response({"detail": "list edited successfully"},status=status.HTTP_200_OK)

class WatchUnwatchList(APIView):
    def put(self,request,list_id):
        list_obj = get_list(list_id)
        if not is_allowed_to_watch_or_star(request,list_obj.board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in list_obj.board.watched_by.all():
            return Response({"detail": "You are already watching board so no need to watch list."},status=status.HTTP_400_BAD_REQUEST)
        if request.user.profile in list_obj.watched_by.all():
            list_obj.watched_by.remove(request.user.profile)
            return Response({'detail': "not watching list"})
        else:
            list_obj.watched_by.add(request.user.profile)
            cards_to_remove = list_obj.cards.filter(watched_by=request.user.profile)
            request.user.profile.watching_cards.remove(*cards_to_remove)
            return Response({'detail' : 'watching list'})
