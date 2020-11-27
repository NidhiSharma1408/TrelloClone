from rest_framework.serializers import ModelSerializer
from .models import Activity
class ActivitySerializer(ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
    