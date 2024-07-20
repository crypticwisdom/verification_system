from rest_framework import serializers
from .models import User, UserDetail, UserRole, State, Service, ServiceDetail, Channel
from .utils import service_selection_algo


