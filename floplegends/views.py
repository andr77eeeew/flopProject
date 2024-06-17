from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from floplegends.models import flopLegendsModel
from floplegends.serializers import CreateflopLegendsSerializer, flopLegendsSerializer


# Create your views here.

class CreateflopLegendsView(generics.CreateAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CreateflopLegendsSerializer

    def perform_create(self, serializer):
        creator = self.request.user
        serializer.save(creator=creator)


class AllflopLegendsView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = flopLegendsSerializer
    queryset = flopLegendsModel.objects.all()
