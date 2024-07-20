from rest_framework import serializers
from account.models import User, UserDetail, UserRole, Transaction, Service, ServiceDetail, Channel

"""
    PM means Partner Manager.
"""


class PMAgencySerializer(serializers.ModelSerializer):
    agencyId = serializers.IntegerField(source="user_detail.user.id")
    agencyName = serializers.CharField(source="user_detail.name")
    agencyEmail = serializers.EmailField(source="user_detail.email")
    agencyAdminName = serializers.CharField(source="user_detail.name")
    agencyAdminEmail = serializers.EmailField(source="user_detail.user.email")
    dateCreated = serializers.DateTimeField(source="user_detail.user.date_joined")
    status = serializers.BooleanField(source="user_detail.approved")

    class Meta:
        model = UserRole
        fields = ['agencyId', 'agencyName', 'agencyEmail', 'agencyAdminName', 'agencyAdminEmail', 'dateCreated',
                  'status']


class PMTransactionSerializer(serializers.ModelSerializer):
    transactionID = serializers.IntegerField(source="id")
    serviceName = serializers.CharField(source="service_detail.name")
    channel = serializers.CharField(source="channel.name")
    document = serializers.CharField()
    documentId = serializers.CharField(source="document_id")
    amount = serializers.DecimalField(max_digits=30, decimal_places=4)
    name = serializers.SerializerMethodField()
    agency = serializers.SerializerMethodField()

    def get_agency(self, obj):
        user = UserDetail.objects.get(user=obj.agency)
        return user.name

    def get_name(self, obj):
        user_detail = UserDetail.objects.get(user=obj.owner)
        return user_detail.name

    class Meta:
        model = Transaction
        fields = ['transactionID', 'name', 'serviceName', 'amount', 'document', 'documentId', 'channel', 'agency',
                  'status', 'created_on']


class PMChannelImageSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        return None

    class Meta:
        model = Channel
        fields = ['logo']


class PMAgencyDetailSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_detail.user.id")
    userRole = serializers.CharField(source="user_role")
    name = serializers.CharField(source="user_detail.name")
    fullName = serializers.SerializerMethodField()
    partnerImage = serializers.SerializerMethodField()
    agencyLogo = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="user_detail.user.first_name")
    lastName = serializers.CharField(source="user_detail.user.last_name")
    phoneNumber = serializers.CharField(source="user_detail.phone_number")
    address = serializers.CharField(source="user_detail.address")
    email = serializers.EmailField(source="user_detail.user.email")
    agencyEmail = serializers.EmailField(source="user_detail.email")
    dateJoined = serializers.DateTimeField(source="user_detail.user.date_joined")
    approved = serializers.BooleanField(source="user_detail.approved")

    def get_fullName(self, obj):
        return obj.user_detail.name

    def get_agencyLogo(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.user_detail.logo.url)
        return None

    def get_partnerImage(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.user_detail.user.image.url)
        return None

    class Meta:
        model = UserRole
        fields = ['userId', 'name', 'email', 'partnerImage', 'agencyLogo', 'fullName',
                  'firstName', 'lastName', 'phoneNumber', 'agencyEmail', 'dateJoined', 'address', 'approved', 'userRole']

