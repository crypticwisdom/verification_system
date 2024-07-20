import json
import secrets
import ast

import requests
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from account.models import User, UserDetail, UserRole, Service, State, Channel, Transaction, ServiceDetail, \
    ClientPaymentGateWayDetail
from util.paginations import CustomPagination
from util.utils import api_response, incoming_request_checks,  encrypt_text, decrypt_text
from verify import utils
from verify.payment_modules import tmsass


# Create your views here.


class IWebProcessorView(APIView, CustomPagination):
    permission_classes = []

    def post(self, request):
        try:
            data = {}
            success, data = incoming_request_checks(request=request, require_data_field=True)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            service_detail_id = data.get("serviceDetailId", None)
            service_detail_code = data.get("serviceDetailCode", None)
            # user_id = data.get("userId", None)
            service_type = data.get("type", None) #  optional field
            payment_redirect_url = data.get("paymentRedirectUrl", None)
            channel_id = data.get('channelId', None)

            if not service_detail_id:
                return Response(api_response(message=f"'serviceDetailId' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not payment_redirect_url:
                return Response(api_response(message=f"'paymentRedirectUrl' is required a field", status=False), status=status.HTTP_400_BAD_REQUEST)

            if not channel_id:
                return api_response(message=f"'channelId' is required a field", status=False)

            channel = get_object_or_404(Channel, pk=channel_id)

            if not service_detail_code:
                return Response(api_response(message=f"'serviceDetailCode' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            # Get ServiceDetail with datas from the request body.
            service_detail = ServiceDetail.objects.filter(id=service_detail_id,
                                                          service_detail_code=service_detail_code)

            if not service_detail.exists():
                return Response(api_response(message=f"Service not found", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            service_detail = service_detail.last()

            # --------------- Voter's Card Verification Logic (VerifyMe - done) ------------------
            if service_detail.service_detail_code == "5O6G&8uStOlRA":
                vin = data.get('id', None)

                if vin is None:
                    return Response(api_response(message=f"'id' field is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                # ========= STEP 2: Generate transaction reference ===========
                transaction_ref = secrets.token_urlsafe(40)

                transaction = Transaction.objects.create(
                    reference_number=transaction_ref, status="pending", service_detail=service_detail, channel=channel)

                if request.user.is_authenticated:
                    owner = request.user
                    transaction.owner = owner
                    transaction.save()

                # save payload
                payload = {
                    "data": dict(data),
                    "service_detail_id": service_detail.id,
                    "transaction_id": transaction.id,
                    "request_id": request.user.id if request.user.is_authenticated else None
                }

                transaction.payload = encrypt_text(text=payload)
                transaction.save()

                if service_detail.service_type == "free":

                    # Call VerifyMe
                    response = utils.verify_me_voters_card_verification(
                        service_detail=service_detail, data=data, request=request, transaction=transaction)

                    # ---- 500 ----
                    if len(response) == 3 and response[2] == 500 and response[0] is False:
                        return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    # ---- 404 ----
                    if len(response) == 3 and response[2] == 404 and response[0] is False:
                        return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                    # ---- 400 ----
                    if len(response) == 3 and response[2] == 400 and response[0] is False:
                        return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                    # ---- 200 ----
                    if len(response) == 3 and response[2] == 200 and response[0] is True:
                        return Response(response[1])

                elif service_detail.service_type == "paid":
                    # Make payment Section

                    # 1. Check what payment gateway this agency has set for transaction.
                    #     - Fetch all ClientPaymentGateWays.
                    #     - Check which of them has been made active. Note that by default the payment gateway
                    #      that was provided during Agency Registration is active. And there will be an update page.

                    fetch_clients_gateways = ClientPaymentGateWayDetail.objects.filter(
                        user_detail=service_detail.agency.userdetail, payment_gateway_is_active=True)

                    client_gateway = None
                    if not fetch_clients_gateways.exists():
                        # NOTE: if client doesn't have an active payment gateway, we can then use TMSASS as a default
                        # payment gateway, which now means that every agency needs to provide their 'sub-account' number

                        # This case is likely not to happen, an agency must have to set a payment gateway.
                        return Response(
                            api_response(message=f"The agency of this service has no payment gateway set",
                                         status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) > 1:
                        return Response(api_response(message=f"This agency has more than 1 payment gateway set",
                                                     status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) == 1:
                        client_gateway: ClientPaymentGateWayDetail = fetch_clients_gateways.last()
                        transaction.payment_detail = client_gateway
                        transaction.save()

                    # 2. Make payment calculation.
                    service_price = float(service_detail.price)
                    platform_percent = float(service_detail.platform_percent)

                    # Make sure 'discount' is greater than 0 before 'platform_percent' price can be calculated.
                    if platform_percent > 0:  # if True, then discount > 0.0; calculate discount

                        # Calculate platforms shares.
                        platform_share = (platform_percent / 100) * service_price

                        # ----------
                        # Perform a check, if service does not belong to TMSASS, you can split money to the owner
                        # of the service.
                        # - It is best to split this payment after users' transaction is successful.
                        # - Can also be a separate program that is performed by a cron job.
                        ...
                        # --------

                        # Since 'platform_percent' is in percentage. E.g: 3.2
                        service_price = service_price - platform_share

                    # Initialize payment function
                    success, response_data = tmsass.TmsassPayment.initialize_payment(
                        amount=service_price,
                        email=request.user.email if request.user.is_authenticated else None,
                        reference=transaction_ref,
                        payment_redirect_url=payment_redirect_url,
                        account_code=transaction.payment_detail.account_code
                    )
                    if not success:
                        return Response(api_response(message=f"Error: Initializing payment", status=False,
                                                     data=response_data), status=status.HTTP_400_BAD_REQUEST)

                    return Response(
                        api_response(message=f"Payment has been initialized", status=True, data=response_data['data']))

                else:
                    return Response(
                        api_response(message="Something went wrong during Voter's Card Number Verification",
                                     status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

            # ------------------- BVN (VerifyMe - done) -----------------
            elif service_detail.service_detail_code == "DgYd&8KcLhJLY":  # Platform: 'Verify Me'
                """ 
                    DATA PRE-CHECKS
                    - create transaction reference.
                    - save 'transaction reference' and 'encrypted payload' to Transaction instance.
                    - Check if service is paid or free.
                      - if free then call verifyMe (Service) Direct.
                      - else: make payment.
                        * Initialize payment
                            - send initialize response to frontend.
                            
                        
                        Another endpoint will be created for payment completion.
                        - verify payment status.
                        - If failed: return failed status to frontend.
                        - Else: call verifyMe endpoint and return response to frontend
                """
                # ========= STEP 1: DATA PRE-CHECKS ===========
                """
                    Perform checks on verification details like, 'id' so we dont call the payment API with incorrect or 
                    Improper details.
                """
                bvn = data.get('id', None)

                if bvn is None:
                    return Response(api_response(message=f"'id' field is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)
                bvn = str(bvn)
                if len(bvn) != 11:
                    return Response(api_response(message=f"BVN number must be 11 digits", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                # ========= STEP 2: Generate transaction reference ===========
                transaction_ref = secrets.token_urlsafe(40)

                transaction = Transaction.objects.create(
                    reference_number=transaction_ref, status="pending", service_detail=service_detail,
                    channel=channel)

                if request.user.is_authenticated:
                    owner = request.user
                    transaction.owner = owner
                    transaction.save()

                # save payload
                payload = {
                    "data": dict(data),
                    "service_detail_id": service_detail.id,
                    "transaction_id": transaction.id,
                    "request_id": request.user.id if request.user.is_authenticated else None
                }

                transaction.payload = encrypt_text(text=payload)
                transaction.save()

                response = utils.verify_me_bvn_verification(
                    service_detail=service_detail,
                    data=data, request=request,
                    transaction=transaction
                )

                # ---- 500 ----
                if len(response) == 3 and response[2] == 500 and response[0] is False:
                    return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # ---- 404 ----
                if len(response) == 3 and response[2] == 404 and response[0] is False:
                    return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                # ---- 400 ----
                if len(response) == 3 and response[2] == 400 and response[0] is False:
                    return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                # ---- 200 ----
                if len(response) == 3 and response[2] == 200 and response[0] is True:

                    if service_detail.service_type == "free":

                        # Call VerifyMe
                        return Response(response[1])

                    elif service_detail.service_type == "paid":
                        # Make payment section

                        # 1. Check what payment gateway this agency has set for transaction.
                        #     - Fetch all ClientPaymentGateWays.
                        #     - Check which of them has been made active. Note that by default the payment gateway
                        #      that was provided during Agency Registration is active. And there will be an update page.

                        fetch_clients_gateways = ClientPaymentGateWayDetail.objects.filter(
                            user_detail=service_detail.agency.userdetail, payment_gateway_is_active=True)

                        if service_detail.agency.userdetail.userrole.user_role == "sub-agency":
                            fetch_clients_gateways = ClientPaymentGateWayDetail.objects.filter(
                                user_detail=service_detail.parent_agency, payment_gateway_is_active=True)

                        if not fetch_clients_gateways.exists():
                            # NOTE: if client doesn't have an active payment gateway, we can then use TMSASS as a default
                            # payment gateway, which now means that every agency needs to provide their 'sub-account' number

                            # This case is likely not to happen, an agency must have to set a payment gateway.
                            return Response(
                                api_response(message=f"The agency of this service has no payment gateway set",
                                             status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                        elif len(fetch_clients_gateways) > 1:
                            return Response(api_response(message=f"This agency has more than 1 payment gateway set",
                                                         status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                        elif len(fetch_clients_gateways) == 1:
                            client_gateway: ClientPaymentGateWayDetail = fetch_clients_gateways.last()
                            transaction.payment_detail = client_gateway
                            transaction.save()

                        # 2. Make payment calculation.
                        service_price = float(service_detail.price)
                        platform_percent = float(service_detail.platform_percent)

                        # Make sure 'discount' is greater than 0 before 'platform_percent' price can be calculated.
                        if platform_percent > 0:  # if True, then discount > 0.0; calculate discount

                            # Calculate platforms shares.
                            platform_share = (platform_percent / 100) * service_price

                            # ----------
                            # Perform a check, if service does not belong to TMSASS, you can split money to the owner
                            # of the service.
                            # - It is best to split this payment after users' transaction is successful.
                            # - Can also be a separate program that is performed by a cron job.
                            ...
                            # --------

                            # Since 'platform_percent' is in percentage. E.g: 3.2
                            service_price = service_price - platform_share

                        # Initialize payment function
                        success, response_data = tmsass.TmsassPayment.initialize_payment(amount=service_price,
                                                                                         email=request.user.email if request.user.is_authenticated else None,
                                                                                         reference=transaction_ref,
                                                                                         payment_redirect_url=payment_redirect_url,
                                                                                         account_code=transaction.payment_detail.account_code)

                        if not success:
                            return Response(api_response(message=f"Error: Initializing payment", status=False,
                                                         data=response_data), status=status.HTTP_400_BAD_REQUEST)

                        return Response(
                            api_response(message=f"Payment has been initialized", status=True, data=response_data['data']))

                else:
                    return Response(
                        api_response(message="Something went wrong during B.V.N Verification", status=False,
                                     data={}), status=status.HTTP_400_BAD_REQUEST)

            # ------------------- CAC (VerifyMe - done) -----------------
            elif service_detail.service_detail_code == "QR0U&8qvnVUJU":
                # Platform: 'Verify Me'
                """ 
                    - DATA PRE-CHECKS
                    - create transaction reference.
                    - save 'transaction reference' and 'encrypted payload' to Transaction instance.
                    - Check if service is paid or free.
                      - if free then call verifyMe (Service) Direct.
                      - else: make payment.
                        * Initialize payment
                            - send initialize response to frontend.


                        Another endpoint will be created for payment completion.
                        - verify payment status.
                        - If failed: return failed status to frontend.
                        - Else: call verifyMe endpoint and return response to frontend
                """
                # ========= STEP 1: DATA PRE-CHECKS ===========
                """
                    Perform checks on verification details like, 'id' so we dont call the payment API with incorrect or 
                    Improper details.
                """
                cac = data.get('id', None)

                if cac is None:
                    return Response(api_response(message=f"'id' field is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)
                # bvn = str(bvn)
                # if len(bvn) != 11:
                #     return Response(api_response(message=f"BVN number must be 11 digits", status=False),
                #                     status=status.HTTP_400_BAD_REQUEST)

                # ========= STEP 2: Generate transaction reference ===========
                transaction_ref = secrets.token_urlsafe(40)

                transaction = Transaction.objects.create(
                    reference_number=transaction_ref, status="pending", service_detail=service_detail,
                    channel=channel)

                if request.user.is_authenticated:
                    owner = request.user
                    transaction.owner = owner
                    transaction.save()

                # save payload
                payload = {
                    "data": dict(data),
                    "service_detail_id": service_detail.id,
                    "transaction_id": transaction.id,
                    "request_id": request.user.id if request.user.is_authenticated else None
                }

                transaction.payload = encrypt_text(text=payload)
                transaction.save()

                if service_detail.service_type == "free":
                    # Call VerifyMe
                    response = utils.verify_me_corporate_affairs_commission_verification(
                        service_detail=service_detail, data=data, request=request, transaction=transaction)

                    # ---- 500 ----
                    if len(response) == 3 and response[2] == 500 and response[0] is False:
                        return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    # ---- 404 ----
                    if len(response) == 3 and response[2] == 404 and response[0] is False:
                        return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                    # ---- 400 ----
                    if len(response) == 3 and response[2] == 400 and response[0] is False:
                        return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                    # ---- 200 ----
                    if len(response) == 3 and response[2] == 200 and response[0] is True:
                        return Response(response[1])

                elif service_detail.service_type == "paid":
                    # Make payment Section

                    # 1. Check what payment gateway this agency has set for transaction.
                    #     - Fetch all ClientPaymentGateWays.
                    #     - Check which of them has been made active. Note that by default the payment gateway
                    #      that was provided during Agency Registration is active. And there will be an update page.

                    fetch_clients_gateways = ClientPaymentGateWayDetail.objects.filter(
                        user_detail=service_detail.agency.userdetail, payment_gateway_is_active=True)

                    if not fetch_clients_gateways.exists():
                        # NOTE: if client doesn't have an active payment gateway, we can then use TMSASS as a default
                        # payment gateway, which now means that every agency needs to provide their 'sub-account' number

                        # This case is likely not to happen, an agency must have to set a payment gateway.
                        return Response(
                            api_response(message=f"The agency of this service has no payment gateway set",
                                         status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) > 1:
                        return Response(api_response(message=f"This agency has more than 1 payment gateway set",
                                                     status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) == 1:
                        client_gateway: ClientPaymentGateWayDetail = fetch_clients_gateways.last()
                        transaction.payment_detail = client_gateway
                        transaction.save()

                    # 2. Make payment calculation.
                    service_price = float(service_detail.price)
                    platform_percent = float(service_detail.platform_percent)

                    # Make sure 'discount' is greater than 0 before 'platform_percent' price can be calculated.
                    if platform_percent > 0:  # if True, then discount > 0.0; calculate discount

                        # Calculate platforms shares.
                        platform_share = (platform_percent / 100) * service_price

                        # ----------
                        # Perform a check, if service does not belong to TMSASS, you can split money to the owner
                        # of the service.
                        # - It is best to split this payment after users' transaction is successful.
                        # - Can also be a separate program that is performed by a cron job.
                        ...
                        # --------

                        # Since 'platform_percent' is in percentage. E.g: 3.2
                        service_price = service_price - platform_share

                    # Initialize payment function
                    success, response_data = tmsass.TmsassPayment.initialize_payment(amount=service_price,
                                                                                     email=request.user.email if request.user.is_authenticated else None,
                                                                                     reference=transaction_ref,
                                                                                     payment_redirect_url=payment_redirect_url,
                                                                                     account_code=transaction.payment_detail.account_code
                                                                                     )

                    if not success:
                        return Response(api_response(message=f"Error: Initializing payment", status=False,
                                                     data=response_data), status=status.HTTP_400_BAD_REQUEST)

                    return Response(
                        api_response(message=f"Payment has been initialized", status=True, data=response_data['data']))

                else:
                    return Response(
                        api_response(message="Something went wrong during C.A.C Verification", status=False,
                                     data={}), status=status.HTTP_400_BAD_REQUEST)

            # ------------------- TIN (VerifyMe - done) -----------------
            elif service_detail.service_detail_code == "zJWQ&8istscV4":

                # Platform: 'Verify Me'
                """ 
                    - DATA PRE-CHECKS
                    - create transaction reference.
                    - save 'transaction reference' and 'encrypted payload' to Transaction instance.
                    - Check if service is paid or free.
                      - if free then call verifyMe (Service) Direct.
                      - else: make payment.
                        * Initialize payment
                            - send initialize response to frontend.


                        Another endpoint will be created for payment completion.
                        - verify payment status.
                        - If failed: return failed status to frontend.
                        - Else: call verifyMe endpoint and return response to frontend
                """
                # ========= STEP 1: DATA PRE-CHECKS ===========
                """
                    Perform checks on verification details like, 'id' so we dont call the payment API with incorrect or 
                    Improper details.
                """
                tin = data.get('id', None)

                if tin is None:
                    return Response(api_response(message=f"'id' field is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                # ========= STEP 2: Generate transaction reference ===========
                transaction_ref = secrets.token_urlsafe(40)

                transaction = Transaction.objects.create(
                    reference_number=transaction_ref, status="pending", service_detail=service_detail,
                    channel=channel)

                if request.user.is_authenticated:
                    owner = request.user
                    transaction.owner = owner
                    transaction.save()

                # save payload
                payload = {
                    "data": dict(data),
                    "service_detail_id": service_detail.id,
                    "transaction_id": transaction.id,
                    "request_id": request.user.id if request.user.is_authenticated else None
                }

                transaction.payload = encrypt_text(text=payload)
                transaction.save()

                if service_detail.service_type == "free":
                    # Call VerifyMe
                    response = utils.verify_me_tax_identification_number(
                        service_detail=service_detail, data=data, request=request, transaction=transaction)

                    # ---- 500 ----
                    if len(response) == 3 and response[2] == 500 and response[0] is False:
                        return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    # ---- 404 ----
                    if len(response) == 3 and response[2] == 404 and response[0] is False:
                        return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                    # ---- 400 ----
                    if len(response) == 3 and response[2] == 400 and response[0] is False:
                        return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                    # ---- 200 ----
                    if len(response) == 3 and response[2] == 200 and response[0] is True:
                        return Response(response[1])

                elif service_detail.service_type == "paid":
                    # Make payment Section

                    # 1. Check what payment gateway this agency has set for transaction.
                    #     - Fetch all ClientPaymentGateWays.
                    #     - Check which of them has been made active. Note that by default the payment gateway
                    #      that was provided during Agency Registration is active. And there will be an update page.

                    fetch_clients_gateways = ClientPaymentGateWayDetail.objects.filter(
                        user_detail=service_detail.agency.userdetail, payment_gateway_is_active=True)

                    if not fetch_clients_gateways.exists():
                        # NOTE: if client doesn't have an active payment gateway, we can then use TMSASS as a default
                        # payment gateway, which now means that every agency needs to provide their 'sub-account' number

                        # This case is likely not to happen, an agency must have to set a payment gateway.
                        return Response(
                            api_response(message=f"The agency of this service has no payment gateway set",
                                         status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) > 1:
                        return Response(api_response(message=f"This agency has more than 1 payment gateway set",
                                                     status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) == 1:
                        client_gateway: ClientPaymentGateWayDetail = fetch_clients_gateways.last()
                        transaction.payment_detail = client_gateway
                        transaction.save()

                    # 2. Make payment calculation.
                    service_price = float(service_detail.price)
                    platform_percent = float(service_detail.platform_percent)

                    # Make sure 'discount' is greater than 0 before 'platform_percent' price can be calculated.
                    if platform_percent > 0:  # if True, then discount > 0.0; calculate discount

                        # Calculate platforms shares.
                        platform_share = (platform_percent / 100) * service_price

                        # ----------
                        # Perform a check, if service does not belong to TMSASS, you can split money to the owner
                        # of the service.
                        # - It is best to split this payment after users' transaction is successful.
                        # - Can also be a separate program that is performed by a cron job.
                        ...
                        # --------

                        # Since 'platform_percent' is in percentage. E.g: 3.2
                        service_price = service_price - platform_share

                    # Initialize payment function
                    success, response_data = tmsass.TmsassPayment.initialize_payment(amount=service_price,
                                                                                     email=request.user.email if request.user.is_authenticated else None,
                                                                                     reference=transaction_ref,
                                                                                     payment_redirect_url=payment_redirect_url,
                                                                                     account_code=transaction.payment_detail.account_code
                                                                                     )

                    if not success:
                        return Response(api_response(message=f"Error: Initializing payment", status=False,
                                                     data=response_data), status=status.HTTP_400_BAD_REQUEST)

                    return Response(
                        api_response(message=f"Payment has been initialized", status=True, data=response_data['data']))

                else:
                    return Response(
                        api_response(message="Something went wrong during T.I.N Verification", status=False,
                                     data={}), status=status.HTTP_400_BAD_REQUEST)

            # ------------------- Driver's License (VerifyMe - done) ----------------------
            elif service_detail.service_detail_code == "Yake&8DAHZkiw":
                driver_license = data.get('id', None)

                if driver_license is None:
                    return Response(api_response(message=f"'id' field is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                # ========= STEP 2: Generate transaction reference ===========
                transaction_ref = secrets.token_urlsafe(40)

                transaction = Transaction.objects.create(
                    reference_number=transaction_ref, status="pending", service_detail=service_detail,
                    channel=channel)

                if request.user.is_authenticated:
                    owner = request.user
                    transaction.owner = owner
                    transaction.save()

                # save payload
                payload = {
                    "data": dict(data),
                    "service_detail_id": service_detail.id,
                    "transaction_id": transaction.id,
                    "request_id": request.user.id if request.user.is_authenticated else None
                }

                transaction.payload = encrypt_text(text=payload)
                transaction.save()

                if service_detail.service_type == "free":
                    # Call VerifyMe
                    response = utils.verify_me_drivers_license(
                        service_detail=service_detail, data=data, request=request, transaction=transaction)

                    # ---- 500 ----
                    if len(response) == 3 and response[2] == 500 and response[0] is False:
                        return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    # ---- 404 ----
                    if len(response) == 3 and response[2] == 404 and response[0] is False:
                        return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                    # ---- 400 ----
                    if len(response) == 3 and response[2] == 400 and response[0] is False:
                        return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                    # ---- 200 ----
                    if len(response) == 3 and response[2] == 200 and response[0] is True:
                        return Response(response[1])

                elif service_detail.service_type == "paid":
                    # Make payment Section

                    # 1. Check what payment gateway this agency has set for transaction.
                    #     - Fetch all ClientPaymentGateWays.
                    #     - Check which of them has been made active. Note that by default the payment gateway
                    #      that was provided during Agency Registration is active. And there will be an update page.

                    fetch_clients_gateways = ClientPaymentGateWayDetail.objects.filter(
                        user_detail=service_detail.agency.userdetail, payment_gateway_is_active=True)

                    if not fetch_clients_gateways.exists():
                        # NOTE: if client doesn't have an active payment gateway, we can then use TMSASS as a default
                        # payment gateway, which now means that every agency needs to provide their 'sub-account' number

                        # This case is likely not to happen, an agency must have to set a payment gateway.
                        return Response(
                            api_response(message=f"The agency of this service has no payment gateway set",
                                         status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) > 1:
                        return Response(api_response(message=f"This agency has more than 1 payment gateway set",
                                                     status=False, data={}), status=status.HTTP_400_BAD_REQUEST)

                    elif len(fetch_clients_gateways) == 1:
                        client_gateway: ClientPaymentGateWayDetail = fetch_clients_gateways.last()
                        transaction.payment_detail = client_gateway
                        transaction.save()

                    # 2. Make payment calculation.
                    service_price = float(service_detail.price)
                    platform_percent = float(service_detail.platform_percent)

                    # Make sure 'discount' is greater than 0 before 'platform_percent' price can be calculated.
                    if platform_percent > 0:  # if True, then discount > 0.0; calculate discount

                        # Calculate platforms shares.
                        platform_share = (platform_percent / 100) * service_price

                        # ----------
                        # Perform a check, if service does not belong to TMSASS, you can split money to the owner
                        # of the service.
                        # - It is best to split this payment after users' transaction is successful.
                        # - Can also be a separate program that is performed by a cron job.
                        ...
                        # --------

                        # Since 'platform_percent' is in percentage. E.g: 3.2
                        service_price = service_price - platform_share

                    # Initialize payment function
                    success, response_data = tmsass.TmsassPayment.initialize_payment(amount=service_price,
                                                                                     email=request.user.email if request.user.is_authenticated else None,
                                                                                     reference=transaction_ref,
                                                                                     payment_redirect_url=payment_redirect_url,
                                                                                     account_code=transaction.payment_detail.account_code)

                    if not success:
                        return Response(api_response(message=f"Error: Initializing payment", status=False,
                                                     data=response_data), status=status.HTTP_400_BAD_REQUEST)

                    return Response(
                        api_response(message=f"Payment has been initialized", status=True, data=response_data['data']))

                else:
                    return Response(
                        api_response(message="Something went wrong during Driver's License Verification", status=False,
                                     data={}), status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message=f"Error: Something went wrong", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)
        except (Exception, ) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class VerifyTransactionView(APIView):
    permission_classes = []
    """
        This view is used for verifying transaction status for different payments gateways.
    """
    def post(self, request):
        try:
            success, data = incoming_request_checks(request=request, require_data_field=True)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            transaction_reference = data.get('transactionReference', None)

            if transaction_reference is None:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            # ----------------- Verify Transaction ----------------
            # Get Transaction record with the 'transaction_reference' and a pending status
            transaction = Transaction.objects.filter(reference_number=transaction_reference, status="pending")
            if not transaction.exists():
                return Response(
                    api_response(message="Error: Transaction record is invalid", status=False,
                                 data={}), status=status.HTTP_400_BAD_REQUEST)

            # If the system finds a single transaction with that 'reference'.
            if len(transaction) == 1:
                transaction = transaction.last()

                # Since this platform can support many payment option, so payment initialization might have been
                # done with other payment options. So I need to check the transaction's payment gateway used.

                # transaction record is found and status is success
                if transaction.status == "success":
                    return Response(
                        api_response(message="This is a previous successful transaction", status=False,
                                     data={}), status=status.HTTP_400_BAD_REQUEST)

                elif transaction.status == "failed":
                    return Response(
                        api_response(message="This is a previous failed-transaction", status=False,
                                     data={}), status=status.HTTP_400_BAD_REQUEST)

                # If transaction record status is pending
                # "proper time to call transaction verification status" because on payment initialization a
                # pending status was given to the transaction.
                elif transaction.status == "pending":

                    # Integrate payment verification for each payment method. E.G tmsass
                    if transaction.payment_detail.payment_gateway.payment_gateway_slug == "tmsass":

                        verify_status, msg, verify_data = tmsass.TmsassPayment.verify_payment(
                            reference=transaction_reference)

                        if not verify_status:
                            return Response(
                                api_response(message=msg, status=False, data=verify_data),
                                status=status.HTTP_400_BAD_REQUEST)

                        # Fetch Transaction record
                        decrypted_trxn_payload = decrypt_text(text=transaction.payload)

                        # Convert the decrypted 'decrypted_trxn_payload' from String to Dictionary.
                        transaction_payload = ast.literal_eval(decrypted_trxn_payload)

                        # service_detail_code = transaction_payload['data']['serviceDetailCode']
                        service_detail_id = transaction_payload['data']['serviceDetailId']
                        service_detail_ = get_object_or_404(ServiceDetail, pk=service_detail_id)

                        data_ = transaction_payload['data']

                        # ====== VERIFYME BVN - Done just checked========
                        if service_detail_.service_detail_code == "DgYd&8KcLhJLY":
                            # Call VerifyMe
                            response = utils.verify_me_bvn_verification(
                                service_detail=service_detail_, data=data_, request=request,
                                transaction=transaction)

                            # ---- 500 ----
                            if len(response) == 3 and response[2] == 500 and response[0] is False:
                                return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                            # ---- 404 ----
                            if len(response) == 3 and response[2] == 404 and response[0] is False:
                                return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                            # ---- 400 ----
                            if len(response) == 3 and response[2] == 400 and response[0] is False:
                                return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                            # ---- 200 ----
                            if len(response) == 3 and response[2] == 200 and response[0] is True:
                                return Response(response[1])

                            return Response(
                                api_response(message=msg, status=True, data=verify_data))

                        # ====== VERIFYME Voters Card VERIFICATION - Done just checked =========
                        elif service_detail_.service_detail_code == "5O6G&8uStOlRA":
                            # Call VerifyMe
                            response = utils.verify_me_voters_card_verification(
                                service_detail=service_detail_, data=data_, request=request, transaction=transaction)

                            # ---- 500 ----
                            if len(response) == 3 and response[2] == 500 and response[0] is False:
                                return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                            # ---- 404 ----
                            if len(response) == 3 and response[2] == 404 and response[0] is False:
                                return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                            # ---- 400 ----
                            if len(response) == 3 and response[2] == 400 and response[0] is False:
                                return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                            # ---- 200 ----
                            if len(response) == 3 and response[2] == 200 and response[0] is True:
                                return Response(response[1])

                            return Response(
                                api_response(message=msg, status=True, data=verify_data))

                        # ====== CAC (VerifyMe - Done just checked) ======
                        elif service_detail_.service_detail_code == "QR0U&8qvnVUJU":
                            response = utils.verify_me_corporate_affairs_commission_verification(
                                service_detail=service_detail_, data=data_, request=request, transaction=transaction)

                            # ---- 500 ----
                            if len(response) == 3 and response[2] == 500 and response[0] is False:
                                return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                            # ---- 404 ----
                            if len(response) == 3 and response[2] == 404 and response[0] is False:
                                return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                            # ---- 400 ----
                            if len(response) == 3 and response[2] == 400 and response[0] is False:
                                return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                            # ---- 200 ----
                            if len(response) == 3 and response[2] == 200 and response[0] is True:
                                return Response(response[1])

                            return Response(
                                api_response(message=msg, status=True, data=verify_data))

                        # ====== T.I.N (VerifyMe - Done just checked) ======
                        elif service_detail_.service_detail_code == "zJWQ&8istscV4":
                            response = utils.verify_me_tax_identification_number(
                                service_detail=service_detail_, data=data_, request=request, transaction=transaction)

                            # ---- 500 ----
                            if len(response) == 3 and response[2] == 500 and response[0] is False:
                                return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                            # ---- 404 ----
                            if len(response) == 3 and response[2] == 404 and response[0] is False:
                                return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                            # ---- 400 ----
                            if len(response) == 3 and response[2] == 400 and response[0] is False:
                                return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                            # ---- 200 ----
                            if len(response) == 3 and response[2] == 200 and response[0] is True:
                                return Response(response[1])

                            return Response(
                                api_response(message=msg, status=True, data=verify_data))

                        # ====== Driver's License Verification (VerifyMe - Done just checked) ======
                        elif service_detail_.service_detail_code == "Yake&8DAHZkiw":
                            response = utils.verify_me_drivers_license(
                                service_detail=service_detail_, data=data_, request=request, transaction=transaction)

                            # ---- 500 ----
                            if len(response) == 3 and response[2] == 500 and response[0] is False:
                                return Response(response[1], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                            # ---- 404 ----
                            if len(response) == 3 and response[2] == 404 and response[0] is False:
                                return Response(response[1], status=status.HTTP_404_NOT_FOUND)

                            # ---- 400 ----
                            if len(response) == 3 and response[2] == 400 and response[0] is False:
                                return Response(response[1], status=status.HTTP_400_BAD_REQUEST)

                            # ---- 200 ----
                            if len(response) == 3 and response[2] == 200 and response[0] is True:
                                return Response(response[1])

                            return Response(
                                api_response(message=msg, status=True, data=verify_data))

            elif len(transaction) > 1:
                return Response(
                    api_response(message="Error: Duplicate transaction record found", status=False,
                                 data={}), status=status.HTTP_400_BAD_REQUEST)
        # ---------------- End of Verification ----------------

        except (Exception, ) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

