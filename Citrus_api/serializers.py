from rest_framework import serializers
from CitrusApp.models import Coach

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = '__all__'  # Or specify fields like ['id', 'name']