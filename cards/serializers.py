from rest_framework import serializers
from userauth.serializers import UserProfileSerializer
from checklists.serializers import ChecklistSerializer
from . import models

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = '__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['user'] = UserProfileSerializer(instance.user,context={'request':self.context.get('request')}).data
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

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Label
        fields ='__all__'


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