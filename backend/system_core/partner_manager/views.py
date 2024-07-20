from django.shortcuts import render
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from account import permission
from rest_framework import status
from account.models import User, UserDetail, UserRole, Service, State, Channel, Transaction, ServiceDetail
from django.db.models import Q
from .serializers import PMAgencySerializer, PMTransactionSerializer, PMAgencyDetailSerializer
from super_admin.serializers import VerificationTransactionSerializer, SharedPMandSPAChannelImageSerializer
from util.paginations import CustomPagination
from util.utils import api_response, date_periods
from super_admin.serializers import SuperAdminAgencyDetailSerializer, SuperAdminAgencyServiceSerializer, \
    SuperAdminTransactionSerializer
from .utils import partner_manager_report_and_filter, partner_manager_report_verification_section, \
    partner_manager_report_channel_verified_section, partner_manager_report_user_verified_section, \
    partner_manager_report_user_category, partner_manager_report_user_channel, partner_manager_dashboard_transaction, \
    partner_manager_dashboard_revenue, partner_manager_dashboard_channel_usage, partner_manager_dashboard_service_used, \
    partner_manager_dashboard_verification_history


# Create your views here.

# ------------  ------------------
class PMDashBoardView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsPartnerManager]

    def get(self, request):
        """
            This view is used for displaying partner-manager's dashboard data.
        """
        try:
            overview_time_query = request.GET.get("overviewTimeQuery", None)
            transaction_time_query = request.GET.get("transactionTimeQuery", None)
            revenue_time_query = request.GET.get("revenueTimeQuery", None)
            channel_usage_time_query = request.GET.get("channelUsageTimeQuery", None)
            service_used_time_query = request.GET.get("serviceUsedTimeQuery", None)
            verification_transactions_time_query = request.GET.get("verificationTransactionsTimeQuery", None)

            data = {}
            query_set = Transaction.objects.filter(agency__userdetail__managed_by=request.user)
            user_roles = UserRole.objects.filter(user_role='agency', user_detail__managed_by=request.user)

            amount = 0.0

            if overview_time_query:
                date_ = date_periods(query=overview_time_query)
                query_set = query_set.filter(created_on__date__range=[date_, timezone.now().date()])
                user_roles = user_roles.filter(created_on__date__range=[date_, timezone.now().date()])

            for transaction in query_set:
                amount += float(transaction.amount)

            # ---- Total Revenue -----
            data['totalRevenue'] = amount
            # ---- End: Total Revenue ----

            # ---------- Total Transaction -----------
            data['totalTransaction'] = query_set.count()
            # ---------- END: Total Transaction -------

            # --------- Total number of Agencies Assigned to this Partner Manager --------------
            data['agenciesAssigned'] = user_roles.count()
            # --------------------------- ENDS ---------------------------------

            # ------------------ Total Transaction verified and not-verified ------------------
            data['agenciesTransactions'] = partner_manager_dashboard_transaction(request, transaction_time_query)

            # --------------- Revenue -----------------------
            data['revenue'] = partner_manager_dashboard_revenue(request, revenue_time_query)

            # -------------------- Most Used Channels ------------------------
            data['channelUsage'] = partner_manager_dashboard_channel_usage(request, channel_usage_time_query)

            # ------------------------- Services (Supposed to be Documents) ---------------------------
            data['serviceUsed'] = partner_manager_dashboard_service_used(request, service_used_time_query)

            # ------- Verification History --------
            data['verificationTransactions'] = partner_manager_dashboard_verification_history(request, verification_transactions_time_query)

            return Response(api_response(message=f"Partner Manager Dashboard Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
# ------------ END ---------------


# (done).
class PMAgencyView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsPartnerManager]

    def get(self, request, pk=None):
        try:
            data = {}
            if pk:
                user_role = UserRole.objects.get(user_detail__user__id=pk)
                # Check the user_type and use the appropriate Serializer to serialize the datas to be rendered.

                if user_role.user_detail.user_type == "agency":
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
                    serialized_services = SuperAdminAgencyServiceSerializer(services, many=True).data
                    # ----------- End --------------

                    # ---------- Get list of last 15 Transactions ---------
                    latest_transactions = Transaction.objects.filter(agency=agency).order_by('-id')[:15]
                    # ---------- END ---------------

                    overview_data['details'] = PMAgencyDetailSerializer(user_role, many=False).data
                    overview_data['overAll'] = overall_amount
                    overview_data['successfulVerification'] = transactions.filter(status='success').count()
                    overview_data['failedVerification'] = transactions.filter(status='failed').count()
                    overview_data['services'] = serialized_services
                    overview_data['recentHistory'] = SuperAdminTransactionSerializer(instance=latest_transactions,
                                                                                     many=True).data
                    return Response(api_response(message="Agency Detail", data=overview_data, status=True))

            query = request.GET.get('query', None)
            start_date = request.GET.get('startDate', None)
            end_date = request.GET.get('endDate', None)
            sort = request.GET.get('sort', None)

            data = {}
            query_set = UserRole.objects.filter(user_detail__managed_by=request.user, user_detail__user_type='agency',
                                                user_role='agency').order_by("id")

            if query:
                query_set = query_set.filter(
                    Q(user_detail__name__icontains=query) |
                    Q(user_detail__email__icontains=query) |
                    Q(user_detail__approved__iexact=query)
                )

            if start_date and end_date:
                query_set = query_set.filter(user_detail__user__date_joined__date__range=[end_date, start_date])

            if sort:
                sort: str = sort.lower()
                if sort in ['a-z', 'z-a']:
                    query_set = query_set.order_by(
                        "user_detail__user__date_joined") if sort == 'a-z' else query_set.order_by(
                        "-user_detail__user__date_joined")

            data.update({"agenciesCount": query_set.count()})
            serialized_pagination = PMAgencySerializer(self.paginate_queryset(
                query_set, request), many=True).data

            paginated_response = self.get_paginated_response(serialized_pagination).data
            data.update({"responses": paginated_response})

            return Response(api_response(message="Agency Dashboard Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)


# (done)
class PMChannelView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsPartnerManager]

    def get(self, request):
        try:
            query = request.GET.get('query', None)
            start_date = request.GET.get('startDate', None)
            end_date = request.GET.get('endDate', None)
            sort = request.GET.get('sort', None)

            data = {}
            data1 = []
            query_set = Transaction.objects.filter(agency__userdetail__managed_by=request.user).order_by("?")

            channels = Channel.objects.filter()
            for channel in channels:
                transaction_count = query_set.filter(channel=channel).count()
                data1.append({"channelName": channel.name, "totalCount": transaction_count,
                              "channelLogo": SharedPMandSPAChannelImageSerializer(channel, many=False,
                                                                                  context={"request": request}).data,
                              "channelId": channel.id})
            data.update({"channels": data1})

            if query:
                # status is either 'success' or 'failed'.
                # - Can properly search by 'status', 'channel' ...

                query_set = query_set.filter(Q(status__iexact=query) | Q(channel__name__icontains=query))

            if start_date and end_date:
                query_set &= query_set.filter(created_on__date__range=[end_date, start_date])

            if sort:
                sort: str = sort.lower()
                if sort in ['a-z', 'z-a']:
                    if sort == "a-z":
                        query_set &= query_set.order_by("created_on")
                    elif sort == "z-a":
                        query_set &= query_set.order_by("-created_on")

            serialized_data = PMTransactionSerializer(
                query_set, many=True).data
            data.update({"recentTransactions": serialized_data})

            return Response(api_response(message="Channel Dashboard Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)


# - Remains: filter_by: date range and sort.
class PMReportView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsPartnerManager]

    def get(self, request):
        try:
            query = request.GET.get('query', None)
            revenue_time_query = request.GET.get('revenueTimeQuery', None)
            verification_time_query = request.GET.get('verificationTimeQuery', None)
            verified_document_time_query = request.GET.get('verifiedDocumentTimeQuery', None)
            user_and_channel_time_query = request.GET.get('userAndChannelTimeQuery', None)
            data = dict()

            # ------------------- Revenue ----------------------------
            data['revenue'] = partner_manager_report_and_filter(request, revenue_time_query)

            # ------------------ Total Transaction verified and not verified ------------------
            data['verification'] = partner_manager_report_verification_section(request, verification_time_query)

            # ------------------- Verified Documents - User (A) --------------------
            data['verifiedDocument'] = partner_manager_report_user_verified_section(request, verified_document_time_query)

            # ------------- Verified Document - Channel (B) --------------------
            data['verifiedDocumentChannelCount'] = partner_manager_report_channel_verified_section(request, verified_document_time_query)

            # ----------- User Category Section (A) -------------------------
            data.update({"userCategories": partner_manager_report_user_category(request, user_and_channel_time_query)})

            # ------------ User Channels (B) -----------------
            data.update({"userChannelCounts": partner_manager_report_user_channel(request, user_and_channel_time_query)})

            return Response(api_response(message="Reports Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)


# (Done).
class PMTransactionView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsPartnerManager]

    def get(self, request):
        try:
            query = request.GET.get('query', None)
            sort = request.GET.get('sort', None)
            start_date = request.GET.get('startDate', None)
            end_date = request.GET.get('endDate', None)
            download = request.GET.get('download', None)
            data = {}

            query_set = Transaction.objects.filter(agency__userdetail__managed_by=request.user).order_by("-id")

            download = str(download).lower()
            if download == "true":
                download = True
            elif download == "false":
                download = False
            else:
                download = False

            if query:
                # status is either 'success' or 'failed'.
                # - Can properly search by 'status', 'channel' ...

                query_set = query_set.filter(Q(status__iexact=query) | Q(channel__name__icontains=query))

            if start_date and end_date:
                query_set = query_set.filter(created_on__date__range=[end_date, start_date])

            if sort:
                sort: str = sort.lower()
                if sort in ['a-z', 'z-a']:
                    query_set = query_set.order_by("created_on") if sort == 'a-z' else query_set.order_by("-created_on")

            serialized_data = PMTransactionSerializer(query_set, many=True).data
            if download is False:
                serialized_pagination = PMTransactionSerializer(self.paginate_queryset(
                    query_set, request), many=True).data

                serialized_data = self.get_paginated_response(serialized_pagination).data

            data.update({"responses": serialized_data})

            return Response(api_response(message="Agency Dashboard Data", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)
