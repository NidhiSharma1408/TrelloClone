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

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Task
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = '__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['user'] = UserProfileSerializer(instance.user,context={'request':self.context.get('request')}).data
        return response

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Checklist
        fields = '__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['tasks'] = TaskSerializer(instance.tasks,many=True).data
        return response

class AttachedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attached_file
        fields ='__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['file'] = 'http://' + self.context["request"].META['HTTP_HOST'] + response['file']
        return response
class AttachedLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attached_link
        fields = '__all__'

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Card
        exclude = ['voted_by','watched_by','members']
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['checklists'] = ChecklistSerializer(instance.checklists,many=True,context={'request' : self.context.get('request')}).data
        response['attachment_links'] = AttachedLinkSerializer(instance.attached_links,many=True,context={'request' : self.context.get('request')}).data
        response['attachment_files'] = AttachedFileSerializer(instance.attached_files,many=True,context={'request' : self.context.get('request')}).data
        response['checklists'] = ChecklistSerializer(instance.checklists,many=True,context={'request' : self.context.get('request')}).data
        response['members'] = UserProfileSerializer(instance.members,many=True,context={'request' : self.context.get('request')}).data
        if instance.list.board.preference.voting_visible:
            response['votes'] = UserProfileSerializer(instance.voted_by,many=True,context={'request' : self.context.get('request')}).data        
        else:
            response['votes'] = None
        response['no_of_votes']=instance.voted_by.count()
        response['label'] = LabelSerializer(instance.label,many=True).data
        return response

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Label
        fields ='__all__'

class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.List
        exclude = ['watched_by']
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['cards'] = CardSerializer(instance.cards,many=True,context={'request' : self.context.get('request')}).data
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

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Activity
        fields = '__all__'
    