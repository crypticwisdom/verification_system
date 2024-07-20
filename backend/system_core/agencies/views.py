import ast, secrets
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from account.emails import sub_agency_account_creation_msg, sub_agency_service_addition_mail
from agencies.utils import agency_revenue_section, user_data_on_agency_report_section, \
    channel_data_on_agency_report_section, verification_data_on_agency_report_section, \
    transaction_data_on_agency_report_section
from super_admin.serializers import SharedPMandSPAChannelImageSerializer
from util.paginations import CustomPagination
from util.utils import api_response, incoming_request_checks, phone_number_check, validate_email, \
    delete_created_instances, get_incoming_request_checks, date_periods
from account import permission
from account.models import Transaction, Channel, User, UserDetail, UserRole, State, Service, ServiceDetail
from agencies.serializers import AgencyVerificationTransactionSerializer, AgencySubAgencyListSerializer, \
    AgencyGetSubAgencyProfileSerializer, AgencyTransactionSerializer, AgencyServiceDetailsSerializer, \
    AgencyExistingAndNonExistingServicesSerializer, AgencySubAgencyServiceSerializer
from django.utils import timezone

from account.models import ClientPaymentGateWayDetail


# from shortcuts

# Dashboard View for Agency Page
class AgencyDashboardView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request):
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            over_view_time_query = request.GET.get("overViewTimeQuery", None)
            revenue_time_query = request.GET.get("revenueTimeQuery", None)
            channel_usage_time_query = request.GET.get("channelUsageTimeQuery", None)
            verification_time_query = request.GET.get("verificationTimeQuery", None)

            data = {}
            query_set = Transaction.objects.filter(agency__userdetail__user=request.user)
            amount = 0.0

            # # ------- Overview ------------
            if over_view_time_query:
                date_query = date_periods(query=over_view_time_query)

                query_set = query_set.filter(Q(created_on__date__range=[date_query, timezone.now().date()]))
                for transaction in query_set:
                    amount += float(transaction.amount)

                data['totalRevenue'] = amount

                # 1a. Total Users
                data['totalUsers'] = query_set.count()

                # 1b. Successful Transaction
                data['successfulTransaction'] = query_set.filter(status="success").count()

                # 1c. Failed Transaction
                data['failedTransaction'] = query_set.filter(status="failed").count()
            else:
                for transaction in query_set:
                    amount += float(transaction.amount)

                data['totalRevenue'] = amount

                # 1a. Total Users
                data['totalUsers'] = query_set.filter().count()

                # 1b. Successful Transaction
                data['successfulTransaction'] = query_set.filter(status="success").count()

                # 1c. Failed Transaction
                data['failedTransaction'] = query_set.filter(status="failed").count()
            # ------- End: Overview -------

            # 2a. Revenue
            if revenue_time_query:
                date_query = date_periods(query=revenue_time_query)

                revenue_container = []
                # Exclude users with 'agency' and 'platform' user-type
                exclude_user_type = Q(user_type="agency") | Q(user_type="platform")

                agency_users = UserDetail.objects.exclude(exclude_user_type).order_by('-id')
                amount_generated = 0.0
                for agency_user in agency_users:
                    transactions = Transaction.objects.filter(Q(agency=request.user, owner=agency_user.user,
                                                                created_on__date__range=[date_query,
                                                                                         timezone.now().date()]))
                    for transaction in transactions:
                        amount_generated += float(transaction.amount)

                    revenue_container.append(
                        {f"agencyId": agency_user.user.id, f"name": f"{agency_user.name}", "totalAmount": amount})
                data['revenueData'] = revenue_container
            else:
                revenue_container = []
                # Exclude users with 'agency' and 'platform' user-type
                exclude_user_type = Q(user_type="agency") | Q(user_type="platform")

                agency_users = UserDetail.objects.exclude(exclude_user_type).order_by('-id')
                amount_generated = 0.0
                for agency_user in agency_users:
                    transactions = Transaction.objects.filter(agency=request.user, owner=agency_user.user)
                    for transaction in transactions:
                        amount_generated += float(transaction.amount)

                    revenue_container.append(
                        {f"agencyId": agency_user.user.id, f"name": f"{agency_user.name}", "totalAmount": amount})
                data['revenueData'] = revenue_container

            # 2b. Channel Usage
            if channel_usage_time_query:
                date_query = date_periods(query=channel_usage_time_query)

                channel_container = []
                channels = Channel.objects.filter()
                for channel in channels:
                    transaction = Transaction.objects.filter(
                        Q(channel=channel, created_on__date__range=[date_query, timezone.now().date()]))
                    channel_container.append({f"channelId": f"{channel.id}", f"channelName": f"{channel.name}",
                                              "usageCount": transaction.count()})
                data['channelUsage'] = channel_container
            else:
                channel_container = []
                channels = Channel.objects.filter()
                for channel in channels:
                    transaction = Transaction.objects.filter(
                        channel=channel)
                    channel_container.append({f"channelId": f"{channel.id}", f"channelName": f"{channel.name}",
                                              "usageCount": transaction.count()})
                data['channelUsage'] = channel_container

            # 3 -------Recent 10 Verification History --------
            if verification_time_query:
                date_query = date_periods(query=verification_time_query)

                recent_transactions = Transaction.objects.filter(
                    Q(agency=request.user, created_on__date__range=[date_query, timezone.now().date()]))[:10]
            else:
                recent_transactions = Transaction.objects.filter(agency=request.user)[:10]
            data['verificationTransactions'] = AgencyVerificationTransactionSerializer(recent_transactions,
                                                                                       many=True).data
            return Response(api_response(message=f"{request.user.first_name} Dashboard data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


# Sub-Agency View for Sub-Agency page.
class AgencySubAgenciesView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request):
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            query = request.GET.get("query", None)
            a_order = request.GET.get("order", None)
            sub_agencies = UserRole.objects.filter(
                user_role="sub-agency", user_detail__user_type="agency", user_detail__parent_agency=request.user)
            start_date = request.GET.get("startDate", None)
            end_date = request.GET.get("endDate", None)

            if start_date and end_date:
                sub_agencies = sub_agencies.filter(
                    Q(user_detail__user__date_joined__date__range=[start_date, end_date]))

            if query:
                query: str = query.lower()
                sub_agencies = sub_agencies.filter(
                    Q(user_detail__name__icontains=query) | Q(user_detail__user__email__icontains=query) |
                    Q(user_detail__email__icontains=query) | Q(user_detail__approved__iexact=query))

            if a_order:  # alphabetical_order
                a_order: str = a_order.lower()
                if a_order in ['a-z', 'z-a']:
                    sub_agencies = sub_agencies.order_by(
                        'user_detail__name') if a_order == 'a-z' else sub_agencies.order_by('-user_detail__name')

            data = AgencySubAgencyListSerializer(sub_agencies, many=True).data
            return Response(api_response(message=f"Sub Agency Section Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


# Sub Agency Profile
class AgencyGetSubAgencyProfileView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request, pk=None):
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            data = {}
            if pk is None:
                return Response(api_response(message=f"Error: 'subAgencyId' parameter is required.", data={},
                                             status=False), status=status.HTTP_400_BAD_REQUEST)

            transaction_name_query = request.GET.get('transactionNameQuery', None)
            order_query = request.GET.get('orderQuery', None)

            # ------------------------- Sub Agency Profile --------------------------
            sub_agency_detail = UserRole.objects.filter(user_detail__user__id=pk)

            if not sub_agency_detail.exists():
                return Response(api_response(message=f"Error: No Sub-Agency matches 'ID'",
                                             data={}, status=False), status=status.HTTP_400_BAD_REQUEST)
            sub_agency_detail = UserRole.objects.get(user_detail__user__id=pk)

            data.update({"agencyProfile": AgencyGetSubAgencyProfileSerializer(sub_agency_detail, many=False,
                                                                              context={'request': request}).data})

            # ------------------------- Over View ------------------------
            response_value = {}
            sub_agencies = UserRole.objects.filter(user_role='sub-agency', user_detail__user_type="agency",
                                                   user_detail__user=request.user)
            container = []

            # --------- Overall revenue -----------
            overAllAmount = 0.00
            for sub_agency in sub_agencies:
                overall_transactions = Transaction.objects.filter(owner=sub_agency)
                overAllAmount += float(overall_transactions.amount)

            container.append({"name": "Overall Revenue", 'amount': overAllAmount})
            # -------- Overall revenue END ---------

            # -------- Channel Amount -----------
            channels = Channel.objects.filter()
            for channel in channels:
                overall_transactions = Transaction.objects.filter(agency=request.user, channel=channel, owner=sub_agency_detail.user_detail.user)

                total_amount_per_channel = 0.00
                for trans_amount in overall_transactions:
                    total_amount_per_channel += float(trans_amount.amount)
                container.append({"name": channel.name, 'amount': total_amount_per_channel, "channelLogo": ""})
            # ------- Channel Amount END ----------

            # ------- Overview Section Data ---------
            data.update({"overView": container})

            # ---------- Service Section ------------
            sub_agencies_service_details = ServiceDetail.objects.filter(agency=sub_agency_detail.user_detail.user)
            data.update({"services": AgencySubAgencyServiceSerializer(sub_agencies_service_details, many=True,
                                                                      context={"request": request}).data})

            # ------------- Transaction and Query -------------
            sub_agency_transactions = Transaction.objects.filter(owner=sub_agency_detail.user_detail.user)

            if transaction_name_query:
                q = Q(full_name__icontains=transaction_name_query) | Q(document__icontains=transaction_name_query)
                sub_agency_transactions = sub_agency_transactions.filter(q)

            order_query: str = order_query.lower() if order_query is not None else None
            if order_query:
                if order_query == "a-z":
                    sub_agency_transactions = sub_agency_transactions.order_by('created_on')

                elif order_query == "z-a":
                    sub_agency_transactions = sub_agency_transactions.order_by('-created_on')

            data.update({"transactionHistory": AgencyTransactionSerializer(sub_agency_transactions, many=True).data})
            return Response(api_response(message=f"'{sub_agency_detail.user_detail.name}' Profile",
                                         data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


# ----------------- Agency Channel Section () --------------------
class AgencyChannelView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request, pk=None):
        """
            Data to be displayed on the Agency Channel-Dashboard Page.
        """
        try:
            query = request.GET.get('query', None)
            data1 = []
            overview_data = {}
            channels = Channel.objects.filter()

            agency_transactions_query = Transaction.objects.filter(agency=request.user).order_by('-id')
            for channel in channels:
                transaction_count = agency_transactions_query.filter(channel=channel).count()
                data1.append({"channelName": channel.name, "totalCount": transaction_count,
                              "channelLogo": SharedPMandSPAChannelImageSerializer(channel, many=False,
                                                                                  context={"request": request}).data,
                              "channelId": channel.id})

            overview_data['channelUsage'] = data1

            # ---------- Get list of Transactions ---------

            # search by channel-name, status
            if query:
                query: str = query.lower()
                agency_transactions_query = agency_transactions_query.filter(
                    Q(channel__name__icontains=query) | Q(status__icontains=query)
                )

            start_date = request.GET.get("startDate", None)
            end_date = request.GET.get("endDate", None)

            if start_date and end_date:
                agency_transactions_query = agency_transactions_query.filter(
                    Q(created_on__date__range=[start_date, end_date]))

            # ---------- END ---------------

            serialized_pagination = AgencyTransactionSerializer(
                self.paginate_queryset(agency_transactions_query, request), many=True,
                context={'request': request}).data
            paginated_response = self.get_paginated_response(serialized_pagination).data
            overview_data['recentHistory'] = paginated_response

            return Response(api_response(message=f"Channels", data=overview_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# -------------- End ----------------


# ------------ Transaction (Done) -------------
class AgencyTransactionView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request, pk=None):
        try:
            query = request.GET.get("query", None)
            agency_transactions_query = Transaction.objects.filter(agency=request.user).order_by('-id')

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

            if start_date and end_date:
                agency_transactions_query = agency_transactions_query.filter(
                    Q(created_on__date__range=[start_date, end_date]))

            if query:
                query: str = query.lower()
                agency_transactions_query = agency_transactions_query.filter(
                    Q(channel__name__icontains=query) | Q(status__iexact=query))

            response = AgencyTransactionSerializer(agency_transactions_query, many=True, context={'request': request}).data
            if download is False:
                serialized_pagination = AgencyTransactionSerializer(
                    self.paginate_queryset(agency_transactions_query, request), many=True,
                    context={'request': request}).data
                response = self.get_paginated_response(serialized_pagination).data

            return Response(api_response(message=f"Agency Transactions Record",
                                         data=response, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


# ---------- Create Sub-Agencies (Done) -----------
class AgencyCreateSubAgencyView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def post(self, request):
        channel, user, user_detail, user_role, service_detail, service_detail_instance = (None,) * 6
        try:
            success, data = incoming_request_checks(request=request, require_data_field=False)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            name = request.data.get('name', None)
            logo = request.FILES.get('logo', None)
            approve = request.data.get('approve', None)
            admin_email = request.data.get('adminEmail', None)
            state_id = request.data.get('stateId', None)
            phone = request.data.get('phone', None)
            admin_last_name = request.data.get('adminLastName', None)
            admin_first_name = request.data.get('adminFirstName', None)
            address = request.data.get('address', None)
            agency_email = request.data.get('agencyEmail', None)
            service_detail_ids = request.data.get('serviceDetailIds', None)

            name: str = name
            if not name:
                return Response(api_response(message="'name' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            if not logo:
                return Response(api_response(message="'logo' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if approve == "true":
                approve = True
            elif approve == "false":
                approve = False

            if not approve:
                return Response(api_response(message="'approve' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not phone:
                return Response(api_response(message="'phone' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            success, phone_response = phone_number_check(phone_number=phone)
            if not success:
                return Response(api_response(message=phone_response, status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            phone = phone_response

            if not admin_email:
                return Response(api_response(message="'adminEmail' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            admin_email_is_valid = validate_email(email=admin_email)

            if not admin_email_is_valid:
                return Response(api_response(message="Invalid 'adminEmail' email field", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not agency_email:
                return Response(api_response(message="'agencyEmail' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            agency_email_is_valid = validate_email(email=agency_email)

            if not agency_email_is_valid:
                return Response(api_response(message="Invalid 'agencyEmail' email field", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            if not admin_first_name:
                return Response(api_response(message="'adminFirstName' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            admin_first_name: str = admin_first_name.capitalize()

            if not admin_last_name:
                return Response(api_response(message="'adminLastName' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            admin_last_name: str = admin_last_name.capitalize()

            if not state_id:
                return Response(api_response(message="'stateId' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)
            state = State.objects.get(pk=state_id)

            if not address:
                return Response(api_response(message="'address' field is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            service_detail_ids = ast.literal_eval(service_detail_ids)

            generated_password = f"{secrets.token_urlsafe(6)}A1!{secrets.token_urlsafe(4)}"
            hashed = make_password(password=generated_password)
            slug = secrets.token_urlsafe(15)
            user = User.objects.create(first_name=admin_first_name, last_name=admin_last_name, email=admin_email,
                                       password=hashed, slug=slug)
            user_detail = UserDetail.objects.create(user=user, phone_number=phone, user_type='agency',
                                                    name=name.capitalize(), email=agency_email,
                                                    parent_agency=request.user,
                                                    created_by=request.user, approved=approve, logo=logo, state=state)
            user_detail.managed_by.add(request.user)
            user_role = UserRole.objects.create(user_detail=user_detail, user_role='sub-agency')

            client_payment = ClientPaymentGateWayDetail.objects.get(user_detail=request.user.userdetail)

            # Add services of the agency to the newly created Sub-Agency
            agency_service_details = ServiceDetail.objects.filter(agency=request.user)
            for service_detail_id in service_detail_ids:
                service_detail = ServiceDetail.objects.filter(id=service_detail_id)

                # Check if this ID exists.
                if not service_detail.exists():
                    delete_created_instances(user, user_detail, user_role)
                    return Response(
                        api_response(message=f"No ServiceDetail with ID '{service_detail_id}'", status=False),
                        status=status.HTTP_400_BAD_REQUEST)

                service_detail = service_detail.last()

                # client_payment = ClientPaymentGateWayDetail.objects.get(user_detail=user_detail)
                if service_detail.agency.id == request.user.id:
                    service_detail_instance = ServiceDetail.objects.create(
                        service=service_detail.service, agency=user, parent_agency=request.user.userdetail,
                        service_detail_code=service_detail.service_detail_code,
                        name=f"{service_detail.service.name} by {name}", price=service_detail.price)

                for channel in service_detail.channel_available.all():
                    if service_detail_instance is not None:
                        service_detail_instance.channel_available.add(channel)

            # send email to inform admin and agency.managed_by
            sub_agency_account_creation_msg(context={"user": user, "password": generated_password})
            return Response(
                api_response(message=f"Successfully created '{name}' Sub-Agency", data={}, status=True))
        except (Exception,) as err:
            delete_created_instances(user, user_detail, user_role, service_detail, service_detail_instance)
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
            Used for fetching a list of all ServiceDetails that belongs to this particular Agency.
            -  This endpoint is called When an Agency wants to create Sub-Agency, to get list of ServiceDetails
                that belongs to this particular Agency.
        """
        try:
            success, data = get_incoming_request_checks(request)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            agencies_services = ServiceDetail.objects.filter(agency=request.user).order_by('id')
            serialized_data = AgencyServiceDetailsSerializer(agencies_services, many=True, context={'request': request})
            return Response(
                api_response(message=f"List of Agency's Service", data=serialized_data.data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# ---------- Report -----------
class AgencyReportView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request, pk=None):
        try:
            success, msg = get_incoming_request_checks(request=request)
            if not success:
                return Response(api_response(message=f"{msg}", data={}, status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            revenue_time_query = request.GET.get("revenueTimeQuery", None)
            user_and_channel_time_query = request.GET.get("userAndChannelTimeQuery", None)
            # verified_document_time_query = request.GET.get("verifiedDocumentTimeQuery", None)
            verification_query = request.GET.get("verificationQuery", None)

            data = dict()

            # ------------------- Revenue --------------------
            data['revenueData'] = agency_revenue_section(revenue_time_query=revenue_time_query)

            # ------------------- Channel Usage Count (A) -----------------------
            data['agencyChannelUsageCount'] = channel_data_on_agency_report_section(request=request,
                                                                                    time_query_string=user_and_channel_time_query)

            # ---------- User Categories Usage (B) -----------
            data['userCategoryUsageCount'] = user_data_on_agency_report_section(request=request,
                                                                                time_query_string=user_and_channel_time_query)

            # -------------- Verified Section -----------------
            data['verifiedDocument'] = verification_data_on_agency_report_section(request=request,
                                                                                  verified_query_string=verification_query)

            # ---------
            # d = {}
            # s = []
            # channels = Channel.objects.filter()
            # for c in channels:
            #     t = Transaction.objects.filter(channel=c, agency=request.user)
            #     for n in t:
            #         s.append({"channelName": c.name, 'channelCount': t.count(), 'document': ''})
            # data.update({"documentVerifiedPerChannel": s})
            # ---------

            # -------------- Transactions Count -------------------
            data.update({"transactionCounts": transaction_data_on_agency_report_section(request)})

            return Response(api_response(message=f"Agency Reports", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class AgencyExistingAndNonExistingServiceView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsAgency]

    def get(self, request, sub_agency_id=None):
        """
            Used for listing out service-details that has been assigned to the sub-agency with 'sub_agency_id'.
        """
        try:
            success, data = get_incoming_request_checks(request=request)
            # To get request, we now need to get 'request.data'.

            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            if sub_agency_id is None:
                return Response(api_response(message="'subAgencyId' parameter is required", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            agency_user_instance = request.user
            sub_agency_user_instance = User.objects.get(id=sub_agency_id)

            if sub_agency_user_instance.userdetail.user_type != "agency" or sub_agency_user_instance.userdetail.userrole.user_role != "sub-agency":
                return Response(api_response(message="'subAgencyId' is not a Sub-Agency", status=False),
                                status=status.HTTP_400_BAD_REQUEST)

            service_details = ServiceDetail.objects.filter(agency=agency_user_instance)
            serializer = AgencyExistingAndNonExistingServicesSerializer(service_details, many=True, context={
                "sub_agency_user_instance": sub_agency_user_instance}).data

            return Response(
                api_response(message=f"Existing and non-existing "
                                     f"ServiceDetail related to '{sub_agency_user_instance.userdetail.name}'", data=serializer, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        service_detail_instance = None
        try:
            success, data = incoming_request_checks(request=request, require_data_field=False)
            if not success:
                return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)

            service_detail_ids = data.get('serviceDetailIds', [])
            sub_agency_id = data.get('subAgencyId', None)

            if type(service_detail_ids) is not list or not service_detail_ids:
                return Response(
                    api_response(message="'serviceDetailIds' field must contain a list/array of serviceDetailIds",
                                 status=False), status=status.HTTP_400_BAD_REQUEST)

            sub_agency = User.objects.get(id=sub_agency_id)
            # agency_service_details = ServiceDetail.objects.filter(agency=request.user)

            all_service_detail_of_sub_agency = ServiceDetail.objects.filter(agency=sub_agency,
                                                                            parent_agency=request.user.userdetail)

            # Clear all ServiceDetail instance that belongs to the sub-agency, before create new ones from the list.
            for service_detail in all_service_detail_of_sub_agency:
                service_detail.delete()

            for service_detail_id in service_detail_ids:
                service_detail = ServiceDetail.objects.filter(id=service_detail_id)

                # Check if this ID exists.
                if not service_detail.exists():
                    return Response(
                        api_response(message=f"No ServiceDetail with ID '{service_detail_id}'", status=False),
                        status=status.HTTP_400_BAD_REQUEST)

                service_detail = service_detail.last()

                # check if this agency (user) is the owner of the service detail being added to the sub-agency
                if service_detail.agency.id == request.user.id:
                    service_detail_instance = ServiceDetail.objects.create(
                        service=service_detail.service, agency=sub_agency, parent_agency=request.user.userdetail,
                        service_detail_code=service_detail.service_detail_code,
                        name=f"{service_detail.service.name} by {sub_agency.userdetail.name}")

                for channel in service_detail.channel_available.all():
                    if service_detail_instance is not None:
                        service_detail_instance.channel_available.add(channel)

            # send email to inform SubAgency about the newly added service.
            sub_agency_service_addition_mail(
                context={"sub_agency_user": sub_agency, "service_detail_ids": service_detail_ids})
            return Response(api_response(message=f"Successfully added '{len(service_detail_ids)}' "
                                                 f"Service details to '{sub_agency.userdetail.name}'", data={}, status=True))
        except (Exception,) as err:
            delete_created_instances(service_detail_instance)
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


