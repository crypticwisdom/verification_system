from rest_framework import serializers
from .models import User, UserDetail, UserRole, State, Service, ServiceDetail, Channel
from account.models import PaymentGateWay, ClientPaymentGateWayDetail
from .utils import service_selection_algo


class IndividualSerializer(serializers.ModelSerializer):
    userRoleId = serializers.IntegerField(source="id")
    userRole = serializers.SerializerMethodField()
    userDetailId = serializers.IntegerField(source="user_detail.id")
    userId = serializers.IntegerField(source="user_detail.user.id")
    userType = serializers.CharField(source="user_detail.user_type")
    username = serializers.CharField(source="user_detail.user.username")
    phoneNumber = serializers.CharField(source="user_detail.phone_number")
    pushNotification = serializers.BooleanField(source="user_detail.user.push_notification")
    imageUrl = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="user_detail.user.first_name")
    lastName = serializers.CharField(source="user_detail.user.last_name")
    email = serializers.EmailField(source="user_detail.user.email")
    isSuperAdmin = serializers.BooleanField(source="user_detail.user.is_superuser")
    passwordIsReset = serializers.BooleanField(source="user_detail.user.super_admin_has_reset_password")

    def get_userRole(self, obj):
        return obj.user_role

    def get_imageUrl(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        return request.build_absolute_uri(obj.user_detail.user.image.url)

    class Meta:
        model = UserRole
        fields = ['userRoleId', 'userDetailId', 'userId', 'userRole', 'userType', 'username', 'pushNotification',
                  'imageUrl', 'firstName', 'lastName', 'email', 'isSuperAdmin', 'phoneNumber', 'passwordIsReset']


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']


class ListUserSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user.id')
    userType = serializers.CharField(source='user_type')

    class Meta:
        model = UserDetail
        fields = ['userId', 'userType', 'name', 'email']


class LandPageListServicesSerializer(serializers.ModelSerializer):
    serviceId = serializers.CharField(source="id")
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        request = self.context.get("request", None)
        if request:
            return request.build_absolute_uri(obj.logo)
        return None

    class Meta:
        model = Service
        fields = ['serviceId', 'name', 'logo']


class ListServiceDetailSerializer(serializers.ModelSerializer):
    serviceDetailId = serializers.SerializerMethodField()
    serviceName = serializers.CharField(source="name")
    serviceDetailCode = serializers.SerializerMethodField()
    serviceDetailDomainUrl = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    def get_serviceDetailId(self, obj):
        service_details = ServiceDetail.objects.filter(service=obj)
        for service_detail in service_details:
            if service_details.count() > 1:
                # Perform random selection of service detail
                service_detail_ids = service_details.values_list('id', flat=True)
                # chosen_service_detail = service_selection_algo(service_detail_ids=service_detail_ids)
                return service_selection_algo(service_detail_ids=service_detail_ids)
            else:
                return service_detail.id

    def get_serviceDetailCode(self, obj):
        service_detail_id = self.get_serviceDetailId(obj)
        service_detail = ServiceDetail.objects.get(id=service_detail_id)
        return service_detail.service_detail_code

    def get_serviceDetailDomainUrl(self, obj):
        service_detail_id = self.get_serviceDetailId(obj)
        service_detail = ServiceDetail.objects.get(id=service_detail_id)
        return service_detail.domain_url

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if request is None:
            return None
        return request.build_absolute_uri(obj.logo.url)

    class Meta:
        model = Service
        fields = ['serviceDetailId', 'serviceName', 'serviceDetailCode', 'serviceDetailDomainUrl', 'logo']


class AllChannelsSerializer(serializers.ModelSerializer):
    channelId = serializers.CharField(source="id")
    channelName = serializers.CharField(source="name")

    class Meta:
        model = Channel
        fields = ['channelId', 'channelName']


class ForgotPasswordResponseSerializer(serializers.ModelSerializer):
    """
        Used to give a response of the user-instance role and user type after requesting for a forgot password.
    """
    userType = serializers.CharField(source="userdetail.user_type")
    userRole = serializers.CharField(source="userdetail.userrole.user_role")

    class Meta:
        model = User
        fields = ['userType', 'userRole']


class PaymentGateWayOptionSerializer(serializers.ModelSerializer):
    payment_gateway_logo = serializers.SerializerMethodField()

    def get_payment_gateway_logo(self, obj):
        request = self.context.get('request', None)

        if request is None:
            return None

        return request.build_absolute_uri(obj.payment_gateway_logo.url)

    class Meta:
        model = PaymentGateWay
        fields = ['id', 'payment_gateway_name', 'payment_gateway_type', 'payment_gateway_logo']
