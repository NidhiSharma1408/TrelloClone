from django.shortcuts import render
from django.db.models import Q
from django.http import Http404
from rest_framework.permissions import AllowAny
from rest_framework import status,mixins
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
        serializer = self.get_serializer(data=data)
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
        invalid_emails = []
        for member in members:
            try:
                user = UserProfile.objects.get(email=member)
                team.members.add(user.id)
            except:
                invalid_emails.append(member)
        if len(invalid_emails) != 0:
            return Response({"detail": "User Not found for some emails. Please tell them to join the flow. You can add them in team after they have joined.","invalid_emails": invalid_emails})
        return Response({"detail" : "Members added successfully"})

class RemoveTeamMemberView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,id):
        team =get_team(request,id)
        user = request.data.get('user')
        try:
            user = UserProfile.objects.get(id=user)
        except:
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
        data['members'] = [request.user.profile.id]
        if 'preference' not in data:
            data['preference']={}
        if data.get('team',None) is None:
            data['preference']['self_join'] =False
            data['preference']['permission_level'] = models.Preference.permission.members
        else:
            try: 
               team = request.user.profile.teams.get(id=data['team'])
            except:
                return Response({"detail" : "Team not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        all_boards = request.user.profile.member_in_boards.all()
        personal_boards = []
        starred_boards = []
        team_boards = []
        for board in all_boards:
            if request.user.profile in board.starred_by.all():
                starred_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True})
                if board.team == None:
                    personal_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True })
                elif request.user.profile not in board.team.members.all():
                    personal_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True })
                else:
                    team_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : True})
            else:
                if board.team == None:
                    personal_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : False})
                elif request.user.profile not in board.team.members.all():
                    personal_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : False})
                else:
                    team_boards.append({'id' : board.id,'name' : board.name,'desc' : board.desc,'starred' : False})
        queryset = {
            "personal_boards" : personal_boards,
            "starred_boards" : starred_boards,
            "team_baords" : team_boards
        }
        return Response(queryset)

    def get_permissions(self):
        permission_classes = []
        if self.action=='create' or self.action=='list': 
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [IsMember|IsBoardAdmin|IsAllowedToView]
        elif self.action == 'delete' or self.action == 'update' or self.action =='partial_update':
            permission_classes = [IsBoardAdmin]  
        return [permission() for permission in permission_classes]


class EditMembersInBoard(APIView):
    permission_classes =[IsAuthenticated]
    def get(self,request,id): #self join
        try:
            board = models.Board.objects.get(id=id)
        except:
            raise Http404
        if board.team is None or request.user.profile not in board.team.members.all():
            raise Http404
        if board.preference.self_join and board.preference.permission_level==models.Preference.permission.team_members:
            board.members.add(request.user.profile)
            serializer = serializers.BoardSerializer(board,context={'request': request})
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response({"detail": "You dont have permission of joining this board"},status=status.HTTP_403_FORBIDDEN)

    def post(self,request,id): #add multiple members
        board = get_board(request,id)
        if board.preference.pref_invitation == models.Preference.invitations.members or request.user.profile in board.admins.all():
            members = request.data.get("members",None)
            if members is not None:
                for member in members:
                    try:
                        user = UserProfile.objects.get(email=member)
                        board.members.add(user.id)
                    except:
                        pass
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self,request,id): # leave board
        board = get_board(request,id)
        if board.members.count() ==1 or (request.user.profile in board.admins.all() and board.admins.count()==1):
            return Response({"detail":"board must have at least one member and admin"},status=status.HTTP_400_BAD_REQUEST)
        board.members.remove(request.user.profile)
        if request.user.profile in board.admins.all():
            board.admins.remove(request.user.profile)
        return Response({"detail":"succesully left board"},status=status.HTTP_200_OK)

    def patch(self,request,id): # remove member
        board = get_board(request,id)
        if board.preference.pref_invitation == models.Preference.invitations.members or (request.user.profile in board.admins.all()):
            member = request.data.get("member",None)
            try:
                member = UserProfile.objects.get(id=member)
            except:
                raise Http404
            if board.members.count() ==1 or (member in board.admins.all() and board.admins.count()==1):
                return Response({"detail":"board must have at least one member and admin"},status=status.HTTP_400_BAD_REQUEST)
            board.members.remove(member)
            if member in board.admins.all():
                board.admins.remove(member)
            return Response({"detail":"succesully removed from board"},status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
    
class StarUnstarBoard(APIView):
    permission_classes = [IsAuthenticated]
    def put(self,request,id):
        board = get_board(request,id)
        if request.user.profile in board.starred_by.all():
            board.starred_by.remove(request.user.profile)
            return Response({"detail": "unstarred board"})
        else:
            board.starred_by.add(request.user.profile)
            return Response({"detail" : 'starred board'})
    
class WatchUnwatchBoard(APIView):
    def put(self,request,id):
        board = get_board(request,id)
        if request.user.profile in board.watched_by.all():
            board.watched_by.remove(request.user.profile)
            return Response({"detail":"watching board"})
        else:
            board.watched_by.add(request.user.profile)
            return Response({"detail":'notwatching board'})

class MakeAdminOrRemoveFromAdmins(APIView):
    def patch(self,request,id):
        board = get_board(request,id)
        if request.user.profile not in board.admins.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        member = request.data.get('member')
        try:
            member = UserProfile.objects.get(id=member)
        except:
            raise Http404
        if member not in board.members.all():
            raise Http404
        if member in board.admins.all():
            board.admins.remove(member)
        else:
            board.admins.add(member)
        return Response({"detail" : "changed permission on member successfully"})
    
class CreateListView(APIView):
    def post(self,request,id,format=None):
        board = get_board(request,id)
        data = request.data
        data['board'] = board.id
        serializer = serializers.ListSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)       

class EditListView(APIView):
    def put(self,request,board_id,list_id):
        try:
            list = models.List.objects.get(id=list_id)
        except:
            raise Http404
        if request.user.profile not in list.board.members.all():
            raise Http404
        data = request.data
        serializer = serializers.ListSerializer(list)
        serializer.update(instance=list,validated_data=data)
        return Response({"detail": "list edited successfully"},status=status.HTTP_200_OK)

class WatchUnwatchList(APIView):
    def put(self,request,list_id):
        try:
            list = models.List.objects.get(id=list_id)
        except:
            raise Http404
        if request.user.profile not in list.board.members.all():
            raise Http404
        if request.user.profile in list.watched_by.all():
            list.watched_by.remove(request.user.profile)
            return Response("watching list")
        else:
            list.watched_by.add(request.user.profile)
            return Response('notwatching list')

class WatchUnwatchcard(APIView):
    def put(self,request,card_id):
        try:
            card = models.Card.objects.get(id=card_id)
        except:
            raise Http404
        if request.user.profile not in card.list.board.members.all():
            raise Http404
        if request.user.profile in card.watched_by.all():
            card.watched_by.remove(request.user.profile)
            return Response("watching card")
        else:
            card.watched_by.add(request.user.profile)
            return Response('notwatching card')


class CreateCardView(APIView):
    def get_list(self,request,list_id):
        try:
            return models.List.objects.get(id=list_id)
        except:
            raise Http404
    def post(self, request,list_id):
        data = request.data
        if request.user.profile not in list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        data["list"] = self.get_list(request,list_id)
        if request.user.profile not in data['list']:
            return Response(status=status.HTTP_403_FORBIDDEN)
        data['list'] = data['list'].id
        data['members'] = None
        serializer = serializers.CardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EditCardView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def put(self,request,card):
        data = request.data
        card = self.get_card(card_id)
        if request.user.profile not in card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.CardSerializer(card)
        serializer.update(instance=card,validated_data=data)
        return Response({"detail": "card edited successfully"},status=status.HTTP_200_OK)

class CreateChecklistView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        data = request.data
        card = self.get_card(card_id)
        if request.user.profile not in card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        data['card'] =card.id
        serializer = serializers.ChecklistSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EditChecklistView(APIView):
    def get_checklist(self,checklist_id):
        try:
            return models.Checklist.objectsget(id=checklist_id)
        except:
            raise Http404
    def delete(self,request,checklist_id):
        checklist=self.get_checklist(checklist_id)
        if request.user.profile not in checklist.card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        checklist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def put(self,request,checklist_id):
        checklist=self.get_checklist(checklist_id)
        if request.user.profile not in checklist.card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ChecklistSerializer(checklist)
        data=request.data
        serializer.update(instance=checklist,validated_data=data)
        return Response({"detail": "Checklist edited successfully"},status=status.HTTP_200_OK)
        
class CreateTaskView(APIView):
    def get_checklist(self,checklist_id):
        try:
            return models.Checklist.objectsget(id=checklist_id)
        except:
            raise Http404
    def post(self,request,checklist_id):
        data=request.data
        checklist=self.get_checklist(checklist_id)
        if request.user.profile not in checklist.card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        data['checklist'] = checklist.id
        serializer = serializers.TaskSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class TaskActionsView(APIView):
    def get_task(self,task_id):
        try:
            return models.Task.objects.all(id=task_id)
        except:
            raise Http404
    def patch(self,request,task_id):
        task = self.get_task(task_id)
        if request.user.profile not in task.checklist.card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        if task.completed:
            task.completed = False
        else:
            task.completed=True
        task.save()
        return Response(status=status.HTTP_200_OK)

    def put(self,request,task_id):
        task=self.get_task(task_id)
        if request.user.profile not in task.checklist.card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.taskSerializer(task)
        data=request.data
        serializer.update(instance=task,validated_data=data)
        return Response({"detail": "task edited successfully"},status=status.HTTP_200_OK)

    def delete(self,request,task_id):
        task = self.get_task(task_id)
        if request.user.profile not in task.checklist.card.list.board.members.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)