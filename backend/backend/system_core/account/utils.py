import logging, re, secrets, requests, json
import random

from django.contrib.auth.hashers import make_password
from util.utils import validate_email, api_response
from .emails import account_creation_msg, account_verification_msg
from .models import User, UserDetail, UserRole, Transaction
from .models import State
from util.utils import delete_created_instances, phone_number_check
from django.conf import settings
from threading import Thread


def add_states():
    try:
        NIGERIA_STATES = [
            {
                "state_id": 1,
                "state_name": "ABIA"
            },
            {
                "state_id": 2,
                "state_name": "ABUJA"
            },
            {
                "state_id": 3,
                "state_name": "ADAMAWA"
            },
            {
                "state_id": 4,
                "state_name": "AKWA IBOM"
            },
            {
                "state_id": 5,
                "state_name": "ANAMBRA"
            },
            {
                "state_id": 6,
                "state_name": "BAUCHI"
            },
            {
                "state_id": 7,
                "state_name": "BAYELSA"
            },
            {
                "state_id": 8,
                "state_name": "BENUE"
            },
            {
                "state_id": 9,
                "state_name": "BORNO"
            },
            {
                "state_id": 10,
                "state_name": "CROSS RIVER"
            },
            {
                "state_id": 11,
                "state_name": "DELTA"
            },
            {
                "state_id": 12,
                "state_name": "EBONYI"
            },
            {
                "state_id": 13,
                "state_name": "EDO"
            },
            {
                "state_id": 14,
                "state_name": "EKITI"
            },
            {
                "state_id": 15,
                "state_name": "ENUGU"
            },
            {
                "state_id": 16,
                "state_name": "GOMBE"
            },
            {
                "state_id": 17,
                "state_name": "IMO"
            },
            {
                "state_id": 18,
                "state_name": "JIGAWA"
            },
            {
                "state_id": 19,
                "state_name": "KADUNA"
            },
            {
                "state_id": 20,
                "state_name": "KANO"
            },
            {
                "state_id": 21,
                "state_name": "KATSINA"
            },
            {
                "state_id": 22,
                "state_name": "KEBBI"
            },
            {
                "state_id": 23,
                "state_name": "KOGI"
            },
            {
                "state_id": 24,
                "state_name": "KWARA"
            },
            {
                "state_id": 25,
                "state_name": "LAGOS"
            },
            {
                "state_id": 26,
                "state_name": "NASSARAWA"
            },
            {
                "state_id": 27,
                "state_name": "NIGER"
            },
            {
                "state_id": 28,
                "state_name": "OGUN"
            },
            {
                "state_id": 29,
                "state_name": "ONDO"
            },
            {
                "state_id": 30,
                "state_name": "OSUN"
            },
            {
                "state_id": 31,
                "state_name": "OYO"
            },
            {
                "state_id": 32,
                "state_name": "PLATEAU"
            },
            {
                "state_id": 33,
                "state_name": "RIVERS"
            },
            {
                "state_id": 34,
                "state_name": "SOKOTO"
            },
            {
                "state_id": 35,
                "state_name": "TARABA"
            },
            {
                "state_id": 36,
                "state_name": "YOBE"
            },
            {
                "state_id": 37,
                "state_name": "ZAMFARA"
            }
        ]
        for state in NIGERIA_STATES:
            if State.objects.filter(list_id=state['state_id']).exists():
                continue
            State.objects.create(list_id=state['state_id'], name=state['state_name'])

        return True, f"Successfully added all {len(NIGERIA_STATES)} states"
    except (Exception,) as err:
        return False, f"{err}"


def password_checker(password: str):
    try:
        # Python program to check validation of password
        # Module of regular expression is used with search()

        flag = 0
        while True:
            if len(password) < 8:
                flag = -1
                break
            elif not re.search("[a-z]", password):
                flag = -1
                break
            elif not re.search("[A-Z]", password):
                flag = -1
                break
            elif not re.search("[0-9]", password):
                flag = -1
                break
            elif not re.search("[#!_@$-]", password):
                flag = -1
                break
            elif re.search("\s", password):
                flag = -1
                break
            else:
                flag = 0
                break

        if flag == 0:
            return True, "Valid Password"

        return False, "Password must contain uppercase, lowercase letters, '# ! - _ @ $' special characters " \
                      "and 8 or more characters"
    except (Exception,) as err:
        return False, f"{err}"


def send_email_notification(subject: str, recipients, sender, content, html_string: str):
    try:
        """
        recipients: comma separated values.
        """
        # base_url: str = f"{settings.EMAIL_SERVICE_BASE_URL}"
        CLIENT_ID: str = f"{settings.CLIENT_ID}"

        url = "https://services.tm30.net/notifications/v1/email"
        payload = {
            "html": html_string,
            "type": "custom",
            "subject": subject,
            "recipients": recipients,
            "provider": "mailgun",
            "content": content,
            "from": sender
        }
        headers = {
            'Accept': 'application/json',
            'client-id': CLIENT_ID,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 201 or response.status_code == 200:
            logging.error(msg={"emailServiceResponse": response.json(), "statusCode": response.status_code})
            return True, response.json()

        logging.error(msg={"emailServiceResponse": response.json(), "statusCode": response.status_code})
        return False, response.json()

    except (Exception,) as err:
        return False, f"{err}"


def business_cac_check_on_registration(cac_number, business_type):
    try:

        url = "https://vapi.verifyme.ng/v1/verifications/identities/cac"

        payload = json.dumps({
            "type": business_type,
            "rcNumber": cac_number
        })
        headers = {
            'Authorization': f'Bearer {settings.VERIFY_ME_BASE_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 201 or response.json()['status'] == 'success':
            api_response(message='Successful CAC Check', data=response.json(), status=True)
            return True, 'Successful CAC Check'

        api_response(message='Failed CAC Check', data=response.json(), status=False)
        return False, "Failed CAC Check"
    except (Exception, ) as err:
        return False


def create_account(request):
    user, user_detail, user_role = None, None, None
    transaction_added_msg = ''
    try:
        data = request.data.get('data', {})
        account_type: str = data.get('accountType', None)

        if account_type is None or account_type.lower() not in ['individual', 'corporate-business', 'developer']:
            return False, "Invalid 'accountType' value"

        first_name: str = data.get('firstName', None)
        business_name: str = data.get('businessName', None)
        last_name: str = data.get('lastName', None)
        phone_number: str = data.get('phoneNumber', None)
        email: str = data.get('email', None)
        business_address: str = data.get('businessAddress', None)
        cac_number: str = data.get('cacNumber', None)
        password: str = data.get('password', None)
        confirm_password: str = data.get('confirmPassword', None)
        transaction_id: str = data.get('transactionId', None)

        if not first_name:
            return False, "'firstName' field is required"

        if not last_name:
            return False, "'lastName' field is required"

        # ---------- Phone Number Check ---------------
        if not phone_number:
            return False, "'phoneNumber' field is required"

        valid_number, phone_number = phone_number_check(phone_number=phone_number)
        if not valid_number:
            return False, phone_number  # 'phone_number' in this case is an error message

        # ---------- Email Check ---------------
        if validate_email(email) is False:
            return False, "Invalid 'email' format"

        # ---------- Password Check ---------------
        if not password or not confirm_password:
            return False, "'password' and 'confirmPassword' fields are required"

        if password != confirm_password:
            return False, "Passwords does not match"

        success, msg = password_checker(password=password)
        if not success:
            return False, msg

        user = user_detail = user_role = None
        if account_type == "individual":
            slug = secrets.token_urlsafe(15)
            user = User.objects.create(email=email, slug=slug, first_name=first_name.capitalize(),
                                       last_name=last_name.capitalize(),
                                       password=make_password(password=password))
            user_detail = UserDetail.objects.create(user=user, phone_number=phone_number, user_type=account_type,
                                                    name=f"{last_name.capitalize()} {first_name.capitalize()}")
            user_role = UserRole.objects.create(user_detail=user_detail, user_role="individual")

        elif account_type == "developer":
            slug = secrets.token_urlsafe(15)
            user = User.objects.create(email=email, slug=slug, first_name=first_name.capitalize(),
                                       last_name=last_name.capitalize(),
                                       password=make_password(password=password))
            user_detail = UserDetail.objects.create(user=user, phone_number=phone_number, user_type=account_type,
                                                    name=f"{last_name.capitalize()} {first_name.capitalize()}")
            user_role = UserRole.objects.create(user_detail=user_detail, user_role="developer")

        elif account_type == "corporate-business":
            if not business_name:
                return False, "'businessName' field is required"

            if not business_address:
                return False, "'businessAddress' field is required"

            if not cac_number:
                return False, "'cacNumber' field is required"

            # Check CAC:
            # - Needs to call the CAC check API to verify business API.

            user = User.objects.create(email=email, first_name=first_name, last_name=last_name,
                                       password=make_password(password=password))
            user_detail = UserDetail.objects.create(user=user, phone_number=phone_number, user_type=account_type,
                                                    name=business_name.capitalize(), business_email=email,
                                                    address=business_address, cac_number=cac_number)
            user_role = UserRole.objects.create(user_detail=user_detail, user_role="corporate-business")

        if user_role is not None:
            # Send Verification mail
            account_verification_msg(context={"user": user})

            # ---- Merge Transaction to this newly created account ----
            transaction = Transaction.objects.filter(id=transaction_id)

            if transaction.exists():
                transaction_added_msg = "!"
                transaction = Transaction.objects.get(id=transaction_id)
                transaction.owner = user
                transaction.save()

            return True, f"Account has been created successfully{transaction_added_msg}"

    except(Exception,) as err:
        # if "duplicate key value violates unique constraint" in str(err):  # Would remove this later on
        #     return False, "An account with this email already exists"
        delete_created_instances(user, user_role, user_detail)
        return False, f"{err}"


def service_selection_algo(service_detail_ids, **kwargs) -> int:
    random_integer = random.randint(1, len(service_detail_ids))
    return service_detail_ids[random_integer-1]
