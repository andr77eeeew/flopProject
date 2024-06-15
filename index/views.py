import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import jwt


def index(request):
    return HttpResponse("Kylie Jenner lipstick!")
