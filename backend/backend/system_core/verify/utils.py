import json

import requests
from django.conf import settings
from util.utils import api_response, encrypt_text


def create_transaction_record(response: dict, service_detail, request, success_type: str, amount: float, document: str,
                              document_id: str, verification_number: str, **kwargs):
    try:
        # Create Transaction record for both Authenticated and Unauthenticated users
        transaction = kwargs.get('transaction', None)
        # channel_id = kwargs.get('channel_id', None)

        if transaction is None:
            return False, "Transaction record not found"

        transaction.status = success_type
        transaction.amount = amount
        transaction.document = document
        transaction.document_id = document_id
        transaction.agency = service_detail.agency
        transaction.verification_number = verification_number
        transaction.full_name = kwargs.get('full_name', 'N/A')
        transaction_id = transaction.id

        transaction.save()
        print(transaction.success_type, transaction.id, '---ds', )
        return True, transaction_id
    except (Exception,) as err1:
        try:
            if transaction is not None:
                transaction.delete()
        except (Exception, ) as err2:
            return False, None
        return False, None


# Implemented (Done)
def verify_me_bvn_verification(service_detail, transaction, data, request):
    """
        This block of code handles Bank Verification Number.
    """
    try:
        bvn = data.get('id', None)
        hashed_bvn = encrypt_text(text=bvn)

        if not bvn:
            return False, api_response(message=f"'id' is required a field for BVN Verification", status=False), 400

        HEADERS = {"Authorization": f"Bearer {settings.VERIFY_ME_BASE_TOKEN}", "Content-Type": "application/json"}
        request_response = requests.request("POST",
                                            url=f"{settings.VERIFY_ME_BASE_URL}/v1/verifications/identities/bvn/{bvn}",
                                            headers=HEADERS)

        # report error message from verify me server
        if request_response.status_code == 500:
            return False, api_response(message=f"Error: Connecting to third-party's server", status=False,
                                       data=data), 500

        # 400 - Bad Request
        if request_response.status_code == 400:
            api_response(message=request_response.json(), status=False)
            return False, api_response(message=request_response.json()['message'], status=False), 400

        # ------------- 404 (Failed) -------------
        if request_response.status_code == 404:
            response_data: dict = request_response.json()
            response = api_response(message=f"BVN details not found", status=False,
                                    data=response_data)

            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="failed", document_id="N/A",
                                                                document="Bank Verification Number",
                                                                verification_number=hashed_bvn,
                                                                full_name="N/A", transaction=transaction)
            print(transaction_id, transaction.id)
            response = dict(response) if type(response) == dict else response
            response.update({"transactionId": transaction_id})
            return False, response, 404

        # ------------- 200 / 201 (Success) -------------
        if (request_response.status_code == 200 or request_response.status_code == 201) and request_response.json()[
            'status'] == 'success':
            response_data: dict = request_response.json()

            # Log response from 3rd party
            api_response(message=f"Successfully verified BVN number", data=request_response.json(), status=True)

            response_data_key: dict = response_data.get('data', None)

            if response_data_key is None:
                return False, api_response(message=f"Empty data field from response", status=False,
                                           data=data), 400

            bvn = response_data_key['bvn']
            first_name = response_data_key['firstname']
            last_name = response_data_key['lastname']
            middle_name = response_data_key['middlename']
            birth_date = response_data_key['birthdate']
            phone = response_data_key['phone']
            api_response(message=f"Empty data field from response", status=False,
                         data=response_data_key)
            # These are remaining responses that gets returned from this service provider with live credentials.
            photo = None if response_data_key.get('photo', None) is None else response_data_key['photo']
            marital_status = None if response_data_key.get('maritalStatus', None) is None else response_data_key[
                'maritalStatus']
            lga_of_residence = None if response_data_key.get('lgaOfResidence', None) is None else response_data_key[
                'lgaOfResidence']
            lga_of_origin = None if response_data_key.get('lgaOfOrigin', None) is None else response_data_key[
                'lgaOfOrigin']
            residential_address = None if response_data_key.get('residentialAddress', None) is None else \
                response_data_key['residentialAddress']
            state_of_origin = None if response_data_key.get('stateOfOrigin', None) is None else response_data_key[
                'stateOfOrigin']
            enrollment_bank = None if response_data_key.get('enrollmentBank', None) is None else response_data_key[
                'enrollmentBank']
            enrollment_branch = None if response_data_key.get('enrollmentBranch', None) is None else response_data_key[
                'enrollmentBranch']
            name_on_card = None if response_data_key.get('nameOnCard', None) is None else response_data_key[
                'nameOnCard']
            title = None if response_data_key.get('title', None) is None else response_data_key['title']
            level_of_account = None if response_data_key.get('levelOfAccount', None) is None else response_data_key[
                'levelOfAccount']

            container = {"BVN": bvn, "First Name": first_name, "Last Name": last_name, "Middle Name": middle_name,
                         "Birth Date": birth_date, "Phone": phone, "Marital Status": marital_status,
                         "LGA Of Residence": lga_of_residence, "LGA Of Origin": lga_of_origin,
                         "Residential Address": residential_address, "State Of Origin": state_of_origin,
                         "Enrollment Bank": enrollment_bank, "Enrollment Branch": enrollment_branch,
                         "Name On Card": name_on_card, "Title": title, "Level Of Account": level_of_account, "Photo": photo}

            response = api_response(message=f"Successfully verified BVN number", data=container, status=True)

            success, transaction_id = create_transaction_record(response, service_detail, request,
                                                                success_type="success", amount=service_detail.price,
                                                                document="Bank Verification Number",
                                                                document_id=response_data_key.get('id', "N/A"),
                                                                verification_number=hashed_bvn,
                                                                transaction=transaction,
                                                                full_name=f"{last_name} {first_name}")

            response = dict(response) if type(response) == dict else response
            response.update({"transactionId": transaction_id})
            return True, response, 200

        response = api_response(message="An error occurred during BVN verification",
                                data=request_response.json(),
                                status=False)
        response = dict(response) if type(response) == dict else response
        return False, response, 400

    except (Exception,) as err:
        return False, api_response(message=f"{err}", status=False, data={}), 400


# Implemented (Done, reformatted response)
def verify_me_voters_card_verification(service_detail, data, request, transaction):
    """
        This block of code handles Voter's Card Verification Number.
    """
    response_data_key = None
    try:
        voter_card_id = data.get('id', None)
        hashed_voter_card_id = encrypt_text(text=voter_card_id)
        if voter_card_id is None:
            return False, api_response(message=f"'id' is required for Voter's Card Verification", status=False), 400

        channel_id = data.get('channelId', None)
        if not channel_id:
            return False, api_response(message=f"'channelId' is required a field", status=False), 400

        HEADERS = {"Authorization": f"Bearer {settings.VERIFY_ME_BASE_TOKEN}", "Content-Type": "application/json"}
        DATA = json.dumps({
            "dob": "1900-01-01"  # e.g: 1998-01-10
        })
        request_response = requests.request("POST",
                                            url=f"{settings.VERIFY_ME_BASE_URL}/v1/verifications/identities/vin/{voter_card_id}",
                                            headers=HEADERS, data=DATA)
        # ---------- 500 --------------
        if request_response.status_code == 500:
            return False, api_response(message=f"Error: Connecting to third-party's server", status=False,
                                       data=data), 500

        # ------------- 400 - Bad Request --------
        if request_response.status_code == 400:
            api_response(message=request_response.json(), status=False)
            return False, api_response(message=request_response.json()['message'], status=False), 400

        # ------------- 404 (Failed) -------------
        if request_response.status_code == 404:
            response_data: dict = request_response.json()

            response = api_response(message=f"Voter's Card details not found", status=False,
                                    data=response_data)

            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="failed", document_id="N/A",
                                                                document="Voter's card verification",
                                                                verification_number=hashed_voter_card_id,
                                                                full_name="N/A", channel_id=channel_id,
                                                                transaction=transaction)
            response = dict(response) if type(response) is dict else response
            response.update({"transactionId": transaction_id})
            return False, response, 404

        # ------------- 200 / 201 ----------------
        if (request_response.status_code == 200 or request_response.status_code == 201) and request_response.json()[
            'status'] == 'success':
            response_data: dict = request_response.json()

            # log response
            api_response(message=f"Successfully verified Voter's card number", data=response_data,
                         status=True)

            response_data_key: dict = response_data.get('data', None)

            if response_data_key is None:
                return False, api_response(message=f"Empty 'data' field from response", status=False,
                                           data=request_response.json())

            # Re-Format api response
            reformat_response = {
                "ID": response_data_key.get('id', 'N/A'),
                "First Name": response_data_key.get('firstName', 'N/A'),
                "Last Name": response_data_key.get('lastName', 'N/A'),
                "Full Name": response_data_key.get('fullname', 'N/A'),
                "VIN": response_data_key.get('vin', 'N/A'),
                "Gender": response_data_key.get('gender', 'N/A'),
                "Occupation": response_data_key.get('occupation', 'N/A'),
                "Polling Unit Code": response_data_key.get('pollingUnitCode', 'N/A'),
            }
            response = api_response(message=f"Successfully verified Voter's Card Details", status=True,
                                    data=reformat_response)
            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="success",
                                                                document="Voters Card Verification",
                                                                document_id=response_data_key.get('id', "N/A"),
                                                                verification_number=hashed_voter_card_id,
                                                                full_name=f"{response_data_key.get('fullname', 'N/A')}",
                                                                channel_id=channel_id, transaction=transaction)
            response = dict(response) if type(response) is dict else response
            response.update({"transactionId": transaction_id})
            return True, response, 200

        response = api_response(message=f"An error occurred during Voter's card verification verification",
                                data=request_response.json(), status=False)
        response = dict(response) if type(response) == dict else response
        return False, response, 400
    except (Exception,) as err:
        return False, api_response(message=f"{err}", status=False, data={}), 400


# Implemented (Done, reformatted response)
def verify_me_corporate_affairs_commission_verification(service_detail, data, request, transaction):
    """
        This block of code handles Corporate Affairs Commission Verification.
    """
    try:
        business_type = data.get('type', None)
        rc_number = data.get('id', None)
        hashed_rc_number = encrypt_text(text=rc_number)

        if not all([business_type, rc_number]):
            return False, api_response(message=f"'businessType', 'id' are required "
                                               f"fields for Corporate Affairs Commission Verification", status=False), 400

        channel_id = data.get('channelId', None)
        if not channel_id:
            return False, api_response(message=f"'channelId' is required a field", status=False), 400

        HEADERS = {"Authorization": f"Bearer {settings.VERIFY_ME_BASE_TOKEN}", "Content-Type": "application/json"}
        DATA = json.dumps({
            "type": f"{business_type}",  # limited_company, business, incorporated_trustee.
            "rcNumber": rc_number
        })

        request_response = requests.request("POST",
                                            url=f"{settings.VERIFY_ME_BASE_URL}/v1/verifications/identities/cac",
                                            headers=HEADERS, data=DATA)

        # ----------- 500 (Third Party Error) ------------
        if request_response.status_code == 500:
            return False, api_response(message=f"Error: Connecting to third-party's server", status=False, data=data), 500

        # ------------- 404 (Failed to be changed to 'Invalid') -------------
        if request_response.status_code == 404:
            response_data: dict = request_response.json()

            response = api_response(message=f"Corporate Affairs Commission details not found", status=False,
                                    data=response_data)

            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="failed", document_id="N/A",
                                                                document="Corporate Affairs Commission",
                                                                verification_number=hashed_rc_number,
                                                                full_name=response_data.get('companyName', 'N/A'),
                                                                channel_id=channel_id, transaction=transaction
                                                                )
            response = dict(response) if type(response) is dict else response
            response.update({"transactionId": transaction_id})
            return False, response, 404

        # -------------- 400 - Bad Request -------------
        if request_response.status_code == 400:
            api_response(message=request_response.json(), status=False)
            return False, api_response(message=request_response.json()['message'], status=False), 400

        # ------------- 200 / 201 (Success) --------------------
        if (request_response.status_code == 200 or request_response.status_code == 201) and request_response.json()[
            'status'] == 'success':
            response_data: dict = request_response.json()

            # Log response
            api_response(message=f"CAC response", status=False,
                         data=response_data)

            response_data_key: dict = response_data.get('data', None)

            if response_data_key is None:
                return False, api_response(message=f"Empty 'data' field from response", status=False,
                                           data=request_response.json()), 400

            response = api_response(message=f"Successfully verified Corporate Affairs Commission Details", status=True,
                                    data=response_data_key)
            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="success", document_id=response_data_key.get('id', "N/A"),
                                                                document="Corporate Affairs Commission",
                                                                verification_number=hashed_rc_number,
                                                                full_name=response_data_key.get('companyName', 'N/A'),
                                                                channel_id=channel_id, transaction=transaction)

            response = dict(response) if type(response) is dict else response
            response.update({"transactionId": transaction_id})
            return True, response, 200

        response = api_response(message=f"An error occurred during Corporate Affairs Commission verification",
                                data=request_response.json(), status=False)
        response = dict(response) if type(response) is dict else response
        return False, response, 400
    except (Exception,) as err:
        return False, api_response(message=f"{err}", status=False, data={}), 400


# Implemented (Done, reformatted response)
def verify_me_tax_identification_number(service_detail, data, request, transaction):
    """
        This block of code handles Tax Identification Number.
    """
    try:
        tin = data.get('id', None)
        hashed_tin = encrypt_text(text=tin)

        if tin is None:
            return False, api_response(message=f"'id' is a required "
                                               f"field for Tax Identification Number Verification", status=False), 400

        channel_id = data.get('channelId', None)
        if not channel_id:
            return False, api_response(message=f"'channelId' is required a field", status=False), 400

        HEADERS = {"Authorization": f"Bearer {settings.VERIFY_ME_BASE_TOKEN}", "Content-Type": "application/json"}
        request_response = requests.request("GET", url=f"{settings.VERIFY_ME_BASE_URL}/v1/verifications/identities/tin/{tin}",
                                            headers=HEADERS)

        # ------------ 500 -----------
        if request_response.status_code == 500:
            return False, api_response(message=f"Error: Connecting to third-party's server", status=False,
                                       data=data), 500

        # ------------- 404 (Failed to be changed to 'Invalid') -------------
        if request_response.status_code == 404:
            response_data: dict = request_response.json()

            response = api_response(message=f"Tax Identification Number Not Found", status=False,
                                    data=response_data)
            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="failed", document_id="N/A",
                                                                document="Tax Identification Number",
                                                                verification_number=hashed_tin,
                                                                full_name="N/A", channel_id=channel_id,
                                                                transaction=transaction)
            response = dict(response) if type(response) is dict else response
            response.update({"transactionId": transaction_id})
            return False, response, 404

        # -------------- 400 - Bad Request -------------
        if request_response.status_code == 400:
            api_response(message=request_response.json(), status=False)
            return False, api_response(message=request_response.json()['message'], status=False), 400

        # ------------- 201 / 200 (Success) ------------
        if (request_response.status_code == 200 or request_response.status_code == 201) and request_response.json()[
            'status'] == 'success':
            response_data: dict = request_response.json()

            # Log response
            api_response(message=f"Successfully verified Tax Identification Number", status=True,
                         data=response_data)

            response_data_key: dict = response_data.get('data', None)

            if response_data_key is None:
                return False, api_response(message=f"Empty 'data' field from response", status=False,
                                           data=request_response.json()), 400

            response = api_response(
                message=f"Successfully verified Tax Identification Number Details", status=True, data=response_data_key)
            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="success", document_id=response_data_key.get('id', "N/A"),
                                                                document="Tax Identification Number",
                                                                verification_number=hashed_tin,
                                                                full_name=response_data_key.get('taxpayerName', 'N/A'),
                                                                channel_id=channel_id, transaction=transaction)

            response = dict(response) if type(response) == dict else response
            response.update({"transactionId": transaction_id})
            return True, response, 200

        response = api_response(message=f"An error occurred during Tax Identification Number verification",
                                data=request_response.json(), status=False)
        response = dict(response) if type(response) is dict else response
        return False, response, 400
    except (Exception,) as err:
        return False, api_response(message=f"{err}", status=False, data={}), 400


# Implemented (Done, reformatted response)
def verify_me_drivers_license(service_detail, data, request, transaction):
    """
        This block of code handles Driver License Verification.
    """
    try:
        drivers_license_id = data.get('id', None)
        hashed_drivers_license = encrypt_text(text=drivers_license_id)

        if drivers_license_id is None:
            return False, api_response(message=f"'id' is a required "
                                               f"field for Driver's License Verification", status=False), 400

        channel_id = data.get('channelId', None)
        if not channel_id:
            return False, api_response(message=f"'channelId' is required a field", status=False), 400

        HEADERS = {"Authorization": f"Bearer {settings.VERIFY_ME_BASE_TOKEN}", "Content-Type": "application/json"}
        request_response = requests.request("POST", url=f"{settings.VERIFY_ME_BASE_URL}/v1/verifications/identities/drivers_license/{drivers_license_id}",
                                            headers=HEADERS, data={})

        # ------------ 500 -----------
        if request_response.status_code == 500:
            return False, api_response(message=f"Error: Connecting to third-party's server", status=False,
                                       data=data), 500

        # ------------- 404 (Failed to be changed to 'Invalid') -------------
        if request_response.status_code == 404:
            response_data: dict = request_response.json()

            response = api_response(message=f"Driver's License Record Not Found", status=False,
                                    data=response_data)
            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="failed", document_id="N/A",
                                                                document="Driver's License Verification",
                                                                verification_number=hashed_drivers_license,
                                                                full_name="N/A", channel_id=channel_id,
                                                                transaction=transaction)
            response = dict(response) if type(response) is dict else response
            response.update({"transactionId": transaction_id})
            return False, response, 404

        # -------------- 400 - Bad Request -------------

        if request_response.status_code == 400:
            api_response(message=request_response.json(), status=False)
            return False, api_response(message=request_response.json()['message'], status=False), 400

        # ------------- 201 / 200 (Success) ------------
        if (request_response.status_code == 200 or request_response.status_code == 201) and request_response.json()[
            'status'] == 'success':
            response_data: dict = request_response.json()
            response_data_key: dict = response_data.get('data', None)

            if response_data_key is None:
                return False, api_response(message=f"Empty 'data' field from response", status=False,
                                           data=request_response.json()), 400

            # Log response from VerifyME
            api_response(
                message=f"Successfully verified Driver's License Number Details", status=True, data=request_response.json())

            reformat_response = {
                "ID": response_data_key.get('id', 'N/A'),
                "License Number": response_data_key.get('licenseNo', 'N/A'),
                "First Name": response_data_key.get('firstname', 'N/A'),
                "Middle Name": response_data_key.get('middlename', 'N/A'),
                "Last Name": response_data_key.get('lastname', 'N/A'),
                "Birth Date": response_data_key.get('birthdate', 'N/A'),
                "Gender": response_data_key.get('gender', 'N/A'),
                "Photo": response_data_key.get('photo', 'N/A'),
                "Issued Date": response_data_key.get('issuedDate', 'N/A'),
                "Expiry Date": response_data_key.get('expiryDate', 'N/A'),
                "State Of Issue": response_data_key.get('stateOfIssue', 'N/A'),
            }

            response = api_response(
                message=f"Successfully verified Driver's License Number Details", status=True, data=reformat_response)
            success, transaction_id = create_transaction_record(response, service_detail, request, amount=0.0,
                                                                success_type="success", document_id=response_data_key.get('id', "N/A"),
                                                                document="Driver's License Verification",
                                                                verification_number=hashed_drivers_license,
                                                                full_name=f"{response_data_key.get('lastname', 'N/A')} {response_data_key.get('firstname', 'N/A')}",
                                                                channel_id=channel_id, transaction=transaction)

            response = dict(response) if type(response) == dict else response
            response.update({"transactionId": transaction_id})
            return True, response, 200

        response = api_response(message=f"An error occurred during Driver's License Number Verification",
                                data=request_response.json(), status=False)
        response = dict(response) if type(response) is dict else response
        return False, response, 400
    except (Exception,) as err:
        return False, api_response(message=f"{err}", status=False, data={}), 400
