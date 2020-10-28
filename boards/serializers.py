from rest_framework import serializers
from userauth.serializers import UserProfileSerializer
from . import models

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Team
        fields = '__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['Type_of_team'] = models.Team.Type(instance.Type_of_team).label
        response['members'] = UserProfileSerializer(instance.members,many=True,context={'request':self.context.get('request')}).data
        return response
        
class PrefernceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Preference
        exclude = ['board']
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['pref_comment'] = models.Preference.comments(instance.pref_comment).label
        response['pref_voting'] = models.Preference.voting(instance.pref_voting).label
        response['pref_invitation'] = models.Preference.invitations(instance.pref_invitation).label
        response['permission_level'] = models.Preference.permission(instance.permission_level).label
        return response
    

class BoardSerializer(serializers.ModelSerializer):
    preference = PrefernceSerializer(required=True)
    class Meta:
        model = models.Board
        fields = ['name','desc','team','admins','is_closed','personal','preference']
        extra_kwargs = {
            'guests': {
                'required': False
            }
        }
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['team'] = TeamSerializer(instance.team,context={'request':self.context.get('request')}).data
        response['admins'] = UserProfileSerializer(instance.admins,many=True,context={'request':self.context.get('request')}).data
        response['guests'] = UserProfileSerializer(instance.guests,many=True,context={'request':self.context.get('request')}).data
        response['preference'] = PrefernceSerializer(instance.preference).data
        if self.context.get('request').user.profile.id in instance.starred_by.all():
            response['stared'] = True
        else:
            response['stared'] = False
        if self.context.get('request').user.profile.id in instance.watched_by.all():
            response['watching'] = True
        else:
            response['watching'] = False
        return response

    def create(self, validated_data):
        pref_data = validated_data.pop('pref')
        admins = validated_data.pop('admins')
        guests=[]
        if 'guests' in validated_data:
            guests = validated_data.pop('guests')
        board = models.Board.objects.create(**validated_data) 
        for admin in admins:
            board.admins.add(admin)
        for guest in guests:
            board.guests.add(admin)
        models.Preference.objects.create(board=board,**pref_data)
        return board