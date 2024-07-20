from rest_framework import serializers
from account.models import Transaction, Channel, Service, ServiceDetail

from account.utils import service_selection_algo


class SubAgencyTransactionSerializer(serializers.ModelSerializer):
    transactionId = serializers.IntegerField(source="id")
    document = serializers.SerializerMethodField()
    documentId = serializers.SerializerMethodField()
    channel = serializers.CharField(source="channel.name")
    fullName = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    def get_document(self, obj):
        if obj.document is None:
            return None
        return obj.document

    def get_documentId(self, obj):
        if obj.document_id is None:
            return None
        return obj.document_id

    def get_fullName(self, obj):
        if obj.owner is None:
            return None
        return f"{obj.owner.last_name} {obj.owner.first_name}"

    def get_agencyLogo(self, obj):
        reqeust = self.context.get("request", None)
        return reqeust.build_absolute_uri(obj.user_detail.logo.url)

    class Meta:
        model = Transaction
        fields = ['transactionId', 'fullName', 'channel', 'document', 'documentId', 'amount', 'date',
                  'status']


class SubAgencyChannelImageSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        request = self.context.get("request", None)
        if not request:
            return None
        return request.build_absolute_uri(obj.logo.url)

    class Meta:
        model = Channel
        fields = ['logo']


class SubAgencyListServiceDetailSerializer(serializers.ModelSerializer):
    serviceId = serializers.IntegerField(source="service.id")
    serviceDetailId = serializers.IntegerField(source="id")
    parentAgencyLogo = serializers.SerializerMethodField()
    serviceName = serializers.CharField(source="service.name")
    serviceDescription = serializers.CharField(source="service.description")
    serviceDetailCode = serializers.CharField(source="service_detail_code")
    serviceDetailDomainUrl = serializers.CharField(source="domain_url")

    def get_parentAgencyLogo(self, obj):
        request = self.context.get('request', None)
        if request is None:
            return None
        return request.build_absolute_uri(obj.service.logo.url)

    class Meta:
        model = ServiceDetail
        fields = ['serviceId', 'serviceDetailId', 'parentAgencyLogo', 'serviceName', 'serviceDetailCode',
                  'serviceDescription', 'serviceDetailDomainUrl']


class SubAgencyRecentVerificationSerializer(serializers.ModelSerializer):
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


class SubAgencyVerificationSerializer(serializers.ModelSerializer):
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


class SubAgencyServiceHistorySerializer(serializers.ModelSerializer):
    transactionId = serializers.IntegerField(source="id")
    document = serializers.CharField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    class Meta:
        model = Transaction
        fields = ['transactionId', 'document', 'amount', 'date', 'status']
