import datetime
import secrets
import logging
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, HttpResponse
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from super_admin.serializers import SuperAdminSerializer
from django.conf import settings
from account.permission import IsDeveloper
from util.utils import incoming_request_checks, validate_email, api_response, get_incoming_request_checks, \
    phone_number_check


class DeveloperDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDeveloper]

    def get(self, request):
        try:
            _status, msg = get_incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message="Developer Dashboard Data", status=True, data={}))
        except(Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)

