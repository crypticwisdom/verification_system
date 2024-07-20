import secrets

import requests
import json
from django.conf import settings
from util.utils import api_response, encrypt_text
import urllib.parse



class TmsassPayment:

    @staticmethod
    def account_resolution(account_number, account_code):
        """
            Used to confirm if a bank account matches the bank code.
        """
        try:
            if account_number is None and account_code is None:
                return False, "'accountNumber' and 'accountCode' are required field"
            account_number: str = account_number
            account_code: str = account_code

            if account_number.isdigit() is False:
                return False, "'accountNumber' must be digit"

            if account_code.isdigit() is False:
                return False, "'accountCode' must be digit"

            url = f"{settings.PAYMENT_BASE_URL}/resolveAccount?accountNumber={account_number}&bankCode={account_code}"
            HEADERS = {
                "client-id": settings.CLIENT_ID,
                "Content-Type": "application/json"
            }
            request_response_ = requests.request(method='GET', url=url, headers=HEADERS)
            response_to_dict: dict = request_response_.json()

            if request_response_.status_code == 200 and response_to_dict.get('status') == "success":
                api_response(message="Success Response", status=True, data=response_to_dict)
                return True, response_to_dict.get('data', [])

            return False, "Failed to Resolute the account number"
        except (Exception,) as err:
            return False, f"{err}"

    @staticmethod
    def create_sub_account(settlement_account, bank_code, business_name, is_default: bool = False, **kwargs):
        """
            This function is used
        """
        try:
            if settlement_account is None and bank_code is None:
                return False, api_response(message="Error: 'accountNumber' and 'accountCode' are required field", status=False)

            account_number: str = settlement_account
            bank_code: str = bank_code

            if account_number.isdigit() is False:
                api_response(message="Error: 'accountNumber' must be digit", status=False)
                return False, "Error: 'accountNumber' must be digit"

            if bank_code.isdigit() is False:
                api_response(message="Error: 'accountCode' must be digit", status=False)
                return False, "Error: 'accountCode' must be digit"

            if len(account_number) != 10:
                api_response(message="Error: account number length must be 10", status=False)
                return False, "Error: account number length must be 10"

            url = f"{settings.PAYMENT_BASE_URL}/split/subaccount"
            HEADERS = {
                "client-id": settings.CLIENT_ID,
                "Content-Type": "application/json"
            }

            DATA = json.dumps({
                "accountNumber": account_number,
                "businessName": business_name,
                "bankCode": bank_code,
                "isDefault": is_default
            })
            request_response_ = requests.request(method='POST', url=url, data=DATA, headers=HEADERS)
            response_to_dict: dict = request_response_.json()

            if request_response_.status_code == 200 and response_to_dict.get('status') == "success":
                # Log response
                api_response(message="Success Response", status=True, data=response_to_dict)
                return True, response_to_dict['data']

            api_response(message="Error Response", status=False, data=response_to_dict)
            return False, response_to_dict

        except (Exception,) as err:
            api_response(message=f"Error: {err}", status=False, data={})
            return False, f"{err}"

    @staticmethod
    def initialize_payment(amount, email, reference, account_code, payment_redirect_url: str = None):
        # payment_redirect_url = "https://tm30verify.netlify.app/end/reason"
        provider = "paystack"

        try:
            if email is None:
                email = f"{secrets.token_hex(10)}@verifypro.com.ng"

            if amount is None:
                api_response(message="Error: 'amount' is required", status=False)
                return False, "Error: 'amount' is required"

            url = f"{settings.PAYMENT_BASE_URL}/cards/initialize"

            payload = f'amount={amount}&email={email}&redirectUrl={payment_redirect_url}&provider={provider}&transactionId={reference}&accountCode={account_code}'
            # payload = f'amount={amount}&email={email}&redirectUrl={payment_redirect_url}&provider={provider}&transactionId={reference}'

            HEADERS = {
                "client-id": settings.CLIENT_ID,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            # api_response(message=f"-----------1----------", status=False,
            #              data={'amount': amount, 'email': email,'ref': reference, 'acctCode':account_code,'redirect': payment_redirect_url, "CLIENT_ID": f"{settings.CLIENT_ID}", "base": settings.PAYMENT_BASE_URL})
            request_response_ = requests.request(method='POST', url=url, data=payload, headers=HEADERS)

            # api_response(message=f"-----------2----------", status=False,
            #              data={'amount': amount, 'email': email,'ref': reference, 'acctCode':account_code,'redirect': payment_redirect_url, "CLIENT_ID": f"{settings.CLIENT_ID}", "base": settings.PAYMENT_BASE_URL, 'response': request_response_.json()})

            if request_response_.status_code == 200:
                api_response(message=f"Initializing payment", status=True, data=request_response_.json())
                return True, request_response_.json()

            api_response(message=f"Failed to initializing payment", status=False, data=request_response_.json())
            return False, request_response_.json()
        except (Exception, ) as err:
            return False, f"Error: {err} -"

    @staticmethod
    def verify_payment(reference: str = None):
        """
            TMSASS's Verify payment endpoint.
        """
        try:
            if reference is None:
                api_response(message="Error: Transaction 'reference' is required", status=False)
                return False, "Error: 'amount' is required", {}

            url = f"{settings.PAYMENT_BASE_URL}/cards/verify/{reference}"

            HEADERS = {
                "client-id": settings.CLIENT_ID,
                "Content-Type": "application/json"
            }
            request_response_ = requests.request(method='GET', url=url, headers=HEADERS)
            json_request_response: dict = request_response_.json()

            if request_response_.status_code == 200 and json_request_response['data']['status'] == "SUCCESS" and \
                    json_request_response['data']['providerResponse']['status'] == "success":

                api_response(message=f"Payment Verification was successful", status=True, data=request_response_.json())
                return True, "Payment Verification was successful", request_response_.json()['data']

            elif request_response_.status_code == 200 and json_request_response['data']['status'] == "FAILED" and \
                    json_request_response['data']['providerResponse']['status'] == "failed":

                api_response(message=f"Payment Verification was not successful", status=False, data=request_response_.json())
                return False, "Payment Verification was not successful", request_response_.json()['data']

            elif request_response_.status_code == 200 and json_request_response['data']['status'] == "ABANDONED" and \
                    json_request_response['data']['providerResponse']['status'] == "abandoned":

                api_response(message=f"Payment Verification was not successful", status=False, data=request_response_.json())
                return False, "Payment Verification was not successful", request_response_.json()['data']

            api_response(message=f"Something went wrong", status=False, data=request_response_.json())
            return False, "Payment Verification Failed", request_response_.json()['data']
        except (Exception, ) as err:
            return False, f"Error: {err}", {}

