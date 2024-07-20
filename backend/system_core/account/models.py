import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.


class State(models.Model):
    list_id = models.CharField(max_length=30, null=True, blank=True)
    name = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.name}"


USER_TYPE_CHOICES = (
    ('platform', 'Platform'),  # TM30 is the platform user
    ('agency', 'Agency'),  # Users that offers services (F.R.S.C Agency)
    ('individual', 'Individual'),  # Normal individual user / business individual
    ('developer', 'Developer'),  # API Consumers.
    ('corporate-business', 'Corporate-Business')  # corporate business
)


class User(AbstractUser):
    # email = models.EmailField(max_length=200, null=True, blank=True, unique=True)
    email = models.EmailField(max_length=200, null=True, blank=True, unique=True)
    username = models.CharField(max_length=250, null=True, blank=True, unique=True)
    image = models.ImageField(default="default/user.jpg", upload_to="users/", null=True)
    slug = models.SlugField(null=True, blank=True, max_length=350, unique=True)
    super_admin_has_reset_password = models.BooleanField(default=False, null=True)
    push_notification = models.BooleanField(default=True, null=True)
    otp_expire = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']  # Fields that are required when creating a user from the Terminal

    def __str__(self):
        return f"{self.first_name} - {self.email}"


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=200, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True, unique=True)

    # email = models.EmailField(max_length=200, unique=True, null=True, blank=True, help_text="Agency's email")
    user_type = models.CharField(max_length=35, choices=USER_TYPE_CHOICES, null=True, blank=True)
    name = models.CharField(max_length=252, null=True, blank=True, help_text="Agency, Sub-Agency, "
                                                                             "Business, Individual ... "
                                                                             "names")
    logo = models.ImageField(default="default/user.jpg", upload_to="logos/", null=True)
    parent_agency = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name="parent_agency",
                                      help_text="Field to hold the parent agency that created this sub agency.")

    # platform_percentage = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True,
    #                                            help_text="TM30 percentage for the service") # No need for this now.
    sub_agency_percentage = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True,
                                                help_text="TM30 percentage for the service")  # This is the Sub Agency's percentage after every Successful transaction.
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    approved = models.BooleanField(default=False)  # Approve Agency created by managers.
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="creator",
                                   help_text="Who created this Sub Agency")
    managed_by = models.ManyToManyField(User, blank=True, related_name="managers",
                                        help_text="Expects a partner manager user profile to manage this Agency Profile")  # for agencies
    manages = models.ManyToManyField(User, blank=True, related_name="manages",
                                     help_text="This field contains who this User Detail (Partner Manager) manages")
    # business_type = models.CharField(max_length=20, null=True, blank=True, help_text="For businesses")
    business_size = models.IntegerField(default=0, null=True, blank=True, help_text="For businesses")
    reg_number = models.CharField(max_length=150, null=True, blank=True, help_text="For businesses")
    cac_number = models.CharField(max_length=150, null=True, blank=True, help_text="For businesses")
    business_email = models.EmailField(max_length=100, null=True, unique=True, blank=True, help_text="For businesses")

    # activate_business = models.BooleanField(default=False)
    address = models.CharField(max_length=500, null=True, blank=True, help_text="General Address")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_type} - {self.name}"

    def image_url(self):
        return self.image.url


USER_ROLE = (
    ("super-admin", "Super-Admin"),  # TM30 Super admin user.
    ('partner-manager', 'Partner-Manager'),  # TM30 partner manager role.
    ('individual', 'Individual'),  # Normal individual user / business individual role
    ('developer', 'Developer'),  # Normal individual user / business individual role
    ("agency", "Agency"),  # Agencies created by the Agencies.
    ("sub-agency", "Sub-Agency"),  # Agencies created by the Agencies.
    ("corporate-business", "Corporate-Business"),  # Business.
    ('sub-corporate-business', 'Sub-Corporate-Business')
)  # A user created by the business admin


class UserRole(models.Model):
    user_detail = models.OneToOneField(UserDetail, on_delete=models.CASCADE, null=True)
    user_role = models.CharField(max_length=100, choices=USER_ROLE, default="super-admin")
    # Should also have a permission field.
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User-Detail-ID: {self.user_detail.id} - {self.user_role}"


class Channel(models.Model):
    """
        More details can come in here.
    """
    name = models.CharField(max_length=50, null=True, blank=True, unique=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    logo = models.ImageField(default="default/user.jpg", upload_to="channels/", null=True)
    is_active = models.BooleanField(default=True, help_text="Tells if this channel is available for use.")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} Channel - {self.is_active}"


TRANSACTION_STATUSES = (
    ('pending', 'Pending'),
    ('success', 'Success'),
    # ('canceled' , 'Canceled'),
    ('failed', 'Failed')
)

SERVICE_TYPE = (
    ('paid', 'Paid'),
    ('free', 'Free')
)


class Service(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True, unique=True)
    description = models.TextField(null=True, blank=True)
    # service_code = models.CharField(max_length=20, null=True, blank=True)
    activate = models.BooleanField(default=True, help_text="Tells if this service is available for use. i.e Services "
                                                           "can be deactivated.")
    logo = models.ImageField(default="default/user.jpg", upload_to="service/", null=True)

    # agency = models.ManyToManyField(User, help_text="If agencies can have more than 1 "
    #                                                 "service.")
    # service_type = models.CharField(max_length=50, choices=SERVICE_TYPE, default="paid", null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"


class ServiceDetail(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    agency = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # This field 'parent_agency' is only used to save the parent agency that creates a sub-agency, while the 'agency' field on this model while then be used to save the 'sub-agency'.
    # Note: This swap in field only applies to the process of sub-agency creation. other than that, the 'agency' field stores the agency.While the 'parent_agency' field is useeless.
    parent_agency = models.ForeignKey(UserDetail, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True, unique=True)
    logo = models.ImageField(default="default/user.jpg", upload_to="service/", null=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE, default="paid", null=True, blank=True)
    domain_url = models.CharField(max_length=200, default="", null=True, blank=True,
                                  help_text="This field is used to hold the url of an agency, needed in V2.")
    service_detail_code = models.CharField(help_text="A unique identifier for this agency used for identifying what "
                                                     "logic to be run when this service detail is selected.",
                                           max_length=20, null=True, blank=True)
    price = models.DecimalField(max_digits=200, decimal_places=2, default=0.00, null=True, blank=True)
    added_amount = models.DecimalField(max_digits=200, decimal_places=2, default=0.00, null=True, blank=True,
                                       help_text="This is an extra amount added by a sub agency, this amount would be "
                                                 "added to the 'price' (price + added_amount) field in this model, "
                                                 "which reveals the total amount a sub-agency is offering the service "
                                                 "to consumers")
    discount = models.DecimalField(max_digits=200, decimal_places=2, default=0.00, null=True, blank=True, help_text="In percentage")
    description = models.TextField(null=True, blank=True)
    platform_percent = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True,
                                           help_text="TM30 percentage for the service")
    is_available = models.BooleanField(default=True, help_text="Tells if this service is available for use. i.e "
                                                               "Services can be deactivated.")
    channel_available = models.ManyToManyField(Channel, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Service Detail'} - {self.is_available} - {self.agency}"


# ---------
PAYMENT_TYPE = (
    ('online', 'Online'),
    ('offline', 'Offline')
)

class PaymentGateWay(models.Model):
    payment_gateway_name = models.CharField(max_length=100, null=True, blank=True)
    payment_gateway_type = models.CharField(choices=PAYMENT_TYPE, max_length=100, default="online", blank=True)
    payment_gateway_logo = models.ImageField(default="default/cash.png", upload_to="payments/", null=True)
    payment_gateway_slug = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.payment_gateway_name} - {self.payment_gateway_name}"


PAYMENT_SUB_TYPE = (
    ('direct', 'Direct'), # This 'sub-type' can only be selected with the 'on-line' type ->
    ('split', 'Split') #
)


class ClientPaymentGateWayDetail(models.Model):
    user_detail = models.ForeignKey(UserDetail, on_delete=models.CASCADE, blank=True, null=True)
    payment_gateway = models.ForeignKey(PaymentGateWay, on_delete=models.CASCADE)
    payment_gateway_is_active = models.BooleanField(default=False)

    # payment_type = models.CharField(max_length=500, default="online", blank=True)
    secret_key = models.CharField(max_length=500, null=True, blank=True, help_text="Used to authenticate request and "
                                                                                   "should be kept secret. Can also "
                                                                                   "store TMSASS 'client_id'")

    settlement_account = models.CharField(max_length=20, null=True, blank=True, unique=True)
    select_sub_type = models.CharField(max_length=20, choices=PAYMENT_SUB_TYPE, null=True, blank=True, unique=True, default='split')
    bank_code = models.CharField(max_length=200, null=True, blank=True, unique=True, help_text="UBA = 033")
    bank_name = models.CharField(max_length=200, null=True, blank=True, unique=True, help_text="UBA")
    account_code = models.CharField(max_length=200, null=True, blank=True, unique=True,
                                    help_text="A token used for making payment to the account number attached to "
                                              "this model. Mostly used for TMSASS")

    # ----- Offline Details ------
    offline_bank_account_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    offline_bank_account_owner_name = models.CharField(max_length=200, null=True, blank=True, unique=True)
    offline_bank_name = models.CharField(max_length=200, null=True, blank=True, unique=True)

    slug = models.SlugField(blank=True, null=True, max_length=100, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_detail.user.first_name} - {self.user_detail.user_type}"


class Transaction(models.Model):
    payment_detail = models.ForeignKey(ClientPaymentGateWayDetail, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    service_detail = models.ForeignKey(ServiceDetail, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True, choices=TRANSACTION_STATUSES)
    reference_number = models.CharField(max_length=200, null=True, blank=True, help_text="VerifyPro Transaction Ref.")
    document = models.CharField(max_length=100, null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    document_id = models.CharField(max_length=250, null=True, blank=True)
    payment_method = models.CharField(max_length=200, null=True, blank=True)
    payment_id = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=200, null=True, blank=True)
    verification_number = models.CharField(max_length=200, null=True, blank=True)
    agency = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="agency",
                               help_text='Agency service used.')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              help_text='Who made this transaction')
    payload = models.JSONField(default=dict)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.email is None or self.phone_number is None:
            return f"{self.agency} {self.channel.name} {self.status}"
        return f"{self.email} {self.phone_number} {self.channel.name}"
