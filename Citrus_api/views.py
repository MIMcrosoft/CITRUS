from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from CitrusApp.models import Coach
from .serializers import YourModelSerializer

# Create your views here.
class YourModelListCreateAPIView(APIView):
    def get(self, request):
        items = Coach.objects.all()
        serializer = YourModelSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = YourModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)