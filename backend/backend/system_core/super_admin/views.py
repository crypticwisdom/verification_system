import ast
import secrets

from dateutil.relativedelta import relativedelta
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from account import permission
from rest_framework import status
from account.models import User, UserDetail, UserRole, Service, State, Channel, Transaction, ServiceDetail, PaymentGateWay, ClientPaymentGateWayDetail
from django.db.models import Q
from .serializers import SuperAdminServiceSerializer, SuperAdminDashboardUserCategorySerializer, \
    SuperAdminUserCategoryPartnerManager, SuperAdminUserCreationSerializer, SuperAdminPartnerManagerDetailSerializer, \
    SuperAdminTransactionSerializer, SuperAdminPartnerManagerAgencyListSerializer, SuperAdminAgencyDetailSerializer, \
    SuperAdminAgencyServiceSerializer, VerificationTransactionSerializer, DashboardBreakDownSerializer, \
    SharedPMandSPAChannelImageSerializer, SuperAdminExistingAndNonExistingServicesSerializer
from util.utils import incoming_request_checks, api_response, validate_email, phone_number_check, \
    delete_created_instances, transaction_queryset_date_range_filter, transaction_queryset_status_filter, date_periods, \
    get_incoming_request_checks, encrypt_text, decrypt_text
from util.paginations import CustomPagination
from .utils import general_field_check, create_user_type
from account.emails import service_activation_msg, service_deactivation_msg, service_addition_mail
from verify.payment_modules.tmsass import TmsassPayment


# Create your views here.


#  ----- User Category First-Page [Filter, Search and Sort remaining ]: Done-------
class SuperAdminUserCategoryDashboardView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request):
        """
            This Method is used for Displaying User Category - Dashboard Data.
        :param request:
        :return:
        """
        try:
            start_date = request.GET.get("startDate", None)
            end_date = request.GET.get("endDate", None)
            user_roles_query = request.GET.get("userRoles", None)
            created_order = request.GET.get("createdOrder", None)
            search_query = request.GET.get("searchQuery", None)

            data = dict()
            data.update({"partnerManagerCount": UserRole.objects.filter(user_role="partner-manager",
                                                                        user_detail__user_type="platform").count()})
            data.update(
                {"AgencyCount": UserRole.objects.filter(user_role="agency", user_detail__user_type="agency").count()})
            data.update({"subAgencyCount": UserRole.objects.filter(user_role="sub-agency",
                                                                   user_detail__user_type="agency").count()})
            data.update({"individualCount": UserRole.objects.filter(user_role="individual",
                                                                    user_detail__user_type="individual").count()})
            data.update({"developerCount": UserRole.objects.filter(user_role="developer",
                                                                   user_detail__user_type="developer").count()})
            data.update({"corporateBusinessCount": UserRole.objects.filter(user_role="corporate-business",
                                                                           user_detail__user_type="corporate-business").count()})

            query_set = UserRole.objects.filter().order_by('-id')

            # ------- Date Filter --------
            if start_date and end_date:
                query_set = query_set.filter(Q(created_on__date__range=[start_date, end_date]))

            # ------ Search Query -------
            if search_query:
                query_set &= query_set.filter(Q(user_detail__name__icontains=search_query) |
                                              Q(user_detail__user__email__icontains=search_query))

            # -------- Order --------
            if created_order:
                created_order: str = created_order.lower()
                if created_order in ['a-z', 'z-a']:

                    if created_order == "a-z":
                        query_set &= query_set.order_by('created_on')

                    if created_order == "z-a":
                        query_set &= query_set.order_by('-created_on')

            if user_roles_query:
                query_set &= query_set.filter(user_role__icontains=user_roles_query)

            serialized_pagination = SuperAdminDashboardUserCategorySerializer(
                self.paginate_queryset(query_set, request), many=True).data
            paginated_response = self.get_paginated_response(serialized_pagination).data
            data.update({"recentlyAddedUsers": paginated_response})

            return Response(
                api_response(message=f"Data for SuperAdmin-UserCategory-Dashboard consumption", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


#  ----- End User Category First Page -------


class SuperAdminUserEachCategoriesView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request):
        """
        - This method is responsible for fetching 'each-section' for individual user-types on the User-Category Section.
        - It is also responsible for fetching recently added 'user-type(category), on the User-Category Section.
            :param request:
            :return:
        """
        try:
            category = request.GET.get('category', None)
            query = request.GET.get('query', None)
            order_query = request.GET.get('order', None)
            start_date_query = request.GET.get('startDateQuery', None)
            end_date_query = request.GET.get('endDateQuery', None)
            serialized_pagination = paginated_response = query_set = None
            data = {}
            if category:
                category: str = category.lower()
                # if category not in ['agency', 'individual', 'developer', 'business', 'partner-manager']:
                if category not in ['agency', 'partner-manager']:
                    return Response(
                        api_response(message=f"Error: 'category' parameter contains an invalid user category",
                                     status=False), status=status.HTTP_400_BAD_REQUEST)

                query_set = UserRole.objects.filter(user_detail__user_type=category).order_by('-id')

                if category == 'agency':

                    # --- name and email ---
                    if query:
                        q = Q(user_detail__name__icontains=query) | Q(user_detail__user__email=query)
                        query_set = query_set.filter(q)

                    # A-Z, Z-A
                    if order_query:
                        order_query: str = order_query.lower()
                        if order_query == 'a-z':
                            query_set = query_set.order_by('user_detail__user__date_joined')
                        elif order_query == 'z-a':
                            query_set = query_set.order_by('-user_detail__user__date_joined')

                    # start date to end date
                    if start_date_query and end_date_query:
                        query_set = query_set.filter(user_detail__user__date_joined__date__range=[start_date_query,
                                                                                                  end_date_query])  # [from, to]

                    serialized_pagination = SuperAdminDashboardUserCategorySerializer(self.paginate_queryset(
                        query_set, request), many=True).data

                elif category == 'partner-manager':
                    query_set = UserRole.objects.filter(user_detail__user_type='platform', user_role=category).order_by(
                        '-id')

                    # name and email query
                    if query:
                        q = Q(user_detail__name__icontains=query) | Q(user_detail__user__email=query)
                        query_set = query_set.filter(q)

                    # A-Z, Z-A
                    if order_query:
                        order_query: str = order_query.lower()
                        if order_query == 'a-z':
                            query_set = query_set.order_by('user_detail__user__date_joined')
                        elif order_query == 'z-a':
                            query_set = query_set.order_by('-user_detail__user__date_joined')

                    # start date to end date
                    if start_date_query and end_date_query:
                        query_set = query_set.filter(user_detail__user__date_joined__date__range=[start_date_query,
                                                                                                  end_date_query])  # [from, to]

                    serialized_pagination = SuperAdminUserCategoryPartnerManager(self.paginate_queryset(
                        query_set, request), many=True).data

                # elif category == 'individual':
                #     # Purposely used the serializer for 'agency' category here
                #     serialized_pagination = SuperAdminDashboardUserCategorySerializer(self.paginate_queryset(
                #         query_set, request), many=True).data

                # elif category == 'developer':
                #     # Still using the 'SuperAdminDashboardUserCategorySerializer'
                #     # because the UX design doesn't specify what data to be displayed
                #     serialized_pagination = SuperAdminDashboardUserCategorySerializer(self.paginate_queryset(
                #         query_set, request), many=True).data

                # elif category == 'sub-agency':
                #     # Still using the 'SuperAdminDashboardUserCategorySerializer'
                #     # because the UX design doesn't specify what data to be displayed
                #     serialized_pagination = SuperAdminDashboardUserCategorySerializer(self.paginate_queryset(
                #         query_set, request), many=True).data

                # elif category == 'business':
                #     # Still using the 'SuperAdminDashboardUserCategorySerializer'
                #     # because the UX design doesn't specify what data to be displayed
                #     serialized_pagination = SuperAdminDashboardUserCategorySerializer(self.paginate_queryset(
                #         query_set, request), many=True).data

                paginated_response = self.get_paginated_response(serialized_pagination).data
                data.update({"response": paginated_response})
                data.update({"totalCount": query_set.count()})

            return Response(
                api_response(message=f"Data for {category.capitalize()} User Category consumption",
                             data=data, status=True))

        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class SuperAdminCreateNewServiceView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request, pk=None):
        """
            Responsible for getting list of Services and Individual Service with sort and filter
        :param request:
        :param pk:
        :return:
        """
        try:
            query = request.GET.get('query', None)
            sort = request.GET.get('sort', None)

            # Get a single service by id.
            if pk:
                service = Service.objects.get(id=pk)
                data = SuperAdminServiceSerializer(service, context={'request': request}).data
                return Response(api_response(message=f"Details of '{service.name}'", data=data, status=True))

            data = dict()
            # ------------ sort and filter operation in queryset -----------
            query_set = Service.objects.filter().order_by("id")
            if query:
                query_set = Service.objects.filter(Q(name__icontains=query))

            if sort:
                sort: str = sort
                if sort.lower() == 'a-z':
                    query_set = query_set.order_by('created_on')
                elif sort.lower() == 'z-a':
                    query_set = query_set.order_by('-created_on')

            serialized_pagination = SuperAdminServiceSerializer(
                self.paginate_queryset(query_set, request), many=True, context={'request': request}).data
            paginated_response = self.get_paginated_response(serialized_pagination).data
            data.update({"services": paginated_response})

            return Response(api_response(message=f"Data for SuperAdmin-Service consumption", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        service = None
        try:
            success, data = incoming_request_checks(request=request, require_data_field=False)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            service_name = request.data.get('serviceName', None)
            service_logo = request.data.get('logo', None)
            description = request.data.get('description', None)
            providers = request.data.get('providers', [])

            if not service_name:
                return Response(api_response(message="'serviceName' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            service_name: str = service_name

            if not service_logo:
                return Response(api_response(message="'logo' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not description:
                return Response(api_response(message="'description' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not providers:
                return Response(api_response(message="'providers' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            providers = ast.literal_eval(providers)

            service_name: str = service_name.capitalize()
            service, created = Service.objects.get_or_create(name=service_name)
            if not created:
                return Response(api_response(message=f"'{service_name} 'Service already exists", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            service.description = description
            service.activate = True
            service.logo = service_logo
            service.save()

            # Add Providers
            if providers is not None:
                for provider_id in providers:
                    # create service detail here for each provider
                    agency = User.objects.get(id=provider_id)
                    # 'service_detail_code' will be added by the superAdmin, which will be used to write a block of code
                    # for them.

                    service_detail = ServiceDetail.objects.create(service=service, agency=agency)

                    # Create a custom Service Name for the Service Detail that belongs to an Agency by appending the
                    # service name with the Agency's name

                    service_detail.name = f"{service_name} by {agency.userdetail.name}"
                    code = secrets.token_urlsafe(3) + "&8" + secrets.token_urlsafe(5)
                    service_detail.service_detail_code = code
                    service_detail.save()

                    #   Send Email Here (Notify agencies of the newly added service to their profile).
                    service_addition_mail(context={"service_detail": service_detail, "agency": agency})

            return Response(api_response(message=f"Successfully added '{service.name}' with provider(s)", data={},
                                         status=True))
        except (Exception,) as err:
            delete_created_instances(service)
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            success, data = incoming_request_checks(request=request)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            service_id = data.get('serviceId', None)
            service_status = data.get('serviceStatus', False)
            service_name = data.get('serviceName', None)
            description = data.get('description', None)

            if not service_id:
                return Response(api_response(message="'serviceID' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            service = Service.objects.get(id=service_id)

            if service_status not in [True, False]:
                return Response(api_response(message="'serviceStatus' expects either true or false", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            service.name = str(service_name).capitalize() if service_name else service.name
            service.description = description if description else service.description
            service.activate = service_status
            service.save()

            serialized_data = SuperAdminServiceSerializer(service, context={'request': request}).data

            return Response(
                api_response(message=f"Successfully updated '{service_name}' Service", data=serialized_data,
                             status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        try:
            if pk is None:
                return Response(api_response(message="'service id' is not present in the URL", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            service = Service.objects.get(id=pk)
            service.delete()
            # Notification can come in here
            return Response(api_response(message=f"Service has been Deleted", status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: '{err}'", status=False), status=status.HTTP_400_BAD_REQUEST)


class SuperAdminUserOperationView(APIView):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request, pk=None):
        """
            Used to get each details of any user except an 'agency'.
        """
        try:
            data = dict()
            serialized_data = {}
            if pk:
                user_role = UserRole.objects.get(user_detail__user__id=pk)
                # Check the user_type and use the appropriate Serializer to serialize the datas to be rendered.
                if user_role.user_detail.user_type == "individual":
                    ...

                # if user_role.user_detail.user_type == "agency":
                # This part has been written as a Stand Alone View, because of it's number of data returned.
                # serialized_data['details'] = {}
                # serialized_data['overview'] = {}
                # serialized_data['services'] = {}
                # serialized_data['recentHistory'] = {}

                if user_role.user_detail.user_type == "developer":
                    ...
                if user_role.user_detail.user_type == "corporate-business":
                    ...
                if user_role.user_detail.user_type == "platform":
                    serialized_data = SuperAdminPartnerManagerDetailSerializer(user_role, many=False,
                                                                               context={'request': request}).data
                    data.update({'userDetail': serialized_data})

                    # Get all Agencies assigned to this Partner-Manage
                    query_filters = user_role.user_detail.manages.filter()
                    data.update({"agencyList": SuperAdminPartnerManagerAgencyListSerializer(query_filters, many=True,
                                                                                            context={
                                                                                                "request": request}).data})

            return Response(
                api_response(message=f"User detail for user with ID '{pk}'", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            success, data = incoming_request_checks(request=request)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            user_id = data.get('userId', None)
            if user_id is None:
                return Response(api_response(message="Error: 'userId' field is required",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            _status = data.get('status', False)
            user_role = UserRole.objects.get(user_detail__user__id=user_id)

            # service.description = description if description else service.description
            user_role.user_detail.approved = _status
            user_role.user_detail.save()

            return Response(
                api_response(message=f"Update was made successfully", data={}, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# ---------- View Individual Agency -----------
class SuperAdminIndividualAgencyView(APIView):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request, pk=None):
        """
            - This View is specifically written for Viewing the Agency Detail Page.
            - This view's response contains 'OverView', 'Service', and 'Recent History'.
        """
        try:
            overview_data = {}
            data = dict()
            if pk:
                user_role = UserRole.objects.get(user_detail__user__id=pk)
                # Check the user_type and use the appropriate Serializer to serialize the datas to be rendered.

                if user_role.user_detail.user_type == "agency":
                    # This part has been written as a Stand-Alone View, because of it's number of data returned.
                    data['details'] = SuperAdminAgencyDetailSerializer(user_role, many=False,
                                                                       context={"request": request}).data

                    # over_view_container = []
                    channels = Channel.objects.filter()
                    overview_data = {}

                    # ----------- Handles the Overview section ----------
                    for channel in channels:
                        successful_transactions = Transaction.objects.filter(agency=user_role.user_detail.user,
                                                                             channel=channel, status='success')
                        amount = 0.0
                        for transaction in successful_transactions:
                            amount += float(transaction.amount)
                        overview_data.update({f"{channel.name}": amount})
                    # ----------- End --------------

                    agency = user_role.user_detail.user
                    transactions = Transaction.objects.filter(agency=agency, status='success')

                    # ----------- Total Overall amount ------------
                    overall_amount = 0.0
                    for transaction in transactions:
                        overall_amount += float(transaction.amount)
                    # ----------- END ------------

                    # ----------- Services --------
                    services = ServiceDetail.objects.filter(agency=agency)
                    serialized_services = SuperAdminAgencyServiceSerializer(services, many=True,
                                                                            context={"request": request}).data
                    # ----------- End --------------

                    # ---------- Get list of last 15 Transactions ----
                    latest_transactions = Transaction.objects.filter(agency=agency).order_by('-id')[:15]
                    # ---------- END ---------------

                    overview_data['details'] = SuperAdminAgencyDetailSerializer(user_role, many=False).data
                    overview_data['overAll'] = overall_amount
                    overview_data['successfulVerification'] = transactions.filter(status='success').count()
                    overview_data['failedVerification'] = transactions.filter(status='failed').count()
                    overview_data['services'] = serialized_services
                    overview_data['recentHistory'] = SuperAdminTransactionSerializer(instance=latest_transactions,
                                                                                     many=True).data

            return Response(
                api_response(message=f"User detail for user with ID '{pk}'", data=overview_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ----- End Of Individual Agency View -----------


class SuperAdminCreateUsersView(APIView):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def post(self, request):
        try:
            user = user_detail = user_role = message = msg_or_serialized_data = None
            # This request handler would also handle form datas and since there is no way to pass in request-body in a
            # 'data' field, I would need to just handle the request that way i.e with expecting 'data' field but will
            # only require requestType field.

            # This will no longer check for 'data' field since 'require_data_field' is 'False' which is default to True.
            success, response = incoming_request_checks(request=request, require_data_field=False)
            # To get request, we now need to get 'request.data'.

            if not success:
                return Response(api_response(message=response, status=False), status=status.HTTP_400_BAD_REQUEST)

            success, request_data = general_field_check(data=request.data)
            if not success:
                return Response(api_response(message=request_data, status=False), status=status.HTTP_400_BAD_REQUEST)
            user_type = request_data.get('user_type', None)

            if user_type is None:
                return Response(api_response(message="'user_type' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            user_type: str = user_type.lower()
            if user_type not in ['agency', 'partner-manager']:
                return Response(api_response(message="'user_type' not valid", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            has_been_created, msg_or_serialized_data = create_user_type(user_type, data=request_data, request=request)
            if not has_been_created:
                return Response(api_response(message=f"Error: {msg_or_serialized_data}", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            return Response(
                api_response(message=f"Successfully created {user_type.capitalize()}", data=msg_or_serialized_data,
                             status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# ----------------- SuperAdmin Channel Section (Not Done) --------------------
class SuperAdminChannelView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request, pk=None):
        """
            Data to be displayed on the SuperAdmin Channel-Dashboard Page.
        """
        try:
            query = request.GET.get('query', None)
            usage_time_filter = request.GET.get('usageTimeFilter', None)
            revenue_time_filter = request.GET.get('revenueTimeFilter', None)
            query_transaction_start_date = request.GET.get('queryTransactionStartDate', None)
            query_transaction_end_date = request.GET.get('queryTransactionEndDate', None)
            transaction_order = request.GET.get('transactionOrder', None)
            data1 = []
            data2 = []
            overview_data = {}
            channels = Channel.objects.filter()

            # --------- Usage ---------------x
            if usage_time_filter:
                # Filter by Usage

                usage_time_filter: str = usage_time_filter.lower()

                date_ = date_periods(query=usage_time_filter)

                for channel in channels:
                    transaction_count = Transaction.objects.filter(channel=channel, created_on__date__range=[date_,
                                                                                                             timezone.now().date()]).count()
                    data1.append({"channelName": channel.name, "totalCount": transaction_count,
                                  "channelLogo": SharedPMandSPAChannelImageSerializer(
                                      channel, many=False, context={"request": request}).data,
                                  "channelId": channel.id})
            else:
                for channel in channels:
                    transaction_count = Transaction.objects.filter(channel=channel).count()
                    data1.append({"channelName": channel.name, "totalCount": transaction_count,
                                  "channelLogo": SharedPMandSPAChannelImageSerializer(
                                      channel, many=False, context={"request": request}).data,
                                  "channelId": channel.id})
            overview_data['channelUsage'] = data1

            # --------- Revenue ---------------x
            if revenue_time_filter:
                revenue_time_filter: str = revenue_time_filter.lower()

                date_ = date_periods(query=revenue_time_filter)

                for channel in channels:
                    transactions = Transaction.objects.filter(channel=channel, status="success",
                                                              created_on__date__range=[date_, timezone.now().date()])
                    amount = 0
                    for transaction in transactions:
                        amount += float(transaction.amount)

                    data2.append({"channelId": channel.id, "channelName": channel.name, "amount": amount,
                                  "channelLogo": SharedPMandSPAChannelImageSerializer(channel, many=False,
                                                                                      context={
                                                                                          "request": request}).data})
                overview_data['channelRevenue'] = data2
            else:
                for channel in channels:
                    transactions = Transaction.objects.filter(channel=channel, status="success")
                    amount = 0
                    for transaction in transactions:
                        amount += float(transaction.amount)

                    data2.append({"channelId": channel.id, "channelName": channel.name, "amount": amount,
                                  "channelLogo": SharedPMandSPAChannelImageSerializer(channel, many=False,
                                                                                      context={
                                                                                          "request": request}).data})
                overview_data['channelRevenue'] = data2

            # ---------- Get list of Transactions ---------
            latest_transactions = Transaction.objects.filter().order_by('-id')

            # Search by channel-name, status, amount, service detail
            if query:
                query: str = query.lower()
                latest_transactions = Transaction.objects.filter(
                    Q(channel__name__icontains=query) | Q(status__icontains=query) | Q(amount__contains=query) | Q(
                        service_detail__name__icontains=query)
                ).order_by('-id')

            # Date range fitler on transaction
            if query_transaction_start_date and query_transaction_end_date:
                latest_transactions &= transaction_queryset_date_range_filter(start_date=query_transaction_start_date,
                                                                              end_date=query_transaction_end_date,
                                                                              query_set=latest_transactions)

            # -------- Transaction Order --------------
            if transaction_order:
                transaction_order: str = transaction_order.lower()
                if transaction_order in ['a-z', 'z-a']:
                    if transaction_order == "a-z":
                        latest_transactions = latest_transactions.order_by('created_on')

                    elif transaction_order == "z-a":
                        latest_transactions.order_by('-created_on')

            # ---------- END ---------------

            serialized_pagination = SuperAdminTransactionSerializer(
                self.paginate_queryset(latest_transactions, request), many=True, context={'request': request}).data
            paginated_response = self.get_paginated_response(serialized_pagination).data
            overview_data['recentHistory'] = paginated_response

            return Response(api_response(message=f"Channels", data=overview_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
            Used for adding channels.
            :param request:
            :return:
        """
        channel = None
        try:
            success, data = incoming_request_checks(request=request, require_data_field=False)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            channel_name = request.data.get('channelName', None)
            code = request.data.get('code', None)
            activate = request.data.get('activate', None)
            logo = request.data.get('logo', None)

            if not channel_name:
                return Response(api_response(message="'channelName' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            channel_name: str = channel_name

            if not code:
                return Response(api_response(message="'code' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if activate == "true":
                activate = True
            elif activate == "false":
                activate = False

            if not activate:
                return Response(api_response(message="'activate' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not logo:
                return Response(api_response(message="'logo' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if Channel.objects.filter(name=channel_name.capitalize()).exists():
                return Response(api_response(message=f"'{channel_name} 'Service already exists", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            channel = Channel.objects.create(name=channel_name.capitalize(), code=code, is_active=activate, logo=logo)

            return Response(
                api_response(message=f"Successfully added a '{channel.name}' Channel", data={}, status=True))
        except (Exception,) as err:
            delete_created_instances(channel)
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# -------------- End ----------------


# ------------------ SuperAdmin Transaction Section ---------------
class SuperAdminTransactionView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request, pk=None):
        """
            Data to be displayed on the SuperAdmin Transaction-Dashboard Page.
        """
        try:
            print('---------')
            overview_data = {}
            query = request.GET.get('query', None)
            sort = request.GET.get('sort', None)
            start_date = request.GET.get('startDate', None)
            end_date = request.GET.get('endDate', None)
            status_query = request.GET.get('status', None)
            download = request.GET.get('download', None)

            download = str(download).lower()
            if download == "true":
                download = True
            elif download == "false":
                download = False
            else:
                download = False

            query_set = Transaction.objects.filter().order_by('-id')
            if query:
                query_set = Transaction.objects.filter(
                    Q(channel__name__icontains=query) | Q(agency__userdetail__name__icontains=query) |
                    Q(amount__contains=query) | Q(owner__userdetail__user__first_name__icontains=query) |
                    Q(owner__userdetail__user__last_name__icontains=query))

            if sort:
                sort: str = sort
                if sort.lower() == 'a-z':
                    query_set = query_set.order_by('service_detail__created_on')
                elif sort.lower() == 'z-a':
                    query_set = query_set.order_by('-service_detail__created_on')

            # ------- status filter--------
            query_set = transaction_queryset_status_filter(status_query, query_set=query_set)

            # ------- Date range filter -------
            query_set = transaction_queryset_date_range_filter(start_date, end_date, query_set)

            serialized_data = SuperAdminTransactionSerializer(query_set, many=True, context={'request': request}).data

            # if download parameter is 'True' fetch all transaction queried to frontend without serialization.

            if download is False:
                serialized_pagination = SuperAdminTransactionSerializer(
                    self.paginate_queryset(query_set, request), many=True, context={'request': request}).data
                serialized_data = self.get_paginated_response(serialized_pagination).data

            overview_data['recentHistory'] = serialized_data

            return Response(api_response(message=f"List of all Transactions", data=overview_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ---------------- End -------------


# ------------ Assign New Agency To Partner Manager ------------------
class SuperAdminAssignAgencyView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request):
        """
            This is method is used to fetch list of Agencies that are assigned to a Particular Partner-Manager.
        """
        try:
            data = {}
            partnerId = request.GET.get('partnerId', None)
            if partnerId is None:
                return Response(
                    api_response(message=f"Error: 'partnerId' parameter is required", data={}, status=False),
                    status=status.HTTP_400_BAD_REQUEST)

            partner_user_instance = User.objects.get(id=partnerId)
            partner_user_detail = partner_user_instance.userdetail

            if partner_user_detail.user_type != 'platform':
                return Response(
                    api_response(message=f"Error: Invalid PartnerManager ID", data={}, status=False),
                    status=status.HTTP_400_BAD_REQUEST)

            # ----------- Main Point to generate the list ------------
            agencies = UserDetail.objects.filter(user_type='agency')
            lists = []

            for agency in agencies:
                if agency.managed_by.filter(id=partner_user_instance.id).exists():
                    lists.append({"agencyId": agency.user.id, "name": agency.name, "status": True})
                else:
                    lists.append({"agencyId": agency.user.id, "name": agency.name, "status": False})
            # ----------- End ------------

            return Response(
                api_response(message=f"Assign Agencies to {partner_user_detail.name}", data=lists, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
            This is method is used
        """
        try:
            success, data = incoming_request_checks(request=request, require_data_field=True)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            partner_id = data.get('partnerId', None)
            agencies = data.get('agencyIdList', [])

            if partner_id is None:
                return Response(
                    api_response(message=f"Error: 'partnerId' parameter is required", data={}, status=False),
                    status=status.HTTP_400_BAD_REQUEST)

            partner = UserDetail.objects.get(user__id=partner_id)

            if not agencies:
                return Response(
                    api_response(message=f"Error: 'agencyIdList' parameter is required", data={}, status=False),
                    status=status.HTTP_400_BAD_REQUEST)

            # ----------- Main Point to generate the list ------------
            # 1- clear partner manager's list.
            partner.manages.clear()

            for agency_id in agencies:
                # Check if agency exists.
                agencies = UserDetail.objects.filter(user__id=agency_id, user_type="agency")
                if agencies.exists() is False:
                    return Response(
                        api_response(message=f"Error: Could not match any Agency with ID '{agency_id}'", status=False),
                        status=status.HTTP_400_BAD_REQUEST)

                agency = UserDetail.objects.get(user__id=agency_id, user_type="agency")
                agency_user = agency.user

                # Update the partner's 'manages' field to include the agency with 'id' passed.
                partner.manages.add(agency_user)

                # Update the agencies 'managed_by' field to include the partner with 'id' passed in request.
                agency.managed_by.add(partner.user)

            # ------------ End ------------

            return Response(
                api_response(message=f"Successfully assigned Agency in list to '{partner.name}' Manager.",
                             data={}, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ------------ END ------------------


# ------------ Super Admin Report Section ------------------
class SuperAdminDashboardView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request):
        """
            This is method is used to fetch Super Admin Dashboard.
            Note: To perform search queries each section will have to have their own specific querysets.
        """
        try:
            data = {}
            transaction_time_query = request.GET.get("transactionTimeQuery", None)
            most_used_channel_time_query = request.GET.get("mostUsedChannelTimeQuery", None)
            service_time_query = request.GET.get("serviceTimeQuery", None)
            verification_time_query = request.GET.get("verificationTimeQuery", None)

            transactions = Transaction.objects.filter()
            amount = 0.0

            for transaction in transactions:
                amount += float(0.0 if transaction.amount is None else transaction.amount)

            data['totalRevenue'] = amount
            data['totalTransaction'] = transactions.count()

            # ----------------- Total End Users ------------------
            users = UserRole.objects.exclude(
                Q(user_role="super-admin") & Q(user_role="partner-manager") & Q(user_role="agency"))
            data['totalEndUser'] = users.count()

            # Total Agencies
            data['totalAgencies'] = UserDetail.objects.filter(user_type="agency").count()

            #  ------------------ Total Transaction verified and not verified with Date Filters------------------
            if transaction_time_query:
                date_ = date_periods(transaction_time_query)
                container1 = []

                agencies = UserRole.objects.filter(user_role="agency")
                for agency in agencies:
                    success_transactions_count = Transaction.objects.filter(Q(agency=agency.user_detail.user,
                                                                              status="success",
                                                                              created_on__date__range=[date_,
                                                                                                       timezone.now().date()])).count()
                    failed_transactions_count = Transaction.objects.filter(Q(agency=agency.user_detail.user,
                                                                             status="failed",
                                                                             created_on__date__range=[date_,
                                                                                                      timezone.now().date()])).count()
                    container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                                       "failed": failed_transactions_count})

                data['agenciesTransactions'] = container1
            else:
                container1 = []

                agencies = UserRole.objects.filter(user_role="agency")
                for agency in agencies:
                    success_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                            status="success").count()
                    failed_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                           status="failed").count()
                    container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                                       "failed": failed_transactions_count})

                data['agenciesTransactions'] = container1

            # ------------------- End of Transaction verified and not verified with Date Filters --------------

            # Revenue (Done) and has No filter.
            container2 = []
            for agency in agencies:
                query = Transaction.objects.filter(agency=agency.user_detail.user, status="success")
                amount = 0.0
                for T in query:
                    amount += float(T.amount)
                container2.append({"name": agency.user_detail.name, "amount": amount})
            data['revenues'] = container2

            # -------------------- Most Used Channels with time filters ------------------------
            if most_used_channel_time_query:
                date_query = date_periods(query=most_used_channel_time_query)

                container3 = []
                channels = Channel.objects.filter()

                for channel in channels:
                    counts = Transaction.objects.filter(
                        Q(channel=channel, created_on__date__range=[date_query, timezone.now().date()])).count()
                    container3.append({"name": channel.name, "count": counts})
                data['mostUsedChannels'] = container3
            else:
                container3 = []
                channels = Channel.objects.filter()

                for channel in channels:
                    counts = Transaction.objects.filter(channel=channel).count()
                    container3.append({"name": channel.name, "count": counts})
                data['mostUsedChannels'] = container3

            # -------------------- End of Most Used Channels with time filters ------------------------

            # ------------------------- Services (Was supposed to be Document) ---------------------------
            if service_time_query:
                container4 = []
                date_query = date_periods(query=most_used_channel_time_query)
                service_details = ServiceDetail.objects.filter()

                for service_detail in service_details:
                    counts = Transaction.objects.filter(Q(service_detail=service_detail,
                                                          created_on__date__range=[date_query,
                                                                                   timezone.now().date()])).count()
                    container4.append({"name": service_detail.service.name, "count": counts})
                data['serviceUsed'] = container4
            else:
                container4 = []
                service_details = ServiceDetail.objects.filter()

                for service_detail in service_details:
                    counts = Transaction.objects.filter(service_detail=service_detail).count()
                    container4.append({"name": service_detail.service.name, "count": counts})

                data['serviceUsed'] = container4

            # ------------------------- End: Services (Was supposed to be Document) ---------------------------

            # ------------------- Verification history with time filter -------------------
            recent_transactions = Transaction.objects.filter()
            if verification_time_query:
                date_query = date_periods(query=verification_time_query)

                recent_transactions = recent_transactions.filter(
                    Q(created_on__date__range=[date_query, timezone.now().date()]))[:10]
                data['verificationTransactions'] = VerificationTransactionSerializer(recent_transactions,
                                                                                     many=True).data
            else:
                recent_transactions = recent_transactions[:10]
                data['verificationTransactions'] = VerificationTransactionSerializer(recent_transactions,
                                                                                     many=True).data

            # ------------------- END: Verification history with time filter -------------------

            return Response(api_response(message=f"", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# ------------ END ------------------


# Dashboard Break Down Pending: [Filters]
class DashboardBreakDownOfRevenueView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request):
        """
            This view gives a break-down of the Revenue on the SuperAdmin Page.
        """
        try:
            data = {}
            query = request.GET.get("query", None)
            all_time_query = request.GET.get("allTimeQuery", None)
            start_date_query = request.GET.get("startDateQuery", None)
            end_date_query = request.GET.get("endDateQuery", None)

            query_set = UserRole.objects.filter(user_role="agency").order_by('id')
            if query:
                query_set = UserRole.objects.filter(user_role="agency", user_detail__name__icontains=query).order_by(
                    '-id')

            if start_date_query and end_date_query:
                query_set = query_set.filter(
                    user_detail__user__date_joined__date__range=[start_date_query, end_date_query])

            if all_time_query:
                date_ = date_periods(query=all_time_query)
                query_set = query_set.filter(user_detail__user__date_joined__date__range=[date_, timezone.now().date()])

            serialized_pagination = DashboardBreakDownSerializer(self.paginate_queryset(query_set, request),
                                                                 many=True).data
            paginated_response = self.get_paginated_response(serialized_pagination).data
            data.update({"breakDown": paginated_response})
            return Response(api_response(message=f"Break Down of Revenue", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ------------ END ------------------


# ------------ Super Admin Report Section ------------------
class SuperAdminReportView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request):
        """
            This method is used to fetch Super Admin Report.
        """
        try:
            success, msg = get_incoming_request_checks(request=request)
            if not success:
                return Response(api_response(message=msg, data={}, status=True))

            user_category_time_query = request.GET.get("userCategoryTimeQuery", None)
            verified_document_time_query = request.GET.get("verifiedDocumentTimeQuery", None)
            verification_query = request.GET.get("verificationQuery", None)

            data = {}
            user_category_count = []
            channel_usage_count = []
            verified_document = []
            channel_document_verified_document = []

            # ------------------- User categories (A) -----------------------

            # Add more roles if more 'user_roles' has been added to the database.

            roles = ['partner-manager', 'individual', 'developer', 'agency', 'sub-agency', 'corporate-business',
                     'individual']  # 'sub-corporate-business'
            user_roles = UserRole.objects.filter()
            channels = Channel.objects.filter()

            # If query parameter for time filter is passed.
            if user_category_time_query:
                date_ = date_periods(query=user_category_time_query)
                q = Q(created_on__date__range=[date_, timezone.now().date()])

                for each_role in roles:
                    all_roles = user_roles.filter(Q(user_role=each_role) & q)
                    user_category_count.append({"name": each_role.capitalize(), "count": all_roles.count()})

                data['userCategories'] = user_category_count

                # ---------- User categories (B) -----------
                """
                    This part was supposed to fetch out the user-categories that uses the different channels.
                """
                for channel in channels:
                    counts = Transaction.objects.filter(Q(channel=channel) & q).count()
                    channel_usage_count.append({"name": channel.name, "count": counts})

                data['userCategoryChannelCount'] = channel_usage_count
                # ------------------- User categories (ENDS) ----------------------------

            else:
                for each_role in roles:
                    all_roles = user_roles.filter(user_role=each_role)
                    user_category_count.append({"name": each_role.capitalize(), "count": all_roles.count()})

                data['userCategories'] = user_category_count

                # ---------- User categories (B) -----------
                """
                    This part was supposed to fetch out the user-categories that uses the different channels.
                """
                for channel in channels:
                    counts = Transaction.objects.filter(channel=channel).count()
                    channel_usage_count.append({"name": channel.name, "count": counts})

                data['userCategoryChannelCount'] = channel_usage_count
                # ------------------- User categories (ENDS) ----------------------------

            # If query parameter for time filter is passed.
            if verified_document_time_query:
                date_ = date_periods(query=verified_document_time_query)
                q = Q(created_on__date__range=[date_, timezone.now().date()])

                # ------------------- Verified Documents (A) --------------------
                agencies = UserRole.objects.filter(user_detail__user_type="agency")
                for agency in agencies:
                    TR = Transaction.objects.filter(Q(agency=agency.user_detail.user) & Q(status="success") & q).count()
                    verified_document.append({"name": agency.user_detail.name, "count": TR})

                data['verifiedDocument'] = verified_document

                # ------------- Verified Document (B) --------------------
                channels1 = Channel.objects.filter()
                """
                    This part was supposed to fetch out the different channels count used in verifying documents.
                """
                for channel in channels1:
                    c = Transaction.objects.filter(Q(channel=channel) & q).count()
                    channel_document_verified_document.append({"name": channel.name, "count": c})

                data['verifiedDocumentChannelCount'] = channel_document_verified_document
                # --------------------------------------------------

            else:
                # ------------------- Verified Documents (A) --------------------
                agencies = UserRole.objects.filter(user_detail__user_type="agency")
                for agency in agencies:
                    TR = Transaction.objects.filter(agency=agency.user_detail.user, status="success").count()
                    verified_document.append({"name": agency.user_detail.name, "count": TR})

                data['verifiedDocument'] = verified_document

                # ------------- Verified Document (B) --------------------
                channels1 = Channel.objects.filter()
                """
                    This part was supposed to fetch out the different channels count used in verifying documents.
                """
                for channel in channels1:
                    c = Transaction.objects.filter(channel=channel).count()
                    channel_document_verified_document.append({"name": channel.name, "count": c})

                data['verifiedDocumentChannelCount'] = channel_document_verified_document
                # --------------------------------------------------

            #  ------------------ Total Transaction verified and not verified ------------------
            container1 = []

            if verification_query:
                date_ = date_periods(query=verified_document_time_query)
                q = Q(created_on__date__range=[date_, timezone.now().date()])

                agencies = UserRole.objects.filter(user_role="agency")
                for agency in agencies:
                    success_transactions_count = Transaction.objects.filter(
                        Q(agency=agency.user_detail.user, status="success") & q).count()
                    failed_transactions_count = Transaction.objects.filter(
                        Q(agency=agency.user_detail.user, status="failed"), q).count()
                    container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                                       "failed": failed_transactions_count})

                data['verification'] = container1
            else:
                agencies = UserRole.objects.filter(user_role="agency")
                for agency in agencies:
                    success_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                            status="success").count()
                    failed_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                           status="failed").count()
                    container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                                       "failed": failed_transactions_count})

                data['verification'] = container1

            return Response(api_response(message=f"", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ------------ END ------------------


# ---------- Add Services to Agency Profile ------------
class SuperAdminAddServiceView(APIView):
    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def get(self, request, agencyId=None):
        try:
            success, data = get_incoming_request_checks(request=request)
            # To get request, we now need to get 'request.data'.

            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            if agencyId is None:
                return Response(api_response(message="'agencyId' parameter is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            agency_user_instance = User.objects.get(id=agencyId)
            if agency_user_instance.userdetail.user_type != "agency" and agency_user_instance.userdetail.userrole.user_role != "agency":
                return Response(api_response(message="'agencyId' is not an Agency", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            all_service_detail = Service.objects.filter()
            serializer = SuperAdminExistingAndNonExistingServicesSerializer(all_service_detail, many=True, context={
                "agency_user_instance": agency_user_instance}).data

            return Response(
                api_response(message=f"List of existing and non-existing Services", data=serializer, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
            This endpoint is used to add Services to an Agency.
            It requires the Agency's ID and a list of Service ID to  be added.
        """
        try:
            service_detail = None
            service = None
            # This will no longer check for 'data' field since 'require_data_field' is 'False' which is default to True.
            success, data = incoming_request_checks(request=request)
            # To get request, we now need to get 'request.data'.

            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            agency_id = data.get("agencyId", None)
            service_ids = data.get("serviceIds", [])

            if agency_id is None:
                return Response(api_response(message="'agency_id' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not service_ids:
                return Response(api_response(message="'serviceIds' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            data = {}
            # Get the agency with 'agency_id'
            user_role = UserRole.objects.filter(user_role='agency', user_detail__user_type="agency",
                                                user_detail__user__id=agency_id)
            if not user_role.exists():
                return Response(api_response(message=f"Agency ID '{agency_id}' does not match any Agency",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            user_role = user_role.last()
            agency = user_role.user_detail.user

            for _id in service_ids:
                service_detail = None
                try:
                    service = Service.objects.get(id=_id)
                    # Check if service and agency instance is already present in the ServiceDetail Model.
                    if ServiceDetail.objects.filter(service=service, agency=agency).exists():
                        return Response(api_response(message=f"Service has already been added to this Agency's profile",
                                                     status=False),
                                        status=status.HTTP_400_BAD_REQUEST)

                    # Create a service detail for the Agency.
                    name = f"{service.name} by {agency.userdetail.name}"
                    service_detail = ServiceDetail.objects.create(service=service, agency=agency, name=name)

                except (Exception,) as err:
                    if service_detail is not None:
                        service_detail.delete()
                    return Response(api_response(message=f"Error: {err}", status=False),
                                    status=status.HTTP_400_BAD_REQUEST)

            return Response(api_response(message=f"Successfully Added Service(s) to {agency.userdetail.name}", data={},
                                         status=True))
        except (Exception,) as err:
            delete_created_instances(service)
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
            This endpoint is used to activate/ de-activate Agency's service.
        """
        try:
            service_detail = None
            service = None
            # This will no longer check for 'data' field since 'require_data_field' is 'False' which is default to True.
            success, data = incoming_request_checks(request=request)
            # To get request, we now need to get 'request.data'.

            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            agency_id = data.get("agencyId", None)
            service_detail_id = data.get("serviceDetailId", None)
            activate = data.get("activate", None)

            if agency_id is None:
                return Response(api_response(message="'agencyId' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if service_detail_id is None:
                return Response(api_response(message="'serviceDetailId' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if activate is None:
                return Response(api_response(message="'activate' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            # Get the agency with 'agency_id'
            user_role = UserRole.objects.filter(user_role='agency', user_detail__user_type="agency",
                                                user_detail__user__id=agency_id)

            if not user_role.exists():
                return Response(api_response(message=f"Agency ID '{agency_id}' does not match any Agency",
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            user_role = user_role.last()
            agency = user_role.user_detail.user

            service_detail = ServiceDetail.objects.filter(id=service_detail_id, agency=agency)

            if not service_detail.exists():
                return Response(
                    api_response(message=f"No ServiceDetail matches the given 'serviceDetailId' and 'agency'",
                                 status=False), status=status.HTTP_400_BAD_REQUEST)

            service_detail = ServiceDetail.objects.get(id=service_detail_id, agency=agency)
            service_detail.is_available = activate
            service_detail.save()

            if service_detail.is_available is True:
                # Send Activation Email to Agency that has the service.
                service_activation_msg(context={"service_detail": service_detail, "request": request})
            else:
                # Send De-activation Email to Agency that has the service.
                service_deactivation_msg(context={"service_detail": service_detail, "request": request})

            return Response(api_response(message=f"Successfully updated the status of {service_detail.name} Service",
                                         data={}, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ------------ END ---------------------


# ----- ADD OR CREATE PAYMENT GATEWAY VIEW TO THE SYSTEM E.G PAYSTACK, FLUTTERWAVE ...
class SuperAdminCreatePaymentGateWayView(APIView):
    """
        This is view is used to add / create Payment Gateway. E.G PayStack, FlutterWave.
    """

    permission_classes = [IsAuthenticated, permission.IsSuperAdmin]

    def post(self, request):
        payment_gateway = None
        try:
            success, data = incoming_request_checks(request=request, require_data_field=False)
            # To get request, we now need to get 'request.data'.

            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            payment_gate_way_name = request.data.get("paymentGateWayName", None)
            payment_logo = request.data.get("paymentLogo", None)

            if payment_gate_way_name is None:
                return Response(api_response(message="'paymentGateWayName' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if payment_logo is None:
                return Response(api_response(message="'paymentLogo' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            # Check if payment gateway with 'payment_gate_way_name' exist in database.
            payment_gate_way_name: str = payment_gate_way_name.capitalize()
            find = PaymentGateWay.objects.filter(payment_gateway_name__iexact=payment_gate_way_name)

            if find.exists():
                return Response(api_response(message=f"A Payment Gateway with this name already exists", status=False,
                                             data={}), status=status.HTTP_400_BAD_REQUEST)

            payment_gateway = PaymentGateWay.objects.create(
                payment_gateway_name=payment_gate_way_name, payment_gateway_logo=payment_logo,
                payment_gateway_slug=str(payment_gate_way_name).lower()
            )
            return Response(api_response(message=f"Successfully Added Payment Gateway", status=True, data={}))
        except (Exception,) as err:
            delete_created_instances(payment_gateway)
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ---------------------------------------------------

