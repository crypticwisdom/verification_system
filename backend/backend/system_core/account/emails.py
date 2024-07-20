import logging
from threading import Thread
# from account.utils import send_email_notification
from django.conf import settings
from util.utils import api_response

from account.models import ServiceDetail

FROM_EMAIL = settings.FROM_EMAIL
SUPPORT_EMAIL = settings.SUPPORT_EMAIL


# Has been Implemented
def partner_manager_account_creation_msg(context: dict):
    user = context.get("user", None)
    password = context.get("password", None)
    url = f"{settings.FRONTEND_PASSWORD_RESET_BASE_URL}/{user.slug}"
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {user.first_name or "Partner Manger"}</b>,<br>

We are pleased to inform you that your Partner Manager’s account has been created successfully. 
As a partner manager, you will have access to the dashboard of the agencies that have been assigned to you, which will help you manage their accounts efficiently.<br>

Your account has been set up with the following login credentials: <br>
Email: {user.email}
Temporary Password: {password}<br>


Please click <a href='{url}' title="URL">Here</a> to reset your default password.
Please note that you will be required to change your password the first time you log in to your account. 
To do this, simply follow the instructions provided in the system.<br>

If you have any questions or concerns, please don’t hesitate to reach out to our customer team. We’re here to help you 
through the verification process and make sure that you’re satisfied with your experience.<br><br>

Best Regards,
The VerifyPro Team
    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Your Partner Manager Account Has Been Created",
                       "recipients": user.email, "sender": f"{FROM_EMAIL}", "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}'", status=False)


# Has been Implemented
def account_creation_msg(context: dict):
    user = context.get("user", None)
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {user.first_name}</b>,<br>

Welcome to VerifyPro!

We’re glad you’ve chosen to verify your identity with us. Our goal is to make the verification process as easy and 
secure as possible and to give you the peace of mind that comes with knowing your identity is protected. 

We take your privacy very seriously, and we use the latest technology and security measure to ensure that your 
information is safe.

If you have any questions or concerns, please don’t hesitate to reach out to our customer team. We’re here to help you 
through the verification process and make sure that you’re satisfied with your experience. 

Thank you or choosing to verify your identity with us. We appreciate your trust and look forward to serving you. 

Best Regards,
The VerifyPro Team
    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Welcome Note",
                       "recipients": user.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}'", status=False)


# Has been Implemented
def account_verification_msg(context: dict):
    user = context.get("user", None)
    url = settings.FRONTEND_ACCT_ACTIVATION_URL
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {user.first_name}</b>,<br>

Welcome to VerifyPro!

We're so glad you've joined the platform and we hope you enjoy our services. It's just a few more steps to verify your email.
To continue setting up your VerifyPro account, please <a href='{url}/{user.slug}' title="Activate Account">verify that this is your email address</a>.

If you did not make this request, please disregard this email. For help, contact us through our Help Center.

Best Regards,
The VerifyPro Team
    </pre>
    </div>
    </body>
    """

    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Account Activation",
                       "recipients": user.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()

        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}'", status=False)


# Has been Implemented
def welcome_msg(context: dict):
    user = context.get("user", None)
    message = f"""
    <body>
    <div>
    <pre>
    
<b>Dear {user.first_name}</b>,<br>

Welcome to VerifyPro! 

We’re glad you’ve chosen to verify your identity with us. Our goal is to make the verification process as easy and 
secure as possible and to give you the peace of mind that comes with knowing your identity is protected. 

We take your privacy very seriously, and we use the latest technology and security measure to ensure that your information is safe. 

If you have any questions or concerns, please don’t hesitate to reach out to our customer team. We’re here to help you 
through the verification process and make sure that you’re satisfied with your experience. 

Thank you for choosing to verify your identity with us. We appreciate your trust and look forward to serving you. 

Best Regards,
The VerifyPro Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Welcome Note",
                       "recipients": user.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}'", status=False)


# Has not been Implemented
def agency_approval_by_super_admin_msg(context: dict):
    user = context.get("user", None)
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {user.first_name}</b>,<br>
Hello! 

Kindly be informed that an Agency has been created and requires your approval. 
Kindly approve and activate their account and provide them with the necessary credentials to access the platform. 

Best Regards,
The VerifyPro Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "AGENCY APPROVAL",
                       "recipients": user.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}'", status=False)


# Has been Implemented but haven't replaced the 'xxxx' part
def service_activation_msg(context: dict):
    service_detail = context.get("service_detail", None)
    SUPPORT_EMAIL = settings.SUPPORT_EMAIL
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {service_detail.agency.first_name}</b>,<br>
 
Please be informed that your {service_detail.service.name} has been activated.
If you have any questions or concerns regarding this action, please don’t hesitate to reach out to us at {SUPPORT_EMAIL}.
 
Best Regards, 
The VerifyPro Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "SERVICE ACTIVATION",
                       "recipients": service_detail.agency.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()

        api_response(message=f"Successfully sent mail to '{service_detail.agency.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {service_detail}", status=False)


# Has been Implemented but haven't replaced the 'xxxx' part
def service_deactivation_msg(context: dict):
    service_detail = context.get("service_detail", None)
    reason = context.get("reason", None)
    SUPPORT_EMAIL = settings.SUPPORT_EMAIL
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {service_detail.agency.first_name}</b>,<br>
 
Please be informed that your {service_detail.service.name} has been de-activated.
If you have any questions or concerns regarding this action, please don’t hesitate to reach out to us at {SUPPORT_EMAIL}.
 
Best Regards, 
The VerifyPro Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "SERVICE DEACTIVATION",
                       "recipients": service_detail.agency.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()

        api_response(message=f"Successfully sent mail to '{service_detail.agency.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {service_detail}", status=False)


# Has been Implemented
def service_addition_mail(context: dict):
    service_detail = context.get("service_detail", None)
    agency = context.get("agency", None)
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {agency.first_name}</b>,<br>

Please be informed that a new service has been added to your list of services.
 
To access {service_detail.name} Please click the link below and log in with your credentials. 
 
If you have any issues logging in or have any questions regarding the service, please don’t hesitate to reach out to our 
support team at {SUPPORT_EMAIL}. 
 
Best Regards,
The VerifyPro Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "A SERVICE HAS BEEN ADDED TO YOU!",
                       "recipients": agency.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()

        api_response(message=f"Successfully sent mail to '{agency.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {agency}", status=False)


# Has been Implemented.
def agency_account_creation_msg(context: dict):
    user = context.get("user", None)
    password = context.get("password", None)
    agency_name = context.get("agency_name", None)
    url = f"{settings.FRONTEND_PASSWORD_RESET_BASE_URL}/{user.slug}"
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {user.first_name or "Agency"}</b>,<br>

We are pleased to inform you that your Agency account has been successfully created on our platform. Your login credentials are as follows:

Email: {user.email}
Temporary Password: {password}<br>
Login Link: <a href='{url}' title="URL">Platform URL</a>

Please keep these details safe and confidential as they are important for accessing your account. We recommend that you 
change your password immediately after logging in to ensure the security of your account.

You can now access your account by visiting <a href='{url}' title="URL">Platform URL</a> and entering your login credentials.

If you have any questions or concerns regarding your account, please feel free to reach out to our customer support team at [Contact Information].

Best regards,
{agency_name}
    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Your Agency Account Has Been Created",
                       "recipients": user.email, "sender": f"{FROM_EMAIL}", "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {user}", status=False)


# Has been Implemented.
def sub_agency_account_creation_msg(context: dict):
    user = context.get("user", None)
    password = context.get("password", None)
    url = f"{settings.FRONTEND_PASSWORD_RESET_BASE_URL}/{user.slug}"
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {user.first_name or "Sub Agency"}</b>,<br>

We are pleased to inform you that your account has been successfully created on our platform. Your login credentials are as follows:

Email: {user.email}
Temporal Password: {password}

Please keep these details safe and confidential as they are important for accessing your account. We recommend that you change your password immediately after logging in to ensure the security of your account.

You can now access your account by visiting <a href='{url}' title="URL">Here</a> and entering your login credentials.

If you have any questions or concerns regarding your account, please feel free to reach out to our customer support team at [Contact Information].

Best regards,
{user.userdetail.parent_agency.userdetail.name}

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Your Sub Agency Account Has Been Created",
                       "recipients": user.email, "sender": f"{FROM_EMAIL}", "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {user}", status=False)


# Has been Implemented.
# All users.
def forgot_password_mail(context: dict):
    user = context.get("user", None)
    url = f"{settings.FRONTEND_FORGOT_PASSWORD_URL}/{user.slug}"

    message = f"""
    <body>
    <div>
    <pre>
<b>Hi, {user.first_name}</b>,<br>

Looks like you requested a password reset. Please click on <a href='{url}' title="URL">HERE</a> to reset the password 
for your VerifyPro account.


Didn’t make this request? Please ignore this email or change your password for extra security.
Note: This link is valid for 10 minutes from the time it was sent to you and can only be used once.

Best Regards,

VerifyPro Support Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": "Forgot Password",
                       "recipients": user.email, "sender": f"{FROM_EMAIL}", "content": "content",
                       "html_string": message}).start()
        api_response(message=f"Successfully sent mail to '{user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {user}", status=False)


# Has been Implemented.
def sub_agency_service_addition_mail(context: dict):
    sub_agency_user = context.get("sub_agency_user", None)
    service_detail_ids = context.get("service_detail_ids", None)
    l = []
    for service_detail_id in service_detail_ids:
        service = ServiceDetail.objects.get(id=service_detail_id)
        l.append(service.name)
    names = ", ".join(l)

    to_plural = "some new services" if len(service_detail_ids) > 1 else "a new service"
    subject_message = "SOME SERVICES HAS BEEN ADDED TO YOU!" if len(service_detail_ids) > 1 else "A SERVICE HAS BEEN ADDED TO YOU!"
    message = f"""
    <body>
    <div>
    <pre>
<b>Dear {sub_agency_user.first_name}</b>,<br>

Please be informed that {to_plural} has been added to your list of services.

To access  Please click the link below and log in with your credentials. 

If you have any issues logging in or have any questions regarding the service(s), please don’t hesitate to reach out to our 
support team at {SUPPORT_EMAIL}. 

Best Regards,
The VerifyPro Team

    </pre>
    </div>
    </body>
    """
    try:
        from account.utils import send_email_notification
        Thread(target=send_email_notification,
               kwargs={"subject": subject_message,
                       "recipients": sub_agency_user.email, "sender": FROM_EMAIL, "content": "content",
                       "html_string": message}).start()

        api_response(message=f"Successfully sent mail to '{sub_agency_user.email}'", status=True)
    except (Exception,) as err:
        api_response(message=f"'{err}' --- {sub_agency_user}", status=False)


