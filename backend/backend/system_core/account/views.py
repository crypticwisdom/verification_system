import datetime, secrets, logging
import json

import requests
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, HttpResponse
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .emails import welcome_msg, forgot_password_mail
from .models import User, UserDetail, UserRole, State, Service, ServiceDetail, Channel, ClientPaymentGateWayDetail, PaymentGateWay
from rest_framework_simplejwt.tokens import AccessToken
from super_admin.serializers import SuperAdminSerializer
from .serializers import IndividualSerializer, StateSerializer, ListUserSerializer, \
    LandPageListServicesSerializer, ListServiceDetailSerializer, AllChannelsSerializer, ForgotPasswordResponseSerializer, PaymentGateWayOptionSerializer
from django.conf import settings
from .utils import create_account, add_states, password_checker, business_cac_check_on_registration
from util.utils import incoming_request_checks, validate_email, api_response, get_incoming_request_checks, phone_number_check


# Create your views here.


def service_welcome(request):
    return HttpResponse("<center><h3 style='color: red'>Verification System Service END-POINT</h3></center>")


class SignInView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            data = request.data.get('data', {})

            _status, msg = incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)

            email: str = data.get('email', None)
            password: str = data.get('password', None)

            if not email:
                return Response(api_response(message="'email' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not validate_email(email=email):
                return Response(api_response(message="Invalid 'email' format", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not password:
                return Response(api_response(message="'password' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email)
            if not user.check_password(raw_password=password):
                return Response(api_response(message="Invalid login credentials", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            user_role = get_object_or_404(UserRole, user_detail__user=user)  # UserRole.objects.get(
            # user_detail__user=user)
            serialized_data = None

            if user.is_superuser and user_role.user_role == "super-admin" and user_role.user_detail.user_type == "platform":
                # Give serialized data
                serialized_data = SuperAdminSerializer(user_role, many=False, context={"request": request}).data

            elif user_role.user_role == "individual":
                serialized_data = IndividualSerializer(user_role, many=False, context={"request": request}).data

            elif user_role.user_role == "corporate-business":
                serialized_data = IndividualSerializer(user_role, many=False, context={"request": request}).data

            elif user_role.user_role == "partner-manager":
                serialized_data = IndividualSerializer(user_role, many=False, context={"request": request}).data

            elif user_role.user_role == "agency" and user_role.user_detail.user_type == "agency":
                serialized_data = IndividualSerializer(user_role, many=False, context={"request": request}).data

            elif user_role.user_role == "sub-agency" and user_role.user_detail.user_type == "agency":
                serialized_data = IndividualSerializer(user_role, many=False, context={"request": request}).data

            return Response(api_response(message="Successfully logged in", status=True, data={
                "accessToken": f"{AccessToken.for_user(user)}",
                # "refreshToken": f"{RefreshToken.for_user(user)}",
                "user": serialized_data
            }))
        except User.DoesNotExist:
            return Response(api_response(message=f"User not registered", status=False), status=status.HTTP_400_BAD_REQUEST)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class AccountCreationView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            _status1, msg1 = incoming_request_checks(request=request)

            if _status1 is False:
                return Response(api_response(message=msg1, status=False), status=status.HTTP_400_BAD_REQUEST)

            _status2, msg2 = create_account(request=request)
            if _status2 is False:
                return Response(api_response(message=msg2, status=False), status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message=msg2, status=True), status=status.HTTP_200_OK)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class StatesCRView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            success, data = add_states()
            if not success:
                return Response(api_response(message=f"{data}", status=False), status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message=f"{data}", status=success))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            states = State.objects.filter()
            # Check if any state exist, if not, then create from the embedded list 'NIGERIA_LIST'.
            if not states.exists():
                add_states()
                states = State.objects.all()

            serialized_data = StateSerializer(states, many=True).data
            return Response(api_response(message="List of all states in Nigeria", data=serialized_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class ListUsersView(APIView):
    permission_classes = []

    def get(self, request):
        """
            Used for getting list of a users in a particular user category.
        :param request:
        :return:
        """
        try:
            success, msg = get_incoming_request_checks(request)

            if not success:
                return Response(api_response(message=f"Error: 'user_type' parameter is required", status=False),
                                status=status.HTTP_200_OK)

            user_type = request.GET.get('user_type', None)

            if user_type is None:
                return Response(api_response(message=f"Error: 'user_type' parameter is required", status=False),
                                status=status.HTTP_200_OK)

            user_type: str = user_type.lower()
            if user_type not in ['agency', 'platform', 'individual', 'developer', 'corporate-business']:
                return Response(api_response(message=f"Error: 'user_type' parameter is not valid", status=False),
                                status=status.HTTP_200_OK)

            query_set = UserDetail.objects.filter(user_type=user_type)
            serialized_data = ListUserSerializer(query_set, many=True).data

            return Response(
                api_response(message=f"List of all '{user_type.capitalize()}' ", data=serialized_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class LandPageListServicesView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            success, response_msg = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=f"{response_msg}", data={}, status=True))

            service_details = Service.objects.filter(
                activate=True, servicedetail__agency__userdetail__userrole__user_role='agency')

            serialized_data = ListServiceDetailSerializer(service_details, many=True, context={"request": request})
            return Response(api_response(message=f"Land Page List of Service Details", data=serialized_data.data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# I can't remember why I provided this API
class ListServiceDetailView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            success, response_msg = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=f"{response_msg}", data={}, status=True))

            service_details = ServiceDetail.objects.filter(is_available=True)
            serialized_data = ListServiceDetailSerializer(service_details, many=True)
            return Response(api_response(message=f"List of Service Details", data=serialized_data.data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class MakeCheckFieldsView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            """
                This view validates 1 or more parameters sent through the request body datas.
                
                email, phone number, cac number, password validate, check if password matches.
            """
            _status1, data = incoming_request_checks(request=request, require_data_field=True)
            if _status1 is False:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            email = data.get("email", None)
            phone_number = data.get("phoneNumber", None)
            password = data.get("password", None)

            # cac_number = request.data.get("cacNumber", None)
            check_passwords = data.get("checkPasswords", None)

            new_password = data.get("password", None)
            confirm_password = data.get("confirmPassword", None)

            if email is None and phone_number is None and password is None:
                return Response(api_response(message="Pass in at least 1 parameter to validate", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if check_passwords is True:
                if not all([new_password, confirm_password]):
                    return Response(
                        api_response(message="'password' and 'confirmPassword' are required fields.", status=False),
                        status=status.HTTP_400_BAD_REQUEST)

            if email:
                success_email = validate_email(email=email)
                if not success_email:
                    return Response(api_response(message="Invalid Email format", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                email_exist = User.objects.filter(email=email).exists()

                if email_exist:
                    return Response(api_response(message="email already exists", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

            if phone_number:
                success_phone_number, phone_number = phone_number_check(phone_number=phone_number)
                if not success_phone_number:
                    return Response(api_response(message=phone_number, status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

            if password:
                valid, data2 = password_checker(password=password)
                if not valid:
                    return Response(api_response(message=data2, status=False), status=status.HTTP_400_BAD_REQUEST)

            if check_passwords:
                if new_password is None:
                    return Response(api_response(message="'password' is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                if confirm_password is None:
                    return Response(api_response(message="'confirmPassword' is required", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                valid1, data1 = password_checker(password=new_password)

                if not valid1:
                    return Response(api_response(message="'password' must contain uppercase, lowercase letters, "
                                                         "'# ! - _ @ $' special characters and 8 or more characters",
                                                 status=False), status=status.HTTP_400_BAD_REQUEST)

                valid2, data2 = password_checker(password=confirm_password)
                if not valid2:
                    return Response(api_response(
                        message="'confirmPassword' must contain uppercase, lowercase letters, '# ! - _ @ $' special "
                                "characters and 8 or more characters", status=False),
                        status=status.HTTP_400_BAD_REQUEST)

                if new_password != confirm_password:
                    return Response(api_response(
                        message="Password does not match", status=False), status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message="Successfully Validated data", status=False))

        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class AllUserRolesView(APIView):
    permission_classes = []

    def get(self, request):
        """
            Used for getting all user-roles view.
        """
        try:
            success, msg = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=f"Error: 'user_type' parameter is required", status=False),
                                status=status.HTTP_200_OK)

            # list_of_all_current_user_role_type
            user_role_types = list()
            user_role_types.append("super-admin")  # TM30 Super admin user
            user_role_types.append("partner-manager")  # TM30 partner manager role.
            user_role_types.append("individual")  # Normal individual user
            user_role_types.append("developer")  # Developer role.
            user_role_types.append("agency")  # Agencies created by the Agencies.
            user_role_types.append("sub-agency")  # Agencies created by the Agencies.
            user_role_types.append("corporate-business")  # Business.
            user_role_types.append("sub-corporate-business")  # Sub Business

            # More User Roles can be added if any has been added to the Platform.

            return Response(api_response(message=f"List of all User Roles on the Platform", data=user_role_types,
                                         status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class GeneratedPasswordResetView(APIView):
    """
    This view is used for reseting the auto-generated passwords of any user that was created by another user role.
    E.g Agency created sub-agency, so this view is used to reset the password of that sub-agency
    """
    permission_classes = []

    def post(self, request, slug=None):
        try:
            data = request.data.get('data', {})

            _status, msg = incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)

            generated_password: str = data.get('generatedPassword', None)
            password: str = data.get('password', None)
            confirm_password: str = data.get('confirmPassword', None)

            if not slug:
                return Response(api_response(message="'slug' is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not generated_password:
                return Response(api_response(message="'generatedPassword' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            if not password:
                return Response(api_response(message="'password' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            success, msg = password_checker(password=password)
            if not success:
                return Response(api_response(message=msg, status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not confirm_password:
                return Response(api_response(message="'confirmPassword' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if password != confirm_password:
                return Response(api_response(message="Passwords does not match", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(slug=slug)
            if not check_password(password=generated_password, encoded=user.password):
                return Response(api_response(message="'GeneratedPassword' field does not match the password generated",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            # if user.userdetail.userrole.user_role == "partner-manager":
            user.password = make_password(password=password)
            user.slug = None
            user.super_admin_has_reset_password = True
            user.save()
            serialized_data = IndividualSerializer(user.userdetail.userrole, many=False, context={"request": request}).data
            return Response(api_response(message="Password has been successfully reset", status=True, data=serialized_data))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class VerifyAccountView(APIView):
    permission_classes = []

    def get(self, request, slug=None):
        """
        After account creation a mail is sent to the user (individual, business), and then he clicks the link in the mail to verify his account.
        This view is used for account verification for individual, businesses,
        :param request:
        :param slug:
        :return:
        """
        try:
            _status, msg = get_incoming_request_checks(request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)

            if not slug:
                return Response(api_response(message="'slug' is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(slug=slug)
            if not user.exists():
                return Response(api_response(message="User with 'slug' does not exists",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(slug=slug)
            if user.userdetail.userrole.user_role == "individual":
                user.userdetail.approved = True
                user.userdetail.save()
                user.slug = None
                user.save()

                # Send welcome mail to individual
                welcome_msg(context={"user": user})

            return Response(api_response(message="Successfully verified your account", status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class AllChannelsView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            success, response_msg = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=f"{response_msg}", data={}, status=True))

            channels = Channel.objects.filter()
            serialized_data = AllChannelsSerializer(channels, many=True)
            return Response(api_response(message=f"List of all Channels", data=serialized_data.data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class VerifyCACView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            """
                This view is used for verifying if a business user provided a valid CAC number.
                The front end guy passing this 'cac' field would have manually sent the type of business that has the CAC 
                which could be one of these: 
                
                1. limited_company: Registered as limited company or
                2. business: Registered as business or
                3. incorprated_trustee: Registered as trust company.
                
                As specified by VerifyMe.
            """
            cac = request.GET.get('cac', None)
            business_type = request.GET.get('businessType', None)

            if cac is None:
                return Response(api_response(message="'cac' query field is required", status=False), status=status.HTTP_400_BAD_REQUEST)

            if business_type is None:
                return Response(api_response(message="'businessType' query field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            _status1, msg1 = get_incoming_request_checks(request=request)
            if _status1 is False:
                return Response(api_response(message=msg1, status=False), status=status.HTTP_400_BAD_REQUEST)

            if not cac:
                return Response(api_response(message="'cac' query parameter is required", status=False), status=status.HTTP_400_BAD_REQUEST)

            stat, msg2 = business_cac_check_on_registration(cac_number=cac, business_type=business_type)
            if not stat:
                return Response(api_response(message=msg2, status=False), status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message=msg2, status=True), status=status.HTTP_200_OK)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """Forgot password  for all user type"""
    permission_classes = []

    def get(self, request):
        try:
            email = request.GET.get('email', None)
            _status, msg = get_incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)

            if not email:
                return Response(api_response(message="'email' parameter is required", status=False), status=status.HTTP_400_BAD_REQUEST)

            if not validate_email(email=email):
                return Response(api_response(message="Invalid email format", status=False), status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email)
            slug = secrets.token_urlsafe(15)
            user.slug = slug
            user.otp_expire = timezone.now() + timezone.timedelta(minutes=10)
            user.save()

            # send forgot password mail to user.
            forgot_password_mail(context={"user": user})
            # serializer = ForgotPasswordResponseSerializer(user, many=False).data
            return Response(api_response(message="Email has been sent to user", status=True))

        except User.DoesNotExist:
            return Response(api_response(message=f"User not registered", status=False), status=status.HTTP_400_BAD_REQUEST)

        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            _status, data = incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            slug: str = data.get('slug', None)
            new_password: str = data.get('newPassword', None)
            confirm_password: str = data.get('confirmPassword', None)
            if not new_password:
                return Response(api_response(message="'newPassword' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            if not confirm_password:
                return Response(api_response(message="'confirmPassword' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            success, msg = password_checker(password=new_password)
            if not success:
                return Response(api_response(message=msg, status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if new_password != confirm_password:
                return Response(api_response(message="Passwords does not match", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(slug=slug)

            if timezone.now() > user.otp_expire:
                return Response(api_response(message="Link has expired, request for another forgot password link", status=False))

            password = make_password(password=new_password)
            user.password = password
            user.slug = None
            user.save()

            serializer = ForgotPasswordResponseSerializer(user, many=False).data
            return Response(api_response(message="Password has been successfully reset", data=serializer, status=True))
        except User.DoesNotExist:
            return Response(api_response(message=f"User not found", status=False), status=status.HTTP_400_BAD_REQUEST)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# Views for Payment
class GetListOfBanksView(APIView):
    """
    This is used to fetch list of banks from TMSASS Platform.
    """
    permission_classes = []

    def get(self, request):
        try:
            _status, msg = get_incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)
            url = f"{settings.PAYMENT_BASE_URL}/banks"
            HEADERS = {
                "client-id": settings.CLIENT_ID,
                "Content-Type": "application/json"
            }
            request_response_ = requests.request(method='GET', url=url, headers=HEADERS)
            response_to_dict: dict = request_response_.json()

            # Log response
            logging.info(msg=response_to_dict)

            if request_response_.status_code == 200 and response_to_dict.get('status') == "success":
                return Response(api_response(message="List of banks", status=True, data=response_to_dict.get('data', [])))

            return Response(api_response(message="List of banks", status=False, data={}), status=status.HTTP_400_BAD_REQUEST)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# This view has been extracted into a function and the function is in used in the super admin - create agency.
class AccountResolutionView(APIView):
    """
        Used to check if the account number and account code provided are valid.
    """
    permission_classes = []

    def get(self, request):
        try:
            _status, msg = get_incoming_request_checks(request=request)
            if _status is False:
                return Response(api_response(message=msg, status=False), status=status.HTTP_400_BAD_REQUEST)

            account_number = request.GET.get('accountNumber', None)
            account_code = request.GET.get('accountCode', None)

            if account_number is None and account_code is None:
                return Response(api_response(message="Error: 'accountNumber' and 'accountCode' are required field",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            account_number: str = account_number
            account_code: str = account_code

            if account_number.isdigit() is False:
                return Response(api_response(message="Error: 'accountNumber' must be digit",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            if account_code.isdigit() is False:
                return Response(api_response(message="Error: 'accountCode' must be digit",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            url = f"{settings.PAYMENT_BASE_URL}/resolveAccount?accountNumber={account_number}&bankCode={account_code}"
            HEADERS = {
                "client-id": settings.CLIENT_ID,
                "Content-Type": "application/json"
            }

            request_response_ = requests.request(method='GET', url=url, headers=HEADERS)
            response_to_dict: dict = request_response_.json()

            if request_response_.status_code == 200 and response_to_dict.get('status') == "success":
                api_response(message="Success Response", status=True, data=response_to_dict)
                return Response(api_response(message="Account Resolution Success", status=True, data=response_to_dict.get('data', [])))

            return Response(api_response(message="Error: Failed to Resolute the account number", status=False, data={}),
                            status=status.HTTP_400_BAD_REQUEST)
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# --------------------------------------


class PaymentGateWayOptions(APIView):
    permission_classes = []

    def get(self, request):
        """
            This view method is used for fetching all payment gateway options. E.G: PayStack, FlutterWave.
            Used in Signing Up an Agency.
        """
        try:
            success, msg = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=f"{msg}", status=False), status=status.HTTP_400_BAD_REQUEST)

            fetch_all_payment_option = PaymentGateWay.objects.all()
            serialized_data = PaymentGateWayOptionSerializer(fetch_all_payment_option, many=True, context={"request": request}).data
            return Response(api_response(message=f"List of all Payment Gateway Options", data=serialized_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)





