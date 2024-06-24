from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
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


class UpdateflopLegendsView(generics.RetrieveUpdateAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = flopLegendsSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return flopLegendsModel.objects.filter(creator=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.filter(id=self.kwargs.get('id')).first()
        if obj is None:
            raise NotFound('No object found with the given ID.')
        return obj

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except NotFound:
            return Response({"error": "No object found with the given ID."}, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.creator == self.request.user:
            serializer = self.get_serializer(obj, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response({"error": "You do not have permission to perform this action."}, status=403)


class DeleteflopLegendsView(generics.DestroyAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = flopLegendsSerializer

    def get_queryset(self):
        return flopLegendsModel.objects.filter(creator=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.filter(id=self.kwargs.get('id')).first()
        if obj is None:
            raise NotFound('No object found with the given ID.')
        return obj

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except NotFound:
            return Response({"error": "No object found with the given ID."}, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.creator == self.request.user:
            obj.delete()
            return Response({"message": "flopLegends deleted successfully."}, status=204)
        return Response({"error": "You do not have permission to perform this action."}, status=403)


class AllflopLegendsView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = flopLegendsSerializer
    queryset = flopLegendsModel.objects.all()
