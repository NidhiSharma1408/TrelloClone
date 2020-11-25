from django.http import Http404
from django.shortcuts import render
from rest_framework import status,mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from .models import Team
from .serializers import TeamSerializer
from boards.permissions import IsMember,IsMemberOrAllowed
from userauth.models import UserProfile
from trello.emailfunc import send_email_to,send_email_to_team_members

def get_team(request,id):
        try:
            return request.user.profile.teams.get(id=id)
        except:
            raise Http404

class TeamView(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

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

