from rest_framework import serializers
from userauth.serializers import UserProfileSerializer
from . import models
from lists.serializers import ListSerializer
from .permissions import is_allowed_to_watch_or_star
class PreferenceSerializer(serializers.ModelSerializer):
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


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Board
        fields = ['id','name','slug','desc','is_closed']
    def to_representation(self,instance):
        response = super().to_representation(instance)
        user = self.context.get('request').user.profile
        if user in instance.starred_by.all():
            response['starred'] = True
        else:
            response['starred'] = False
        return response

class BoardSerializer(serializers.ModelSerializer):
    preference = PreferenceSerializer(required=True)
    class Meta:
        model = models.Board
        fields = ['id','name','desc','team','admins','is_closed','preference','members','slug']

    def to_representation(self,instance):
        response = super().to_representation(instance)
        if instance.team:
            response['team'] = {'id': instance.team.id, 'name': instance.team.name}
        response['lists'] = ListSerializer(instance.lists,many=True,context={'request' : self.context.get('request')}).data
        response['admins'] = UserProfileSerializer(instance.admins,many=True,context={'request':self.context.get('request')}).data
        response['members'] = UserProfileSerializer(instance.members,many=True,context={'request':self.context.get('request')}).data
        response['preference'] = PreferenceSerializer(instance.preference).data
        user = self.context.get('request').user.profile
        if user in instance.starred_by.all():
            response['starred'] = True
        else:
            response['starred'] = False
        if user in instance.watched_by.all():
            response['watching'] = True
        else:
            response['watching'] = False
        return response

    def create(self, validated_data):
        pref_data = validated_data.pop('preference')
        admins = validated_data.pop('admins')
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
            if "permission_level" in pref_data:
                if pref_data['permission_level'] == 3:
                    for user in instance.watched_by.all():
                        if not (user in instance.members.all()):
                            instance.watched_by.remove(user)
                    for user in instance.starred_by.all():
                        if not (user in instance.members.all()):
                            instance.starred_by.remove(user)
                    for list in instance.lists.all():
                        for user in list.watched_by.all():
                            if not (user in instance.members.all()):
                                list.watched_by.remove(user)
                        for card in list.cards.all():
                            for user in card.watched_by.all():
                                if not (user in instance.members.all()):
                                    card.watched_by.remove(user)
                elif pref_data['permission_level'] == 4:
                    for user in instance.watched_by.all():
                        if not (user in instance.members.all()) and not (user in instance.team.members.all()):
                            instance.watched_by.remove(user)
                    for user in instance.starred_by.all():
                        if not (user in instance.members.all()) and not (user in instance.team.members.all()):
                            instance.starred_by.remove(user)
                    for list in instance.lists.all():
                        for user in list.watched_by.all():
                            if not (user in instance.members.all()) and not (user in instance.team.members.all()):
                                list.watched_by.remove(user)
                        for card in list.cards.all():
                            for user in card.watched_by.all():
                                if not (user in instance.members.all()) and not (user in instance.team.members.all()):
                                    card.watched_by.remove(user)
            PreferenceSerializer(instance.preference).update(instance=instance.preference,validated_data=pref_data)
        instance = super().update(instance, validated_data)
        return instance

