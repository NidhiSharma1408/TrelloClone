from rest_framework import serializers
from userauth.serializers import UserProfileSerializer
from .models import Team

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['Type_of_team'] = Team.Type(instance.Type_of_team).label
        response['members'] = UserProfileSerializer(instance.members,many=True,context={'request':self.context.get('request')}).data
        return response