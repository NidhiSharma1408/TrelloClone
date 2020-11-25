from rest_framework import serializers
from userauth.serializers import UserProfileSerializer
from cards.serializers import CardSerializer
from .models import List
class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        exclude = ['watched_by']
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['cards'] = CardSerializer(instance.cards,many=True,context={'request' : self.context.get('request')}).data
        return response
