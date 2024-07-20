from django.contrib.auth.hashers import check_password, make_password
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from account import permission
from rest_framework import status
from account.models import User, UserDetail, UserRole, Service, State, Channel, Transaction, ServiceDetail
from django.db.models import Q
from util.paginations import CustomPagination
from util.utils import api_response, incoming_request_checks, get_month, transaction_queryset_date_range_filter
from .serializers import IndividualVerificationServiceSerializer, IndividualTransactionSerializer, \
    IndividualVerificationServicesListSerializer, IndividualServiceHistorySerializer, \
    IndividualRecentVerificationSerializer, IndividualProfileSerializer, LandPageServicesSerializer
from django.utils import timezone

from util.utils import validate_email, phone_number_check, get_incoming_request_checks
from account.utils import password_checker


# Create your views here.
class IDashboardView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsIndividual]

    def get(self, request):
        try:
            query_month = request.GET.get("query_month", None)
            data = {}
            container1 = {}
            transactions = Transaction.objects.filter(owner=request.user)

            # Filter by 'this month', 'last month' and 'last 6 month'
            if query_month == "this_month":
                query_month = get_month(month=0).date()
                transactions = transactions.filter(created_on__date__range=[query_month, timezone.now().date()])
            elif query_month == "last_month":
                query_month = get_month(month=1).date()
                transactions = transactions.filter(created_on__date__range=[query_month, timezone.now().date()])
            elif query_month == "last_6_month":
                query_month = get_month(month=6).date()
                transactions = transactions.filter(created_on__date__range=[query_month, timezone.now().date()])

            container1.update({"totalRequests": transactions.count()})
            container1.update({"verifiedRequests": transactions.filter(status="success").count()})
            container1.update({"pendingRequests": transactions.filter(status="pending").count()})
            container1.update({"failedRequests": transactions.filter(status="failed").count()})
            data.update(container1)
            # ---------- Recent Services -----------
            container3 = []
            # 1. Fetch all 5 recent services used by this user.
            recent_transaction = Transaction.objects.filter(owner=request.user).order_by('-id')
            service_detail_ids = []

            # 2. Fetch 'ids' of all service_detail in Transaction recently made by this user without duplicate.
            for transaction in recent_transaction:
                if transaction.service_detail is not None:
                    if transaction.service_detail.id not in service_detail_ids:
                        service_detail_ids.append(transaction.service_detail.id)

            data_ = []

            # 3. Get all 'ServiceDetail' instance for individual ids.
            for service_detail_id in service_detail_ids:
                service_detail = ServiceDetail.objects.get(id=service_detail_id)
                _ = IndividualRecentVerificationSerializer(service_detail, many=False,
                                                           context={"request": request}).data
                data_.append(_)
            data.update({"recentVerifications": data_})

            # Transaction made by this user.
            container2 = {}
            container2.update({"recentHistory": IndividualTransactionSerializer(transactions.order_by('-id')[:10],
                                                                                many=True).data})

            data.update(container2)
            return Response(api_response(message=f"Individual Dashboard Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class IVerificationView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsIndividual]

    def get(self, request, pk=None):
        try:
            if pk:
                # Get the agencies under
                service = Service.objects.filter(id=pk)
                if not service.exists():
                    return Response(api_response(message=f"Service with ID '{pk}' does not exists", data={},
                                                 status=False), status=status.HTTP_400_BAD_REQUEST)

                data = IndividualVerificationServiceSerializer(service, many=True, context={"request": request}).data
                return Response(api_response(message=f"Services Under '{service.last().name}'", data=data, status=True))

            data = {}
            q1 = Q(servicedetail__service_type="free", servicedetail__is_available=True, activate=True) \
                 & Q(servicedetail__agency__userdetail__user_type='agency') \
                 & Q(servicedetail__agency__userdetail__userrole__user_role='agency')

            # Fetch all 'free' activated and allowed services on the Platform.
            free_services = Service.objects.filter(q1).order_by('id')

            serialized_pagination = LandPageServicesSerializer(
                self.paginate_queryset(free_services.distinct(), request), many=True,
                context={'request': request, "service_type": "free"}).data
            paginated_response1 = self.get_paginated_response(serialized_pagination).data
            data.update({"free": paginated_response1})

            q2 = Q(servicedetail__service_type="paid", servicedetail__is_available=True, activate=True) \
                 & Q(servicedetail__agency__userdetail__user_type='agency') \
                 & Q(servicedetail__agency__userdetail__userrole__user_role='agency')
            paid_services = Service.objects.filter(q2).order_by('id')
            serialized_pagination = LandPageServicesSerializer(
                self.paginate_queryset(paid_services.distinct(), request), many=True,
                context={'request': request, "service_type": "paid"}).data
            paginated_response2 = self.get_paginated_response(serialized_pagination).data
            data.update({"paid": paginated_response2})

            # - For learning purpose, this can be used to filter just the IDs of the queryset, that is  can be used to
            # get a queryset of only the ids or specific model field.

            # Service.objects.values_list('id', flat=True) <1, 2, 3>, if flat=False then, <(1,), (2,)>

            return Response(api_response(message=f"Verification Dashboard Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class ITransactionView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsIndividual]

    def get(self, request):
        try:
            query = request.GET.get("query", None)
            status_query = request.GET.get("statusFilter", None)
            service_ids_filter = request.GET.get("serviceDetailIdsFilter", None)
            start_date = request.GET.get("startDate", None)
            end_date = request.GET.get("endDate", None)
            download = request.GET.get('download', None)

            download = str(download).lower()
            if download == "true":
                download = True
            elif download == "false":
                download = False
            else:
                download = False

            query_set = Transaction.objects.filter(owner=request.user).order_by("-id")
            # SEARCH: query by service-type, service-detail-name, name, document.
            if query:
                query: str = query.lower()
                query_set = query_set.filter(
                    Q(service_detail__service_type__icontains=query) | Q(service_detail__name=query)
                    | Q(channel__name__icontains=query) | Q(amount__contains=query) | Q(document__icontains=query) | Q(full_name__icontains=query))

            # ------- Date range filter -------
            query_set = transaction_queryset_date_range_filter(start_date, end_date, query_set)

            # ------- Status filter --------
            # Note: Filter values must be separated by only commas. e.g: success,failed.
            if status_query:
                status_query: str = status_query
                status_query: list = [each_status.lower() for each_status in status_query.split(',')]

                # Filter 'success' and 'failed' together.
                if len(status_query) == 2 and ('success' in status_query and 'failed' in status_query):
                    query_set &= query_set.filter(Q(status__iexact="success") | Q(status__iexact="failed"))

                # If the filter value passed is 1 e.g "success". Run the code below.
                elif len(status_query) == 1:
                    if status_query[0] == "success":
                        query_set &= query_set.filter(status__iexact="success")

                    if status_query[0] == "failed":
                        query_set &= query_set.filter(status__iexact="failed")

                # Catches a case where a single filter value was passed but with a comma. e.g "success,"
                elif len(status_query) == 2 and (status_query[1] == '' or status_query[1] == ' '):
                    if status_query[0] == "success":
                        query_set &= query_set.filter(status__iexact="success")

                    if status_query[0] == "failed":
                        query_set &= query_set.filter(status__iexact="failed")

                # ---------------- End of status filter ---------------

                # ---------------- Filter by Service Detail -----------------
                if service_ids_filter is not None:
                    service_ids_filter: str = service_ids_filter
                    service_ids_filter: list = service_ids_filter.split(',')

                    for each_id in service_ids_filter:
                        if each_id:
                            # This operation will add/appends all existing transaction records with the 'each_id' found.
                            query_set ^= query_set.filter(Q(service_detail__id=each_id))

            response = IndividualTransactionSerializer(query_set, many=True).data
            if download is False:
                paginated_query = self.paginate_queryset(query_set, request=request)
                response = self.get_paginated_response(
                    IndividualTransactionSerializer(paginated_query, many=True).data).data

            return Response(api_response(message=f"Transaction Dashboard Data", data=response, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class IGetServiceInformation(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsIndividual]

    def get(self, request, pk=None):
        try:
            if pk:
                # Fetch all transactions that has been done with this Service.
                queryset = Service.objects.filter(id=pk)
                service = Service.objects.filter(id=pk).last()

                if not queryset.exists():
                    return Response(api_response(message=f"Service with ID '{pk}' does not exists", data={},
                                                 status=False), status=status.HTTP_400_BAD_REQUEST)

                transactions_history = Transaction.objects.filter(owner=request.user,
                                                                  service_detail__service=service).order_by('id')
                paginated_query = self.paginate_queryset(transactions_history, request=request)
                response = self.get_paginated_response(
                    IndividualServiceHistorySerializer(paginated_query, many=True, context={"user": request.user}).data)
                return Response(
                    api_response(message=f"Services Information for '{service.name}'", data=response.data, status=True))

            return Response(api_response(message=f"service ID is required", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class IndividualSettingsView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsIndividual]

    def post(self, request):
        try:
            data = request.data.get('data', {})
            _status1, data = incoming_request_checks(request=request, require_data_field=False)

            if _status1 is False:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            first_name = request.data.get("firstName", None)
            last_name = request.data.get("lastName", None)
            image = request.FILES.get("image", None)
            email = request.data.get("email", None)
            phone_number = request.data.get("phoneNumber", None)
            current_password = request.data.get("currentPassword", None)
            new_password = request.data.get("newPassword", None)
            confirm_password = request.data.get("confirmPassword", None)
            push_notification = request.data.get("pushNotification", None)

            if image:
                image = image

            if first_name:
                first_name: str = first_name.title()

            if last_name:
                last_name: str = last_name.title()

            if email:
                check_email = validate_email(email=email)

                if not check_email:
                    return Response(api_response(message="Invalid email format", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

                if User.objects.filter(email=email).exists():
                    return Response(api_response(message="Email already exist", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

            if phone_number:
                phone_number_success, phone_number = phone_number_check(phone_number=phone_number)

                if not phone_number_success:
                    return Response(api_response(message=phone_number, status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

            if current_password:
                is_current_password = check_password(password=current_password, encoded=request.user.password)
                if not is_current_password:
                    return Response(api_response(message="Incorrect current password", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

            if new_password:
                valid, data1 = password_checker(password=new_password)
                if not valid:
                    return Response(api_response(message=data1, status=False), status=status.HTTP_400_BAD_REQUEST)

            if confirm_password:
                valid, data2 = password_checker(password=confirm_password)
                if not valid:
                    return Response(api_response(message=data2, status=False), status=status.HTTP_400_BAD_REQUEST)

            new_password_is_current_password = check_password(password=new_password, encoded=request.user.password)
            if new_password_is_current_password:
                return Response(api_response(message="Your new password and current password cannot be the same",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            elif new_password != confirm_password:
                return Response(api_response(message="Passwords does not match", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if push_notification:
                push_notification: str = push_notification.lower()

                if push_notification == "true" or push_notification == "True":
                    push_notification: bool = True
                elif push_notification == "false" or push_notification == "False":
                    push_notification: bool = False

            user = request.user

            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.push_notification = push_notification
            user.password = make_password(password=new_password)
            user.image = image
            user.save()

            user.userdetail.phone_number = phone_number
            user.userdetail.save()

            # Check if Notification was just turned ON or OFF then send a mail.
            if user.push_notification is True and push_notification is True:
                # Send Mail: Notification service has been turned ON, have a separate email notification message for
                # this
                ...

            if user.push_notification is False and push_notification is False:
                # Send Mail: Notification service has been turned OFF, have a separate email notification message for
                # this
                ...

            serialized_data = IndividualProfileSerializer(user, many=False, context={"request": request}).data
            return Response(api_response(message=f"{user.first_name}'s profile", data=serialized_data, status=True))

        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
            Used for get a logged in Individual user record.
        """
        try:
            success, msg = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=f"Error: 'user_type' parameter is required", status=False),
                                status=status.HTTP_200_OK)

            serialized_data = IndividualProfileSerializer(request.user, many=False, context={"request": request}).data
            return Response(api_response(message=f"{request.user.first_name}'s profile", data=serialized_data,
                                         status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", status=False), status=status.HTTP_400_BAD_REQUEST)
