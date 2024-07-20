from rest_framework import serializers
from account.models import Transaction, UserDetail, ServiceDetail, Service, User, UserRole
from account.utils import service_selection_algo


class IndividualTransactionSerializer(serializers.ModelSerializer):
    transactionID = serializers.IntegerField(source="id")
    name = serializers.CharField(source="full_name")
    document = serializers.CharField()
    documentId = serializers.CharField(source="document_id")
    channel = serializers.CharField(source="channel.name")
    amount = serializers.SerializerMethodField()
    dateRequested = serializers.DateTimeField(source="updated_on")
    status = serializers.CharField()

    def get_amount(self, obj):
        if obj.amount is None:
            return 0.0
        return obj.amount

    class Meta:
        model = Transaction
        fields = ['transactionID', 'name', 'document', 'documentId', 'channel', 'amount', 'dateRequested', 'status']


class IndividualVerificationServicesListSerializer(serializers.ModelSerializer):
    serviceId = serializers.IntegerField(source="id")
    serviceName = serializers.CharField(source="name")
    serviceDescription = serializers.CharField(source="description")
    serviceDetail = serializers.SerializerMethodField()
    serviceLogo = serializers.SerializerMethodField()

    def get_serviceLogo(self, obj):
        request = self.context.get("request", None)
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_serviceDetail(self, obj):
        data = []
        service_type = self.context.get("service_type", None)
        request = self.context.get("request", None)

        service_details = ServiceDetail.objects.filter(service=obj, service_type=service_type, is_available=True)

        for service_detail in service_details:
            data.append({"serviceDetailId": service_detail.id, "type": service_detail.service_type,
                         "serviceDetailCode": service_detail.service_detail_code,
                         "logo": request.build_absolute_uri(service_detail.logo.url), "price": service_detail.price
                         })
        return data

    class Meta:
        model = Service
        fields = ['serviceId', 'serviceName', 'serviceLogo', 'serviceDetail', 'serviceDescription']


class IndividualVerificationServiceSerializer(serializers.ModelSerializer):
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


class IndividualServiceHistorySerializer(serializers.ModelSerializer):
    transactionId = serializers.IntegerField(source="id")
    document = serializers.CharField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    class Meta:
        model = Transaction
        fields = ['transactionId', 'document', 'amount', 'date', 'status']


class IndividualRecentVerificationSerializer(serializers.ModelSerializer):
    serviceId = serializers.CharField(source="service.id")
    serviceDetailId = serializers.CharField(source="id")
    serviceName = serializers.CharField(source="service.name")
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
        fields = ['serviceId', 'serviceDetailId', 'serviceName', 'serviceType', 'serviceDetailCode',
                  'serviceDetailLogo']


class IndividualProfileSerializer(serializers.Serializer):
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
        fields = ['userId', 'firstName', 'lastName', 'userEmail', 'phoneNumber', 'userRole', 'image', 'pushNotification']


class LandPageServicesSerializer(serializers.ModelSerializer):
    serviceId = serializers.IntegerField(source="id")
    serviceDetailId = serializers.SerializerMethodField()
    serviceName = serializers.CharField(source="name")
    serviceDetailCode = serializers.SerializerMethodField()
    serviceDetailDomainUrl = serializers.SerializerMethodField()

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

    class Meta:
        model = Service
        fields = ['serviceId', 'serviceDetailId', 'serviceName', 'serviceDetailCode', 'serviceDetailDomainUrl']