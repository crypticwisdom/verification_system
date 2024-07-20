from rest_framework import serializers
from account.models import Transaction, UserDetail, ServiceDetail, Service, User, UserRole


class BusinessTransactionSerializer(serializers.ModelSerializer):
    transactionID = serializers.IntegerField(source="id")
    name = serializers.IntegerField(source="full_name")
    serviceName = serializers.CharField(source="agency.userdetail.name")
    agencyServiceDetailName = serializers.CharField(source="service_detail.name")
    serviceDetailId = serializers.CharField(source="service_detail.id")
    agencyServiceType = serializers.CharField(source="service_detail.service_type")  # TYPE
    channel = serializers.CharField(source="channel.name")
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=30, decimal_places=2)
    owner = serializers.SerializerMethodField()

    def get_owner(self, obj):
        user = UserDetail.objects.get(user=obj.owner)
        return user.name

    class Meta:
        model = Transaction
        fields = ['transactionID', 'name', 'serviceName', 'serviceDetailId', 'agencyServiceDetailName', 'agencyServiceType', 'amount', 'channel', 'owner', 'status', 'created_on']


class BusinessRecentVerificationSerializer(serializers.ModelSerializer):
    serviceId = serializers.CharField(source="service.id")
    serviceDetailId = serializers.IntegerField(source="id")
    serviceDetailName = serializers.CharField(source="name")
    serviceType = serializers.CharField(source="service_type")
    serviceDetailCode = serializers.CharField(source="service_detail_code")
    serviceDetailLogo = serializers.SerializerMethodField()

    def get_serviceDetailLogo(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    class Meta:
        model = ServiceDetail
        fields = ['serviceId', 'serviceDetailId', 'serviceDetailName', 'serviceType', 'serviceDetailCode',
                  'serviceDetailLogo']


class BusinessVerificationServiceSerializer(serializers.ModelSerializer):
    agencyServiceDetail = serializers.SerializerMethodField()

    def get_agencyServiceDetail(self, obj):
        request = self.context.get("request", None)
        container, data = {}, []

        service_detail = ServiceDetail.objects.filter(service=obj)

        for detail in service_detail:
            data.append(
                {"serviceDetailId": detail.id, 'serviceDetailCode': detail.service_detail_code, "agencyName": detail.agency.userdetail.name,
                 "serviceDetailName": detail.name, "serviceDetailLogo":
                     request.build_absolute_uri(detail.logo.url), "serviceDetailPrice": detail.price,
                 "serviceDetailDiscount": detail.discount, "serviceDetailDescription": detail.description,
                 "serviceIsAvailable": detail.is_available})
        return data

    class Meta:
        model = Service
        fields = ['agencyServiceDetail']


class BusinessServiceHistorySerializer(serializers.ModelSerializer):
    transactionId = serializers.IntegerField(source="id")
    document = serializers.CharField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    class Meta:
        model = Transaction
        fields = ['transactionId', 'document', 'amount', 'date', 'status']


class BusinessProfileSerializer(serializers.Serializer):
    userId = serializers.IntegerField(source="id")
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")
    userEmail = serializers.CharField(source="email")
    userRole = serializers.SerializerMethodField()
    phoneNumber = serializers.SerializerMethodField()
    pushNotification = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_userRole(self, obj):
        if obj.userdetail:
            if obj.userdetail.userrole:
                return obj.userdetail.userrole.user_role
        return None

    def get_pushNotification(self, obj):
        return obj.push_notification

    def get_image(self, obj):
        request = self.context.get("request", None)
        if request:
            return request.build_absolute_uri(obj.image.url)
        return None
    #
    def get_phoneNumber(self, obj):
        if obj.userdetail:
            return obj.userdetail.phone_number
        return None

    class Meta:
        model = User
        # fields = "__all__"
        fields = ['userId', 'firstName', 'lastName', 'userEmail', 'phoneNumber', 'userRole', 'image', 'pushNotification']
