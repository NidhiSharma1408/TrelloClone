from django.db.models import Q,F
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status,mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from .permissions import IsBoardAdmin,IsAllowedToView,IsMember,IsMemberOrAllowed,is_allowed_to_watch_or_star
from . import models,serializers
from trello.emailfunc import send_email_to,send_email_to_object_watchers
from activity.models import Activity
def get_board(request,id):
        try:
            return request.user.profile.member_in_boards.get(id=id)
        except:
            raise Http404
        
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
        # activity creation
        Activity.objects.create(description="{} created {} ".format(request.user.profile.name,serializer.data['name']),board=serializer.instance,user=request.user.profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        all_boards = request.user.profile.member_in_boards.all()
        personal_boards = request.user.profile.member_in_boards.filter(Q(team=None) | ~Q(team__members=request.user.profile)) 
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
        user = request.user.profile
        if user in board.members.all():
            return Response({"detail": "You are already a member of this board."},status=status.HTTP_400_BAD_REQUEST)
        if board.preference.self_join and board.preference.permission_level==models.Preference.permission.team_members:
            board.members.add(request.user.profile)
            # sending email notification
            mail_body = f"{user.name} joined the board {board.name}. You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
            mail_subject = f"{board.name}(Board)"
            send_email_to_object_watchers(board,mail_body,mail_subject)
            #------
            serializer = serializers.BoardSerializer(board,context={'request': request})
            # activity creation
            Activity.objects.create(description="{} joined {}.".format(user.name,board.name),board=board,user=user)
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
                        user = models.UserProfile.objects.get(user__email=member)
                    except:
                        print("user does not exist")
                        continue
                    if member in board.members.all():
                        continue
                    board.members.add(user)
                    mail_body =f"{request.user.profile.name} added you to board {board.name}.\n If you don't want to be in that board you can leave the board anytime."
                    mail_subject = f"You are invited to join board"
                    send_email_to(member,mail_body,mail_subject)
                mail_body = f"{request.user.profile.name} added some members to the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
                mail_subject = f"{board.name}(Board)"
                send_email_to_object_watchers(board,mail_body,mail_subject)
                #activity creation
                Activity.objects.create(description="{} added some members in {}.".format(request.user.profile.name,board.name),user=request.user.profile,board=board)
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
        if not is_allowed_to_watch_or_star(request.user.profile,board):
            board.starred_by.remove(request.user.profile)
            board.watched_by.remove(request.user.profile)
            lists_to_unwatch = request.user.profile.watching_lists.filter(board=board)
            request.user.profile.starred_lists.remove(*lists_to_unwatch)
            cards_to_unwatch = request.user.profile.watching_cards.filter(list__board=board)
            request.user.profile.starred_lists.remove(*cards_to_unwatch)
        mail_body = f"{request.user.profile.name} left the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
        mail_subject = f"{board.name}(Board)"
        send_email_to_object_watchers(board,mail_body,mail_subject)
        #activity creation
        Activity.objects.create(description="{} left {}.".format(request.user.profile.name,board.name),user=request.user.profile,board=board)
        return Response({"detail":"succesfully left board"},status=status.HTTP_200_OK)

    def patch(self,request,id): # remove member
        board = get_board(request,id)
        request_user_is_admin = bool(request.user.profile in board.admins.all())
        if board.preference.pref_invitation == models.Preference.invitations.members or request_user_is_admin:
            member = request.data.get("member",None)
            try:
                member = board.members.get(id=member)
            except:
                return Response({"detail": "No such member found."},status=status.HTTP_400_BAD_REQUEST)
            member_is_admin = bool(member in board.admins.all())
            if board.members.count() ==1 or (member_is_admin and board.admins.count()==1):
                return Response({"detail":"board must have at least one member and admin"},status=status.HTTP_400_BAD_REQUEST)
            if member_is_admin and not request_user_is_admin:
                return Response({"detail": "You are not allowed to remove an admin from board."},status=status.HTTP_403_FORBIDDEN)
            board.members.remove(member)
            if member in board.admins.all():
                board.admins.remove(member)
            if not is_allowed_to_watch_or_star(member,board):
                board.starred_by.remove(member)
                board.watched_by.remove(member)
                lists_to_unwatch = member.watching_lists.filter(board=board)
                member.starred_lists.remove(*lists_to_unwatch)
                cards_to_unwatch = member.watching_cards.filter(list__board=board)
                member.starred_lists.remove(*cards_to_unwatch)
            mail_body = f"{request.user.profile.name} removed you from board {board.name}."
            mail_subject = "you were removed from a board"
            send_email_to(member.user.email,mail_body,mail_subject)
            mail_body = f"{member.name} was removed from the board {board.name}.\n You are receiving this email because you are watching the board {board.name}. If you don't want to receive such emails, you can unwatch the board."
            mail_subject = f"{board.name}(Board)"
            send_email_to_object_watchers(board,mail_body,mail_subject)
            #activity creation
            Activity.objects.create(description="{} removed {} from {}.".format(request.user.profile.name,member.name,board.name),user=request.user.profile,board=board)
            return Response({"detail":"succesfully removed from board"},status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
    
class StarUnstarBoard(APIView):
    def put(self,request,id):
        try:
            board = models.Board.objects.get(id=id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request.user.profile,board):
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
        if not is_allowed_to_watch_or_star(request.user.profile,board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in board.watched_by.all():
            board.watched_by.remove(request.user.profile)
            return Response({"detail":"not watching board"})
        else:
            board.watched_by.add(request.user.profile)
            lists_to_remove = board.lists.filter(watched_by=request.user.profile)
            cards_to_remove = request.user.profile.watching_cards.filter(list__board=board)
            request.user.profile.watching_cards.remove(*cards_to_remove)
            request.user.profile.watching_lists.remove(*lists_to_remove)
            return Response({"detail":'watching board'})

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
            Activity.objects.create(description=f"{member.name} is no longer the admin of {board.name}",user=member,board=board)
        else:
            board.admins.add(member)
            mail_body = f"You are now an admin of board {board.name}"
            Activity.objects.create(description=f"{member.name} is now an admin of {board.name}",user=member,board=board)
        mail_subject = f"{board.name}(board)"
        send_email_to(member.user.email,mail_body,mail_subject)
        return Response({"detail" : "changed permission of member successfully"})
    