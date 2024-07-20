import secrets
from threading import Thread

import requests
from django.shortcuts import get_object_or_404

from util.utils import validate_email, delete_created_instances, phone_number_check, encrypt_text, api_response
from account.models import User, UserDetail, UserRole, State, PaymentGateWay, ClientPaymentGateWayDetail
from verify.payment_modules.tmsass import TmsassPayment
from .serializers import SuperAdminUserCreationSerializer
from django.contrib.auth.hashers import make_password
import ast
from django.conf import settings
from account.emails import partner_manager_account_creation_msg, agency_account_creation_msg


def general_field_check(data):
    """
        Used to perform if repeated fields like firstname, lastname, email are passed in the request body.
        :param data: request.data
        :return: (bool, str)
    """
    first_name = data.get('firstName', None)
    last_name = data.get('lastName', None)
    phone_number = data.get('phoneNumber', None)
    email = data.get('email', None)

    if first_name is None:
        return False, "Error: 'firstName' field is required"

    if last_name is None:
        return False, "Error: 'lastName' field is required"

    if phone_number is None:
        return False, "Error: 'phoneNumber' field is required"

    if email is None:
        return False, "Error: 'email' field is required"

    if not validate_email(email=email):
        return False, "Error: invalid 'email' format"

    if len(phone_number) > 11:
        return False, "Error: incomplete phone number length"

    return True, data


def create_user_type(user_type, data, request):
    """

    """
    user = user_detail = user_role = client_payment_gateway = None
    try:
        first_name: str = data.get('firstName')
        last_name: str = data.get('lastName')
        email: str = data.get('email')
        phone_number = data.get('phoneNumber')

        phone_no_is_clean, response = phone_number_check(phone_number=phone_number)
        if not phone_no_is_clean:
            return False, response

        phone_number = response
        generated_password = f"{secrets.token_urlsafe(6)}A1!{secrets.token_urlsafe(4)}"
        slug = secrets.token_urlsafe(15)

        if user_type == 'agency':
            # ----- Frontend signup process ----
            # Collect details: account-number, bank
            # Call list of banks to fetch all bank names.
            # Call list of banks again to get all bank codes. (For the admin to select the bank code for the entered bank name)
            # Call Account resolution function to confirm if the bank name and code matches.

            user = user_detail = user_role = None
            agency_name = data.get('agencyName', None)
            agency_email = data.get('agencyEmail', None)
            state_id = data.get('stateId', None)
            # payment_gateway_id = data.get('paymentGateWayId', None)  # This ID should be fetched from an API
            # payment_secret_key = data.get('paymentSecretKey', None)  # User enters their payment secret key

            settlement_account = data.get('settlementAccount', None)
            # business_name = data.get('businessName', None)  # Fetched from an API
            bank_account_code = data.get('bankAccountCode', None)  # Fetched from an API # UBA=033
            bank_name = data.get('bankName', None)

            address = data.get('address', None)
            # image = data.get('image', None)
            image = request.FILES.get('image', None)

            if validate_email(agency_email) is False:
                return False, "Invalid 'agencyEmail' format"

            if agency_name is None:
                return False, "'agencyName' field is required"

            # if payment_gateway_id is None:
            #     # Pass in the payment gateway ID, which can be gotten after calling the list all gateway endpoint.
            #     return False, "'paymentId' field is required"

            # if payment_secret_key:
            #     # Hash to payment Secret Key
            #     payment_secret_key = encrypt_text(text=payment_secret_key)

            settlement_account: str = settlement_account
            if settlement_account:
                if not settlement_account.isnumeric():
                    return False, "'bankAccountNumber' field must contain numbers"

                if len(settlement_account) != 10:
                    return False, "'bankAccountNumber' field must be a length of 10"

                # if business_name is None:
                #     return False, "'businessName' field is required"

                if bank_account_code is None:
                    return False, "'bankAccountCode' field is required"

                if bank_name is None:
                    return False, "'bankName' field is required"

            agency_name: str = agency_name.capitalize()

            if state_id is None:
                return False, "'stateId' field is required"

            # Get state by its ID
            state = State.objects.get(id=state_id)
            if address is None:
                return False, "'address' field is required"
            address: str = address.capitalize()

            if image is None:
                return False, "'image' field is required"

            hashed = make_password(password=generated_password)
            user = User.objects.create(email=email, first_name=first_name.capitalize(),
                                       last_name=last_name.capitalize(), password=hashed, slug=slug)

            user_detail = UserDetail.objects.create(user=user, email=agency_email, phone_number=phone_number,
                                                    user_type='agency',
                                                    logo=image, name=agency_name, state=state, address=address,
                                                    created_by=request.user, approved=True)

            user_role = UserRole.objects.create(user_detail=user_detail, user_role='agency')
            user_data = SuperAdminUserCreationSerializer(instance=user_role, context={'request': request}).data

            # ------------ Create default Settlement Payment Account on TMSASS ---------------
            # payment_gateway = get_object_or_404(PaymentGateWay, slug="")

            payment_gateway = PaymentGateWay.objects.get(payment_gateway_slug__iexact="tmsass")
            account_resolution_is_success, account_resolution_data = TmsassPayment.account_resolution(
                account_number=settlement_account, account_code=bank_account_code)

            if account_resolution_is_success is False:
                delete_created_instances(user, user_detail, user_role, client_payment_gateway)
                return False, account_resolution_data

            # Call Create Sub Account endpoint to create a sub_account on paystack and get the 'account_code'.
            stats, response_data = TmsassPayment.create_sub_account(
                settlement_account=settlement_account, bank_code=bank_account_code, business_name=agency_name)

            # If success, collect account_code and settlement bank name
            if not stats:
                delete_created_instances(user, user_detail, user_role, client_payment_gateway)
                return False, response_data

            client_payment_gateway = ClientPaymentGateWayDetail.objects.create(
                user_detail=user_detail, payment_gateway=payment_gateway, settlement_account=settlement_account,
                bank_code=bank_account_code, payment_gateway_is_active=True, account_code=response_data['accountCode'],
                bank_name=response_data['settlementBank'])
        # --------------------- END -----------------------

            # Send email message with password, to the newly created agency.
            agency_account_creation_msg(
                context={"user": user, "password": generated_password, "agency_name": request.user.first_name})

        elif user_type == 'partner-manager':
            agencies = data.get('agencies', [])
            hashed = make_password(password=generated_password)
            user = User.objects.create(first_name=first_name, last_name=last_name, email=email, slug=slug,
                                       password=hashed)
            user_detail = UserDetail.objects.create(user=user, phone_number=phone_number, user_type='platform',
                                                    name=f"{last_name.capitalize()} {first_name.capitalize()}",
                                                    created_by=request.user)
            user_role = UserRole.objects.create(user_detail=user_detail, user_role='partner-manager')

            if agencies:
                agencies = ast.literal_eval(agencies)
                for agency_id in agencies:
                    agency = User.objects.get(id=agency_id)
                    # Add agency to this user's 'manages' field.
                    user_detail.manages.add(agency)

                    # Add agency to this agency's 'managed_by' field.
                    agency.userdetail.managed_by.add(user)

            # Send email message with password, to the newly created agency.
            partner_manager_account_creation_msg(context={"user": user, "password": generated_password})

        user_data = SuperAdminUserCreationSerializer(instance=user_role, context={'request': request}).data

        return True, user_data
    except (Exception,) as err:
        delete_created_instances(user, user_detail, user_role, client_payment_gateway)
        return False, str(err)
