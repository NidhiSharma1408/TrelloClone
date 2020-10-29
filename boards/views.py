from django.shortcuts import render
from django.db.models import Q
from django.http import Http404
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from userauth.models import UserProfile
from .permissions import IsBoardAdmin,IsAllowedToView,IsMember,IsMemberOrAllowed
from . import models,serializers

def get_board(request,id):
        try:
            return request.user.profile.member_in_boards.get(id=id)
        except:
            raise Http404

def get_team(request,id):
        try:
            return request.user.profile.teams.get(id=id)
        except:
            raise Http404

class TeamView(ModelViewSet):
    queryset = models.Team.objects.all()
    serializer_class = serializers.TeamSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        if "members" not in data:
            data['members'] = [request.user.profile.id]
        else:
            data["members"].append(request.user.profile.id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        boards = instance.boards.all().values('id','name','desc')
        serializer = self.get_serializer(instance,context={'request':request})
        return Response({'team': serializer.data, "boards": boards})

    def list(self, request, *args, **kwargs):
        queryset = request.user.profile.teams.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        permission_classes = []
        if self.action=='create' or self.action=='list': 
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [IsMemberOrAllowed]
        elif self.action == 'delete' or self.action == 'update' or self.action=='partial_update':
            permission_classes = [IsMember]    
        print(permission_classes)
        return [permission() for permission in permission_classes]


class AddTeamMemberView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,id):
        team = get_team(request,id)
        if 'members' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        members = request.data['members']
        for member in members:
            team.members.add(member)
        return Response({"detail" : "Members added successfully"})

class RemoveTeamMemberView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,id):
        team =get_team(request,id)
        user = request.data.get('user')
        try:
            id_user = request.data.get('user')
            user = UserProfile.objects.get(id=id_user)
        except user.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if team not in user.teams.all():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if team.members.count() == 1:
            return Response({"detail" : "Team should have at least one member. You can delete the team instead of removing the only member."},status=status.HTTP_406_NOT_ACCEPTABLE)
        team.members.remove(user)
        return Response({"detail" : "Member was removed successfully."})


class BoardView(ModelViewSet):
    queryset = models.Board.objects.all()
    serializer_class = serializers.BoardSerializer
    def create(self, request, *args, **kwargs):
        data = request.data
        data['admins'] = [request.user.profile.id]
        if 'members' in data:
            data["members"].append(request.user.profile.id)
        else:
            data['members'] = [request.user.profile.id]
        if 'preference' not in data:
            data['preference']={}
        if data.get('team',None) is None:
            data['preference']['self_join'] =False
            data['preference']['permission_level'] = models.Preference.permission.members
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        all_boards = request.user.profile.member_in_boards.all()
        personal_board = []
        starred_boards = []
        team_boards = []
        for board in all_boards:
            if request.user.profile in board.starred_by.all():
                starred_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True})
                if request.user.profile not in board.team.members.all() or board.team == None:
                    personal_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True })
                else:
                    team_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True})
        else:
            if request.user.profile not in board.team.members.all() or board.team == None:
                    personal_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : False})
            else:
                team_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : False})
        queryset = {
            "personal_boards" : personal_board,
            "starred_boards" : starred_boards,
            "team_baords" : team_boards
        }
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        # serializer = self.get_serializer(queryset, many=True)
        return Response(queryset)

    def get_permissions(self):
        permission_classes = []
        if self.action=='create' or self.action=='list': 
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [IsMember,IsBoardAdmin,IsAllowedToView]
        elif self.action == 'delete' or self.action == 'update' or self.action =='partial_update':
            permission_classes = [IsBoardAdmin]  
        return [permission() for permission in permission_classes]


class EditMembersInBoard(APIView):
    permission_classes =[IsAuthenticated]
    def get(self,request,id): #self join
        try:
            board = request.user.profile.team.boards(id=id)
        except:
            raise Http404
        if board.preference.self_join and board.preference.permission_level==models.Board.permission.team_members:
            board.members.add(request.user.profile)
            serializer = serializers.BoardSerializer(board)
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response({"detail": "You dont have permission of joining this board"},status=status.HTTP_403_FORBIDDEN)

    def post(self,request,id): #add multiple members
        board = get_board(request,id)
        if board.preference.pref_invitation == models.Preference.invitations.members or request.user.profile in board.admins.all():
            members = request.data.get("members",None)
            if members is not None:
                board.members.add(members)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self,request,id): # remove a member
        board = get_board(request,id)
        if board.members.count() ==1 or (request.user.profile in board.admins.all() and board.admins.count()==1):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        board.members.remove(request.user.profile)
        if request.user.profile in board.admins.all():
            board.admins.remove(request.user.profile)
        return Response(status=status.HTTP_200_OK)

    def patch(self,request,id): # leave board
        board = get_board(request,id)
        if board.preference.pref_invitation == models.Preference.invitations.members or request.user.profile in board.admins.all():
            member = request.data.get("member",None)
            if board.members.count() ==1 or (member in board.admins.all() and board.admins.count()==1):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            board.members.remove(member)
            if member in board.admins.all():
                board.admins.remove(member)
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
    
class StarUnstarBoard(APIView):
    def put(self,request,id):
        board = get_board(request,id)
        if request.user.profile in board.starred_by.all():
            board.starred_by.remove(request.user.profile)
            return Response("unstarred board")
        else:
            board.starred_by.add(request.user.profile)
            return Response('starred board')
    
class WatchUnwatchBoard(APIView):
    def put(self,request,id):
        board = get_board(request,id)
        if request.user.profile in board.watched_by.all():
            board.watched_by.remove(request.user.profile)
            return Response("watching board")
        else:
            board.watched_by.add(request.user.profile)
            return Response('notwatching board')

class MakeAdminOrRemoveFromAdmins(APIView):
    def patch(self,request,id):
        board = get_board(request,id)
        if request.user.profile not in board.admins.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        member = reqeust.data.get('member')
        if member not in board.admins.all():
            board.admins.remove(member)
        else:
            board.admins.add(member)
        return Response("changed permission on member successfully")
    
class CreateListView(APIView):
    def post(self,request,id,format=None):
        board = get_board(request,id)
        data = request.data
        data['board'] = board
        serializer = serializers.ListSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)       

class EditListView(APIView):
    def put(self,request,board_id,list_id):
        board = get_board(request,board_id)
        try:
            list = board.lists.get(id=list_id)
        except:
            raise Http404
        data = request.data
        serializer = serializers.ListSerializer(list)
        serializer.update(instance=list,validated_data=data)
        return Response({"detail": "list edited successfully"},status=status.HTTP_200_OK)

class WatchUnwatchList(APIView):
    def put(self,request,board_id,list_id):
        board = get_board(request,board_id)
        try:
            list = board.lists.get(id=list_id)
        except:
            raise Http404
        if request.user.profile in list.watched_by.all():
            list.watched_by.remove(request.user.profile)
            return Response("watching list")
        else:
            list.watched_by.add(request.user.profile)
            return Response('notwatching list')
