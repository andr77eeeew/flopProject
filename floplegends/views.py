from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication

from floplegends.models import flopLegendsModel
from floplegends.serializers import CreateflopLegendsSerializer, flopLegendsSerializer


# Create your views here.

class CreateflopLegendsView(generics.CreateAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CreateflopLegendsSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        creator = self.request.user
        cover = self.request.data.get('cover')
        serializer.save(creator=creator, cover=cover)


class AllflopLegendsView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = flopLegendsSerializer
    queryset = flopLegendsModel.objects.all()
