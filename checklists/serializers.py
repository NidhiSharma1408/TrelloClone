from rest_framework import serializers
from . import models

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Task
        fields = '__all__'

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Checklist
        fields = '__all__'
    def to_representation(self,instance):
        response = super().to_representation(instance)
        response['tasks'] = TaskSerializer(instance.tasks,many=True).data
        return response

