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
        fields = ['id','name','desc','team','admins','is_closed','preference']
        extra_kwargs = {
            'members': {
                'required': False
            }
        }
    def to_representation(self,instance):
        response = super().to_representation(instance)
        if instance.team is not None:
            response['team'] = TeamSerializer(instance.team,context={'request':self.context.get('request')}).data
        response['admins'] = UserProfileSerializer(instance.admins,many=True,context={'request':self.context.get('request')}).data
        response['members'] = UserProfileSerializer(instance.members,many=True,context={'request':self.context.get('request')}).data
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
        pref_data = validated_data.pop('preference')
        admins = validated_data.pop('admins')
        members=[]
        if 'members' in validated_data:
            members = validated_data.pop('members')
        board = models.Board.objects.create(**validated_data) 
        for admin in admins:
            board.admins.add(admin)
        for member in members:
            board.members.add(member)
        models.Preference.objects.create(board=board,**pref_data)
        return board
    def update(self, instance, validated_data):
        if 'preference' in validated_data:
            pref_data = validated_data.pop('preference')
            PreferenceSerializer(instance.preference).update(instance=instance.preference,validated_data=pref_data)
        instance = super().update(instance, validated_data)
        return instance

class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.List
        exclude = ['watched_by']