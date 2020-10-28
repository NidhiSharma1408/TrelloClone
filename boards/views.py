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
from .permissions import IsAdminOfBoard,IsAllowedInBoard,IsMember,IsMemberOrAllowed
from . import models,serializers

class TeamView(ModelViewSet):
    queryset = models.Team.objects.all()
    serializer_class = serializers.TeamSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        queryset = self.request.user.profile.teams.all()
        return queryset.distinct()

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

    def get_permissions(self):
        permission_classes = []
        if self.action=='create' or self.action=='list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        elif self.action == 'delete' or self.action == 'update' or self.action=='partial_update':
            permission_classes = [IsMember]    
        return [permission() for permission in self.permission_classes]

def get_team(request,id):
        try:
            return request.user.profile.teams.get(id=id)
        except:
            raise Http404

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
    permission_classes = [IsAuthenticated]
    def create(self, request, *args, **kwargs):
        data = request.data
        data['admins'] = [request.user.profile.id]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


