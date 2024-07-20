from rest_framework import serializers
from account.models import User, UserDetail, UserRole, Service, ServiceDetail, Transaction
from account.models import Channel


class SuperAdminSerializer(serializers.ModelSerializer):
    userRoleId = serializers.IntegerField(source="id")
    userRole = serializers.SerializerMethodField()
    userDetailId = serializers.IntegerField(source="user_detail.id")
    userId = serializers.IntegerField(source="user_detail.user.id")
    userType = serializers.CharField(source="user_detail.user_type")
    username = serializers.CharField(source="user_detail.user.username")
    imageUrl = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="user_detail.user.first_name", )
    lastName = serializers.CharField(source="user_detail.user.last_name")
    email = serializers.EmailField(source="user_detail.user.email")
    isSuperAdmin = serializers.BooleanField(source="user_detail.user.is_superuser")

    def get_userRole(self, obj):
        return obj.user_role

    def get_imageUrl(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        return request.build_absolute_uri(obj.user_detail.user.image.url)

    class Meta:
        model = UserRole
        fields = ['userRoleId', 'userDetailId', 'userId', 'userRole', 'userType', 'username',
                  'imageUrl', 'firstName', 'lastName', 'email', 'isSuperAdmin']


class SuperAdminDashboardUserCategorySerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_detail.user.id")
    fullName = serializers.SerializerMethodField()  # here needs to be Agency Name
    agencyName = serializers.CharField(source="user_detail.name")
    userType = serializers.CharField(source="user_detail.user_type")
    firstName = serializers.CharField(source="user_detail.user.first_name")
    lastName = serializers.CharField(source="user_detail.user.last_name")
    email = serializers.EmailField(source="user_detail.user.email")
    agencyEmail = serializers.EmailField(source="user_detail.email")
    date_joined = serializers.DateTimeField(source="user_detail.user.date_joined")
    approved = serializers.BooleanField(source="user_detail.approved")

    def get_userRole(self, obj):
        return obj.user_role

    def get_imageUrl(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        return request.build_absolute_uri(obj.user_detail.user.image.url)

    def get_fullName(self, obj):
        return obj.user_detail.name

    def get_created(self, obj):
        return str(obj.user_detail.user.date_joined.date)

    class Meta:
        model = UserRole
        fields = ['userId', 'fullName', 'agencyName', 'email', 'agencyEmail', 'userType', 'firstName', 'lastName',
                  'date_joined',
                  'approved']


class SuperAdminServiceSerializer(serializers.ModelSerializer):
    serviceId = serializers.IntegerField(source="id")
    name = serializers.CharField()
    isActive = serializers.BooleanField(source="activate")
    description = serializers.CharField()
    createdOn = serializers.DateTimeField(source="created_on")

    def get_serviceType(self, obj):
        return obj.servicedetail.servicetype

    class Meta:
        model = Service
        # fields = ['serviceId', 'name', 'serviceCode', 'description', 'isActive', 'agency', 'createdOn']
        fields = ['serviceId', 'name', 'description', 'isActive', 'createdOn']


class SuperAdminUserCategoryPartnerManager(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_detail.user.id")
    userRole = serializers.CharField(source="user_role")
    name = serializers.CharField(source="user_detail.name")
    fullName = serializers.SerializerMethodField()
    noOfAgenciesAssigned = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="user_detail.user.first_name")
    lastName = serializers.CharField(source="user_detail.user.last_name")
    email = serializers.EmailField(source="user_detail.user.email")
    dateJoined = serializers.DateTimeField(source="user_detail.user.date_joined")
    approved = serializers.BooleanField(source="user_detail.approved")

    def get_fullName(self, obj):
        return obj.user_detail.name

    def get_noOfAgenciesAssigned(self, obj):
        return obj.user_detail.manages.count()

    class Meta:
        model = UserRole
        fields = ['userId', 'name', 'email', 'noOfAgenciesAssigned', 'fullName',
                  'firstName', 'lastName', 'dateJoined', 'approved', 'userRole']


class SuperAdminUserCreationSerializer(serializers.ModelSerializer):
    userRoleId = serializers.IntegerField(source="id")
    userRole = serializers.SerializerMethodField()
    name = serializers.CharField(source="user_detail.name")
    userDetailId = serializers.IntegerField(source="user_detail.id")
    userId = serializers.IntegerField(source="user_detail.user.id")
    userType = serializers.CharField(source="user_detail.user_type")
    username = serializers.CharField(source="user_detail.user.username")
    imageUrl = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="user_detail.user.first_name", )
    lastName = serializers.CharField(source="user_detail.user.last_name")
    email = serializers.EmailField(source="user_detail.user.email")
    agencyEmail = serializers.EmailField(source="user_detail.email")
    approved = serializers.BooleanField(source="user_detail.approved")
    createdBy = serializers.IntegerField(source="user_detail.user.id")

    def get_userRole(self, obj):
        return obj.user_role

    def get_imageUrl(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        return request.build_absolute_uri(obj.user_detail.user.image.url)

    class Meta:
        model = UserRole
        fields = ['userRoleId', 'name', 'userDetailId', 'userId', 'userRole', 'userType', 'username',
                  'imageUrl', 'firstName', 'lastName', 'email', 'agencyEmail', 'approved', 'createdBy']


class SuperAdminPartnerManagerDetailSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_detail.user.id")
    userRole = serializers.CharField(source="user_role")
    name = serializers.CharField(source="user_detail.name")
    fullName = serializers.SerializerMethodField()
    partnerImage = serializers.SerializerMethodField()
    noOfAgenciesAssigned = serializers.SerializerMethodField()
    firstName = serializers.CharField(source="user_detail.user.first_name")
    lastName = serializers.CharField(source="user_detail.user.last_name")
    phoneNumber = serializers.CharField(source="user_detail.phone_number")
    email = serializers.EmailField(source="user_detail.user.email")
    dateJoined = serializers.DateTimeField(source="user_detail.user.date_joined")
    approved = serializers.BooleanField(source="user_detail.approved")

    def get_fullName(self, obj):
        return obj.user_detail.name

    def get_noOfAgenciesAssigned(self, obj):
        return obj.user_detail.manages.count()

    def get_partnerImage(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.user_detail.user.image.url)
        return None

    class Meta:
        model = UserRole
        fields = ['userId', 'name', 'email', 'partnerImage', 'noOfAgenciesAssigned', 'fullName',
                  'firstName', 'lastName', 'phoneNumber', 'dateJoined', 'approved', 'userRole']


class SuperAdminPartnerManagerAgencyListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    agencyName = serializers.CharField(source='userdetail.name')
    adminFullName = serializers.SerializerMethodField()
    userType = serializers.CharField(source="userdetail.user_type")
    numberVerification = serializers.SerializerMethodField()
    agencyEmail = serializers.EmailField(source="userdetail.email")
    adminEmail = serializers.EmailField(source="email")
    created = serializers.DateTimeField(source="date_joined")
    approved = serializers.BooleanField(source="userdetail.approved")

    def get_userType(self, obj):
        return obj.userdetail.user_type

    def get_adminFullName(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_noOfAgenciesAssigned(self, obj):
        return obj.user_detail.manages.count()

    def get_numberVerification(self, obj):
        return "Number of Verification Done on this Agency"

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.userdetail.logo)
        return None

    class Meta:
        model = User
        fields = ['id', 'agencyName', 'logo', 'agencyEmail', 'adminEmail', 'adminFullName', 'numberVerification',
                  'userType', 'approved', 'created']


class SuperAdminAgencyDetailSerializer(serializers.ModelSerializer):
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
                  'firstName', 'lastName', 'phoneNumber', 'agencyEmail', 'dateJoined', 'address', 'approved',
                  'userRole']


class SuperAdminTransactionSerializer(serializers.ModelSerializer):
    transactionID = serializers.IntegerField(source="id")
    serviceName = serializers.SerializerMethodField()
    channel = serializers.CharField(source="channel.name")
    amount = serializers.DecimalField(max_digits=30, decimal_places=2)
    owner = serializers.SerializerMethodField()
    agency = serializers.SerializerMethodField()
    createdOn = serializers.DateTimeField(source="created_on")

    def get_agency(self, obj):
        if obj.agency is None:
            return None
        return obj.agency.userdetail.name

    def get_serviceName(self, obj):
        if obj.service_detail is None:
            return None
        return obj.service_detail.service.name

    def get_owner(self, obj):
        if obj.owner is None:
            return None
        return f"{obj.owner.userdetail.user.last_name} {obj.owner.userdetail.user.first_name}"

    class Meta:
        model = Transaction
        fields = ['transactionID', 'serviceName', 'amount', 'channel', 'owner', 'agency', 'status', 'createdOn']


class SuperAdminAgencyServiceSerializer(serializers.ModelSerializer):
    serviceDetailId = serializers.IntegerField(source="id")
    name = serializers.CharField()
    # price = serializers.DecimalField(max_digits=20, decimal_places=10)
    # discount = serializers.DecimalField(max_digits=20, decimal_places=10)
    # platformPercent = serializers.DecimalField(source="platform_percent", max_digits=20, decimal_places=2)
    isActive = serializers.BooleanField(source="is_available")
    serviceDetailCode = serializers.CharField(source="service_detail_code")
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if request is None:
            return None
        return request.build_absolute_uri(obj.logo.url)

    class Meta:
        model = ServiceDetail
        fields = ['serviceDetailId', 'name', 'serviceDetailCode', 'logo', 'isActive']


class SuperAdminChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = "__all__"


class VerificationTransactionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    document = serializers.CharField()
    documentId = serializers.CharField(source="document_id", allow_null=True)
    agencyName = serializers.SerializerMethodField()
    amount = serializers.CharField()
    date = serializers.DateTimeField(source="created_on")
    status = serializers.CharField()

    def get_name(self, obj):
        if obj.owner is None:
            return None
        return obj.owner.userdetail.name

    def get_agencyName(self, obj):
        if obj.agency is None:
            return None
        return obj.agency.userdetail.name

    class Meta:
        model = Transaction
        fields = ['id', 'name', 'document', 'documentId', 'agencyName', 'amount', 'date', 'status']


class DashboardBreakDownSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="id")
    agency = serializers.CharField(source="user_detail.name")
    emailAddress = serializers.EmailField(source="user_detail.email")
    revenueGenerated = serializers.SerializerMethodField()
    web = serializers.SerializerMethodField()
    whatsapp = serializers.SerializerMethodField()
    sms = serializers.SerializerMethodField()

    # web # Total money in web has been added.
    # ussd # this will be added once the channel has been added.
    # sms # this will be added once the channel has been added.
    # whatsapp # this will be added once the channel has been added.

    def get_revenueGenerated(self, obj):
        total = 0.0
        query = Transaction.objects.filter(agency=obj.user_detail.user, status="success")
        for transaction in query:
            total += float(transaction.amount)
        return total

    def get_web(self, obj):
        web = Channel.objects.filter(name__icontains='web')
        if web.exists():
            transactions = Transaction.objects.filter(channel=web.last(), agency=obj.user_detail.user)

            amount = 0.0
            for transaction in transactions:
                amount += float(transaction.amount)
            return amount
        else:
            return 0.0

    def get_whatsapp(self, obj):
        web = Channel.objects.filter(name__icontains='whatsapp')
        if web.exists():
            transactions = Transaction.objects.filter(channel=web.last(), agency=obj.user_detail.user)

            amount = 0.0
            for transaction in transactions:
                amount += float(transaction.amount)
            return amount
        else:
            return 0.0

    def get_sms(self, obj):
        sms = Channel.objects.filter(name__icontains='sms')
        if sms.exists():
            transactions = Transaction.objects.filter(channel=sms.last(), agency=obj.user_detail.user)

            amount = 0.0
            for transaction in transactions:
                amount += float(transaction.amount)
            return amount
        else:
            return 0.0

    class Meta:
        model = UserRole
        fields = ['userId', 'agency', 'emailAddress', 'revenueGenerated', 'web', 'whatsapp', 'sms']


class SharedPMandSPAChannelImageSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None

        return request.build_absolute_uri(obj.logo.url)

    class Meta:
        model = Channel
        fields = ['logo']


class SuperAdminExistingAndNonExistingServicesSerializer(serializers.ModelSerializer):
    serviceId = serializers.IntegerField(source="id")
    name = serializers.CharField()
    exists = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    description = serializers.CharField()
    createdOn = serializers.DateTimeField(source="created_on")

    def get_exists(self, obj):
        exists = False
        agency_user_instance = self.context.get('agency_user_instance', None)
        if agency_user_instance is not None:
            service_details = ServiceDetail.objects.filter(agency=agency_user_instance)

            for service_detail in service_details:
                if service_detail.service.id == obj.id:
                    exists = True
                    break
        return exists

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    class Meta:
        model = Service
        # fields = ['serviceId', 'name', 'serviceCode', 'description', 'isActive', 'agency', 'createdOn']
        fields = ['serviceId', 'name', 'logo', 'description', 'exists', 'createdOn']
