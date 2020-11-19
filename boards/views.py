from django.db.models import Q,F
from django.http import Http404
from django.template import loader
from django.shortcuts import render
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework import status,mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from userauth.models import UserProfile
from .permissions import IsBoardAdmin,IsAllowedToView,IsMember,IsMemberOrAllowed,is_allowed_to_watch_or_star
from . import models,serializers

def send_email_to_object_watchers(object,mail_body,mail_subject):
    # sending email notification
    context = {'body':mail_body}
    html_content = loader.render_to_string('userauth/info_mail.html', context)
    send_mail(
        mail_subject,
        mail_body,'info.the.flow.app@gmail.com',
        object.watched_by.values_list('user__email',flat=True),
        html_message = html_content,fail_silently = False
    )
    #-------

def send_email_to_team_members(team,mail_body,mail_subject):
    context = {'body':mail_body}
    html_content = loader.render_to_string('userauth/info_mail.html', context)
    send_mail(
        mail_subject,
        mail_body,'info.the.flow.app@gmail.com',
        team.members.values_list('user__email',flat=True),
        html_message = html_content, fail_silently = False
    )

def send_email_to(email,mail_body,mail_subject):
    context = {'body':mail_body}
    html_content = loader.render_to_string('userauth/info_mail.html', context)
    send_mail(mail_subject, mail_body,'info.the.flow.app@gmail.com',[email], html_message = html_content, fail_silently = False)

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
        # models.Activity.objects.create(description=f"Create a team {data['name']}",user=request.user.profile)
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
                user = UserProfile.objects.get(user__email=member)
                team.members.add(user.id)
                mail_body = f"{request.user.profile.name} added you to team {team.name}. If you don't want to be a part of this team you can leave the team anytime."
                mail_subject = f'You were added to a team'
                send_email_to(member,mail_body,mail_subject) #email notification
            except:
                invalid_emails.append(member)
                # mail_body = f"Someone wanted to join you to a 'The Flow' team. Flow helps you to organise you project and other works properly to increase you productivity upto 100%. You Create an account on 'The Flow' for free. For more information visit -------------" 
        if len(invalid_emails) != 0:
            return Response({"detail": "User Not found for some emails. Please tell them to join 'The Flow'. You can add them in team after they have joined.","invalid_emails": invalid_emails})
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
        #sending email to the person who was removed
        mail_body = f"{request.user.profile.name} removed you from the team {team.name}."
        mail_subject ="You were removed from a team"
        send_email_to(user.user.email,mail_body,mail_subject)
        #sending email to all team members
        mail_body = f"{user.name} was removed from the team {team.name} by {request.user.profile.name}."
        mail_subject = "A member was removed from your team"
        send_email_to_team_members(team,mail_body,mail_subject)
        #-------
        return Response({"detail" : "Member was removed successfully."})
    def put(self,request,id): #leave team
        team =get_team(request,id)
        user = request.user.profile
        if team.members.count() == 1:
            return Response({"detail" : "Team should have at least one member. You can delete the team instead of removing the only member."},status=status.HTTP_406_NOT_ACCEPTABLE)
        team.members.remove(user)
        mail_body = f"{user.name} left your team {team.name}."
        mail_subject = f"{team.name}(Team)"
        send_email_to_team_members(team,mail_body,mail_subject)
        return Response({"detail" : "You left team successfully."})

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
        personal_boards = request.user.profile.member_in_boards.filter(team=None)
        starred_boards = request.user.profile.starred_boards.all()
        team_boards_id = request.user.profile.teams.all().values_list('boards',flat=True)
        team_boards = models.Board.objects.filter(id__in=team_boards_id,members=request.user.profile)
        queryset = {
            "personal_boards" : serializers.BoardListSerializer(personal_boards,many=True,context={"request":request}).data,
            "starred_boards" : serializers.BoardListSerializer(starred_boards,many=True,context={"request":request}).data,
            "team_baords" : serializers.BoardListSerializer(team_boards,many=True,context={"request":request}).data
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
            # sending email notification
            mail_body = f"{user.name} joined the board {board.name}. You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
            mail_subject = f"{board.name}(Board)"
            send_email_to_object_watchers(board,mail_body,mail_subject)
            #------
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
                        user = UserProfile.objects.get(user__email=member)
                    except:
                        print("user does not exist")
                        continue
                    board.members.add(user)
                    mail_body =f"{request.user.profile.name} added you to board {board.name}.\n If you don't want to be in that board you can leave the board anytime."
                    mail_subject = f"You are invited to join board"
                    send_email_to(member,mail_body,mail_subject)
                mail_body = f"{request.user.profile.name} added some members to the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
                mail_subject = f"{board.name}(Board)"
                send_email_to_object_watchers(board,mail_body,mail_subject)
                return Response({"detail":"Members were added"},status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self,request,id): # leave board
        board = get_board(request,id)
        if board.members.count() ==1 or (request.user.profile in board.admins.all() and board.admins.count()==1):
            return Response({"detail":"board must have at least one member and admin"},status=status.HTTP_400_BAD_REQUEST)
        board.members.remove(request.user.profile)
        if request.user.profile in board.admins.all():
            board.admins.remove(request.user.profile)
        mail_body = f"{request.user.profile.name} left the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
        mail_subject = f"{board.name}(Board)"
        send_email_to_object_watchers(board,mail_body,mail_subject)
        return Response({"detail":"succesfully left board"},status=status.HTTP_200_OK)

    def patch(self,request,id): # remove member
        board = get_board(request,id)
        if board.preference.pref_invitation == models.Preference.invitations.members or (request.user.profile in board.admins.all()):
            member = request.data.get("member",None)
            try:
                member = board.members.get(id=member)
            except:
                return Response({"detail": "No such member found."},status=status.HTTP_400_BAD_REQUEST)
            if board.members.count() ==1 or (member in board.admins.all() and board.admins.count()==1):
                return Response({"detail":"board must have at least one member and admin"},status=status.HTTP_400_BAD_REQUEST)
            board.members.remove(member)
            if member in board.admins.all():
                board.admins.remove(member)
            mail_body = f"{request.user.profile.name} removed you from board {board.name}."
            mail_subject = "you were removed from a board"
            send_email_to(member.user.email,mail_body,mail_subject)
            mail_body = f"{member.name} was removed from the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
            mail_subject = f"{board.name}(Board)"
            send_email_to_object_watchers(board,mail_body,mail_subject)
            return Response({"detail":"succesfully removed from board"},status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
    
class StarUnstarBoard(APIView):
    def put(self,request,id):
        try:
            board = models.Board.objects.get(id=id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request,board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in board.starred_by.all():
            board.starred_by.remove(request.user.profile)
            return Response({"detail": "unstarred board"})
        else:
            board.starred_by.add(request.user.profile)
            return Response({"detail" : 'starred board'})
    
class WatchUnwatchBoard(APIView):
    def put(self,request,id):
        try:
            board = models.Board.objects.get(id=id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request,board):
            return Response(status=status.HTTP_403_FORBIDDEN)
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
            return Response({"detail":"You are not an admin of the board so you are not allowed to perform this action"},status=status.HTTP_403_FORBIDDEN)
        member = request.data.get('member')
        try:
            member = board.members.get(id=member)
        except:
            return Response({"detail" : "No such member found."},status=status.HTTP_400_BAD_REQUEST)
        if member in board.admins.all():
            board.admins.remove(member)
            mail_body = f"You are no longer the admin of board {board.name}."
        else:
            board.admins.add(member)
            mail_body = f"You are now an admin of board {board.name}"
        mail_subject = f"{board.name}(board)"
        send_email_to(member.user.email,mail_body,mail_subject)
        return Response({"detail" : "changed permission of member successfully"})
    
class CreateListView(APIView):
    def post(self,request,id,format=None):
        board = get_board(request,id)
        data = request.data
        data['board'] = board.id
        serializer = serializers.ListSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mail_body = f"{request.user.profile.name} created a list {data['name']} to the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
        mail_subject = f"A list was added in {board.name}(Board)"
        send_email_to_object_watchers(board,mail_body,mail_subject)
        return Response(serializer.data,status=status.HTTP_201_CREATED)       

class EditListView(APIView):
    def put(self,request,list_id):
        try:
            list = models.List.objects.get(id=list_id)
        except:
            raise Http404
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
        serializer = serializers.ListSerializer(list)
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
        try:
            list = models.List.objects.get(id=list_id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request,list.board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in list.board.watched_by.all():
            return Response({"detail": "You are already watching board so no need to watch list."},status=status.HTTP_400_BAD_REQUEST)
        if request.user.profile in list.watched_by.all():
            list.watched_by.remove(request.user.profile)
            return Response("watching list")
        else:
            list.watched_by.add(request.user.profile)
            return Response('notwatching list')

class WatchUnwatchCard(APIView):
    def put(self,request,card_id):
        try:
            card = models.Card.objects.get(id=card_id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request,card.list.board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in card.list.board.watched_by.all():
            return Response({"detail": "You are already watching board so no need to watch card."},status=status.HTTP_400_BAD_REQUEST)
        if request.user.profile in card.list.watched_by.all():
            return Response({"detail": "You are already watching the list so no need to watch card."},status=status.HTTP_400_BAD_REQUEST)
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
    def get(self, request,list_id):
        list=self.get_list(request,list_id)
        if not (request.user.profile in list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ListSerializer(list,context={'request':request})
        return Response(serializer.data)

    def post(self, request,list_id):
        data = request.data
        list=self.get_list(request,list_id)
        if not (request.user.profile in list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data["list"] = list.id
        data['members'] = None
        data['index'] = list.cards.count()
        serializer = serializers.CardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mail_body = f"{request.user.profile.name} created a card {data['name']} in list {list.name} in board {list.board.name}."
        mail_subject = f"{list.board.name}(Board)"
        send_email_to_object_watchers(list.board,mail_body, mail_subject)
        mail_subject = f"{list.name}(List)"
        send_email_to_object_watchers(list,mail_body, mail_subject)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EditCardView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def put(self,request,card_id):
        data = request.data
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if 'list' in data:
            try:
                list = models.List.objects.get(id=data['list'])
                data['list'] = list
            except:
                raise Http404
            if not (request.user.profile in list.board.members.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
            mail_body = f"{request.user.profile.name} edited the card {card.name} in list {card.list.name} in board {card.list.board.name}."
            if not (list in card.list.board.lists.all()):
                return Response({"detail" : "Can't move card outside the board"},status=status.HTTP_403_FORBIDDEN)
            if list == card.list:
                if 'index' in data:
                    if data['index'] > card.list.cards.count()+1 or data['index']<0:
                        return Reponse({"detail": "Index can't hold this value"},status=status.HTTP_400_BAD_REQUEST)
                    if card.index > data['index']:
                        card.list.cards.filter(index__gte=data['index'],index__lt=card.index).update(index=F('index')+1)
                    else:
                        card.list.cards.filter(index__gt=card.index,index__lte=data['index']).update(index=F('index')-1)
            else:
                if 'index' in data:
                    if data['index'] > list.cards.count()+1 or data['index']<0:
                        return Reponse({"detail": "Index can't hold this value"},status=status.HTTP_400_BAD_REQUEST)
                    list.cards.filter(index__gte=data['index']).update(index=F('index')+1)
                    card.list.cards.filter(index_gt=card.index).update(index=F('index')-1)
                    mail_body = f"{request.user.profile.name} moved card {card.name} from list {card.list.name} to list {list.name}."
        send_email_to_object_watchers(card.list.board,mail_body,f"{card.list.board.name}(Board)")
        send_email_to_object_watchers(card.list,mail_body,f"{card.list.name}(List)")
        send_email_to_object_watchers(card,mail_body,f"{card.name}(Card)")
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
        if not (request.user.profile in card.list.board.members.all()):
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
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        checklist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def put(self,request,checklist_id):
        checklist=self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ChecklistSerializer(checklist)
        data=request.data
        serializer.update(instance=checklist,validated_data=data)
        return Response({"detail": "Checklist edited successfully"},status=status.HTTP_200_OK)
        
class CreateTaskView(APIView):
    def get_checklist(self,checklist_id):
        try:
            return models.Checklist.objects.get(id=checklist_id)
        except:
            raise Http404
    def get(self,request,checklist_id):
        checklist = self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ChecklistSerializer(checklist,context={"request":request})
        return Response(serializer.data)

    def post(self,request,checklist_id):
        data=request.data
        checklist=self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data['checklist'] = checklist.id
        serializer = serializers.TaskSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class TaskActionsView(APIView):
    def get_task(self,task_id):
        try:
            return models.Task.objects.get(id=task_id)
        except:
            raise Http404
    def get(self,request,task_id):
        task = self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.TaskSerializer(task,context={"request":request})
        return Response(serializer.data)

    def patch(self,request,task_id):
        task = self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if task.completed:
            task.completed = False
        else:
            task.completed=True
        task.save()
        return Response(status=status.HTTP_200_OK)

    def put(self,request,task_id):
        task=self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.TaskSerializer(task)
        data=request.data
        serializer.update(instance=task,validated_data=data)
        return Response({"detail": "task edited successfully","task": serializer.data},status=status.HTTP_200_OK)

    def delete(self,request,task_id):
        task = self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommentView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        board = card.list.board
        if board.preference.pref_comment == models.Preference.comments.disabled:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_comment == models.Preference.comments.admins:
            if not (request.user.profile in board.admins.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_comment == models.Preference.comments.members:
            if not (request.user.profile in board.members.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_comment == models.Preference.comments.team_members:
            if board.team:
                if not (request.user.profile in board.team.members.all()):
                    return Response(status=status.HTTP_403_FORBIDDEN)
        data = request.data
        data['card'] = card.id
        data['user'] = request.user.profile.id
        serializer = serializers.CommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    # def is_allowed(self,request,board):
    #     if board.preference.permission_level == models.Preference.permission.public or request.user.profile in board.members.all():
    #         return True
    #     if board.preference.permission_level == models.Preference.permission.team_members:
    #         if request.user.profile in board.team.members.all():
    #             return True
    #         return False
    #     return False

    def get(self,request,card_id):
        card = self.get_card(card_id)
        board = card.list.board
        if not is_allowed_to_watch_or_star(request,board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.CommentSerializer(card.comments,many=True,context={'request':request})
        return Response(serializer.data)

class VoteCardView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        board = card.list.board
        if board.preference.pref_voting == models.Preference.voting.disabled:
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_voting == models.Preference.voting.admins:
            if not (request.user.profile in board.admins.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_voting == models.Preference.voting.members:
            if not (request.user.profile in board.members.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_voting == models.Preference.voting.team_members:
            if board.team:
                if not (request.user.profile in board.team.members.all()):
                    return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in card.voted_by.all():
            card.voted_by.remove(request.user.profile)
            return Response("voted card")
        else:
            card.voted_by.add(request.user.profile)
            return Response('unvoted card')
        

class CreateLabelView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = request.data
        data['card'] = card.id
        serializer = serializers.LabelSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EditMembersInCard(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        members = request.data['members']
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        for member in members:
            try:
                user = card.list.board.members.get(user__email=member)
            except:
                continue
            card.members.add(user)
            if user != request.user.profile:
                mail_body = f"{request.user.profile.name} added you to card {card.name}."
                mail_subject = f'You were added to a card'
                send_email_to(member,mail_body,mail_subject) #email notification
        return Response({"detail":"successfully added members in card."})
    def put(self,request,card_id):
        card = self.get_card(card_id)
        members = request.data['members']
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        for member in members:
            try:
                user = card.members.get(user__email=member)
            except:
                continue
            card.members.remove(user)
            if user != request.user.profile:
                mail_body = f"{request.user.profile.name} removed you from the card {card.name}."
                mail_subject = f'You were removed from a card'
                send_email_to(member,mail_body,mail_subject) #email notification
        return Response({"detail":"successfully removed members from card."})

class AttachLinkView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment = request.data
        attachment['card'] = card.id
        serializer = serializers.AttachedLinkSerializer(data=attachment)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class AttachFileView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment = request.data
        attachment['card'] = card.id
        serializer = serializers.AttachedFileSerializer(data=attachment,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EditDeleteAttachedLinkView(APIView):
    def get_attachment(self,id):
        try:
            return models.Attached_link.objects.get(id=id)
        except:
            raise Http404
    def put(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.AttachedLinkSerializer(attachment)
        data=request.data
        serializer.update(instance=attachment,validated_data=data)
        return Response({"detail":"successful"})
    def delete(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EditDeleteAttachedFileView(APIView):
    def get_attachment(self,id):
        try:
            return models.Attached_file.objects.get(id=id)
        except:
            raise Http404
    def put(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.AttachedFileSerializer(attachment)
        data=request.data
        serializer.update(instance=attachment,validated_data=data)
        return Response({"detail":"successful"})
    def delete(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)