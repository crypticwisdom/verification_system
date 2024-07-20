from rest_framework import serializers
from account.models import Transaction, UserRole, User, UserDetail, Service, ServiceDetail


class AgencyVerificationTransactionSerializer(serializers.ModelSerializer):
    transactionId = serializers.IntegerField(source="id")
    name = serializers.SerializerMethodField()
    document = serializers.CharField()
    documentId = serializers.CharField(source="document_id")
    amount = serializers.CharField()
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    def get_name(self, obj):
        try:
            if obj.owner is None or obj.owner.userdetail is None:
                return None
        except (Exception, ) as err:
            return None

        try:
            return obj.owner.userdetail.name
        except (Exception, ) as err:
            return None

    class Meta:
        model = Transaction
        fields = ['transactionId', 'name', 'document', 'documentId', 'amount', 'date', 'status']


class AgencySubAgencyListSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_detail.user.id")
    subAgencyName = serializers.CharField(source="user_detail.name")
    email = serializers.CharField(source="user_detail.email")
    adminFullName = serializers.SerializerMethodField()
    adminEmail = serializers.CharField(source="user_detail.user.email")
    createdOn = serializers.DateTimeField(source="user_detail.user.date_joined")
    status = serializers.BooleanField(source="user_detail.approved")

    def get_adminFullName(self, obj):
        if obj.user_detail.user.last_name is not None and obj.user_detail.user.first_name is not None:
            return f"{obj.user_detail.user.last_name} {obj.user_detail.user.first_name}"
        return None

    class Meta:
        model = UserRole
        fields = ['userId', 'subAgencyName', 'email', 'adminFullName', 'adminEmail', 'createdOn', 'status']


class AgencyGetSubAgencyProfileSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_detail.user.id")
    subAgencyName = serializers.CharField(source="user_detail.name")
    email = serializers.CharField(source="user_detail.user.email")
    agencyLogo = serializers.ImageField(source="user_detail.logo")
    adminFullName = serializers.SerializerMethodField()
    adminEmail = serializers.CharField(source="user_detail.email")
    createdOn = serializers.DateTimeField(source="user_detail.user.date_joined")
    status = serializers.BooleanField(source="user_detail.approved")

    def get_adminFullName(self, obj):
        if obj.user_detail.user.last_name is not None and obj.user_detail.user.first_name is not None:
            return f"{obj.user_detail.user.last_name} {obj.user_detail.user.first_name}"
        return None

    def get_agencyLogo(self, obj):
        reqeust = self.context.get("request", None)
        return reqeust.build_absolute_uri(obj.user_detail.logo.url)

    class Meta:
        model = UserRole
        fields = ['userId', 'subAgencyName', 'agencyLogo', 'email', 'adminFullName', 'adminEmail', 'createdOn', 'status']


class AgencyTransactionSerializer(serializers.ModelSerializer):
    transactionId = serializers.IntegerField(source="id")
    document = serializers.CharField()
    documentId = serializers.CharField(source="document_id")
    channel = serializers.CharField(source="channel.name")
    fullName = serializers.CharField(source="full_name")
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    class Meta:
        model = Transaction
        fields = ['transactionId', 'document', 'documentId', 'fullName', 'channel', 'amount', 'date',
                  'status']


class AgencyServiceDetailsSerializer(serializers.ModelSerializer):
    serviceDetailId = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    def get_serviceDetailId(self, obj):
        return obj.id

    def get_logo(self, obj):
        request = self.context.get('request', None)

        if request is None:
            return None
        return request.build_absolute_uri(obj.logo.url)

    class Meta:
        model = ServiceDetail
        fields = ['serviceDetailId', 'name', 'logo']


class AgencyExistingAndNonExistingServicesSerializer(serializers.ModelSerializer):
    serviceDetailId = serializers.IntegerField(source="id")
    name = serializers.CharField(source="service.name")
    exists = serializers.SerializerMethodField()
    createdOn = serializers.DateTimeField(source="created_on")

    def get_exists(self, obj):
        exists = False
        sub_agency_user_instance = self.context.get('sub_agency_user_instance', None)
        if sub_agency_user_instance is not None:
            service_details = ServiceDetail.objects.filter(agency=sub_agency_user_instance)

            for service_detail in service_details:
                if service_detail.service == obj.service:
                    exists = True
                    break

        return exists


    class Meta:
        model = ServiceDetail
        fields = ['serviceDetailId', 'name', 'exists', 'createdOn']


class AgencySubAgencyServiceSerializer(serializers.ModelSerializer):
    serviceId = serializers.SerializerMethodField()
    serviceName = serializers.CharField(source="service.name")
    serviceDetailId = serializers.IntegerField(source="id")
    serviceDetailStatus = serializers.BooleanField(source="is_available")
    serviceDetailLogo = serializers.SerializerMethodField()
    createdOn = serializers.DateTimeField(source="created_on")

    def get_serviceDetailLogo(self, obj):
        request = self.context.get('request', None)
        if request is None:
            return None
        return request.build_absolute_uri(obj.logo.url)

    def get_serviceId(self, obj):
        return obj.service.id

    class Meta:
        model = ServiceDetail
        fields = ['serviceId', 'serviceName', 'serviceDetailId', 'serviceDetailStatus', 'serviceDetailLogo',
                  'createdOn']

