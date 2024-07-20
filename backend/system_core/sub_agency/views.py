# You can get the original Agency from a Transaction through the service detail field.
from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from util.paginations import CustomPagination
from account import permission
from account.models import Service, Transaction, Channel, ServiceDetail
from util.utils import get_incoming_request_checks, api_response, date_periods
from rest_framework import status
from .serializers import SubAgencyTransactionSerializer, SubAgencyChannelImageSerializer, \
    SubAgencyListServiceDetailSerializer, SubAgencyRecentVerificationSerializer, SubAgencyServiceHistorySerializer

from .utils import verification_data_on_sub_agency_report_section, sub_agency_revenue_section, \
    channel_data_on_sub_agency_report_section, user_data_on_sub_agency_report_section, \
    transaction_data_on_sub_agency_report_section, channel_usage_dashboard, dashboard_revenue, verified_document, \
    verified_document_channel_count


# Done
class SubAgencyDashboardView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request):
        """Returns data for the Sub-Agency Analyzed data for dashboard."""
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            data = dict()
            over_view_time_query = request.GET.get("overViewTimeQuery", None)
            channel_usage_time_query = request.GET.get("channelUsageTimeQuery", None)
            revenue_time_query = request.GET.get("revenueTimeQuery", None)
            verification_time_query = request.GET.get("verificationTransactionTimeQuery", None)
            transaction_query_set = Transaction.objects.filter(status="success", agency__userdetail__user=request.user)

            amount = 0.0

            # ------- Overview ------------
            if over_view_time_query:
                date_query = date_periods(query=over_view_time_query)

                transaction_query_set = transaction_query_set.filter(
                    Q(created_on__date__range=[date_query, timezone.now().date()]))
                for transaction in transaction_query_set:
                    amount += float(transaction.amount)

                data['totalRevenue'] = amount

                # 1a. Total Users
                data['totalUsers'] = transaction_query_set.count()

                # 1b. Successful Transaction
                data['successfulTransaction'] = transaction_query_set.filter(status="success").count()

                # 1c. Failed Transaction
                data['failedTransaction'] = transaction_query_set.filter(status="failed").count()
            else:
                for transaction in transaction_query_set:
                    amount += float(transaction.amount)

                data['totalRevenue'] = amount

                # 1a. Total Users
                data['totalUsers'] = transaction_query_set.filter().count()

                # 1b. Successful Transaction
                data['successfulTransaction'] = transaction_query_set.filter(status="success").count()

                # 1c. Failed Transaction
                data['failedTransaction'] = transaction_query_set.filter(status="failed").count()
            # ------- End: Overview -------

            # ---------- Recent Services -----------
            container3 = []
            # 1. Fetch all 5 recent services used by this user.
            recent_transaction = Transaction.objects.filter(service_detail__agency=request.user).order_by('-id')

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
                _ = SubAgencyRecentVerificationSerializer(service_detail, many=False, context={"request": request}).data
                data_.append(_)

            data.update({"recentVerifications": data_})
            # ---- End ---------

            # -------- Transaction Counts --------
            data['transactionCounts'] = transaction_data_on_sub_agency_report_section(request)

            # 2a. ------ Revenue -----
            data['revenue'] = dashboard_revenue(request, revenue_time_query=revenue_time_query)
            # ------------

            # 2b. Channel Usage
            data['channelUsage'] = channel_usage_dashboard(request, channel_usage_time_query)

            # 3 -------Recent 10 Verification History --------
            if verification_time_query:
                date_query = date_periods(query=verification_time_query)

                recent_transactions = Transaction.objects.filter(
                    Q(agency=request.user, created_on__date__range=[date_query, timezone.now().date()]))[:10]
            else:
                recent_transactions = Transaction.objects.filter(agency=request.user)[:10]
            data['verificationTransactions'] = SubAgencyTransactionSerializer(recent_transactions, many=True).data

            return Response(api_response(message=f"Data for Sub Agency Dashboard", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# Done
class SubAgencyChannelView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request):

        """Returns data for the Sub-Agency Analyzed data for Channels."""
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            container = dict()
            data = []

            query_set = Transaction.objects.filter(agency=request.user).order_by("id")
            channels = Channel.objects.filter()
            for channel in channels:
                transaction_count = query_set.filter(channel=channel).count()
                data.append({"channelName": channel.name, "totalCount": transaction_count,
                             "channelLogo": SubAgencyChannelImageSerializer(channel, many=False,
                                                                            context={"request": request}).data,
                             "channelId": channel.id})
            container.update({"channels": data})
            # ---------------

            # ---------- Get list of Transactions ---------

            query = request.GET.get("query", None)
            order = request.GET.get("order", None)
            start_date = request.GET.get("startDate", None)
            end_date = request.GET.get("endDate", None)
            channel_query = request.GET.get("channels", None)

            # search by owner-name, amount, document, document_id, transaction-id
            if query:
                query: str = query.lower()
                query_set = query_set.filter(
                    Q(owner__userdetail__name__icontains=query) | Q(amount__icontains=query) |
                    Q(document_id__icontains=query) | Q(id__exact=query)
                )

            # a-z or z-a
            if order:
                order: str = order.lower()
                if order in ['a-z', 'z-a']:
                    query_set = query_set.order_by('created_on') if order == 'a-z' else query_set.order_by(
                        '-created_on')

            # start-date: 2023-01-21, end-date; 2023-09-23
            if start_date and end_date:
                query_set = query_set.filter(
                    Q(created_on__date__range=[start_date, end_date]))

            # Channels
            if channel_query:
                channel_query: str = channel_query
                channel_ids = channel_query.split(",")

                for channel_id in channel_ids:
                    if channel_id and channel_id.isnumeric():
                        query_set &= query_set.filter(channel__id=channel_id)

            serialized_pagination = SubAgencyTransactionSerializer(
                self.paginate_queryset(query_set, request), many=True,
                context={'request': request}).data
            paginated_response = self.get_paginated_response(serialized_pagination).data
            container['recentHistory'] = paginated_response

            return Response(api_response(message=f"Data for Sub Agency Dashboard", data=container, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request):
    #     service = None
    #     try:
    #         success, data = incoming_request_checks(request=request, require_data_field=False)
    #         if not success:
    #             return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)
    #
    #         service_name = request.data.get('serviceName', None)
    #         service_logo = request.data.get('logo', None)
    #         description = request.data.get('description', None)
    #         providers = request.data.get('providers', [])
    #
    #         if not service_name:
    #             return Response(api_response(message="'serviceName' field is required", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #         service_name: str = service_name
    #
    #         if not service_logo:
    #             return Response(api_response(message="'logo' field is required", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         if not description:
    #             return Response(api_response(message="'description' field is required", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         if not providers:
    #             return Response(api_response(message="'providers' field is required", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         providers = ast.literal_eval(providers)
    #
    #         service_name: str = service_name.capitalize()
    #         service, created = Service.objects.get_or_create(name=service_name)
    #         if not created:
    #             return Response(api_response(message=f"'{service_name} 'Service already exists", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         service.description = description
    #         service.activate = True
    #         service.logo = service_logo
    #         # service.service_code = service_code
    #         service.save()
    #
    #         # Add Providers
    #         if providers is not None:
    #             for provider_id in providers:
    #                 # create service detail here for each provider
    #                 agency = User.objects.get(id=provider_id)
    #                 # 'service_detail_code' will be added by the superAdmin, which will be used to write a block of code
    #                 # for them.
    #
    #                 service_detail = ServiceDetail.objects.create(service=service, agency=agency)
    #
    #                 # Create a custom Service Name for the Service Detail that belongs to an Agency by appending the
    #                 # service name with the Agency's name
    #                 service_detail.name = f"{service_name} by {agency.userdetail.name}"
    #                 service_detail.save()
    #
    #                 #   Send Email Here (Notify agencies of the newly added service to their profile).
    #                 service_addition_mail(context={"service_detail": service_detail, "agency": agency})
    #
    #         return Response(api_response(message=f"Successfully added '{service.name}' with provider(s)", data={},
    #                                      status=True))
    #     except (Exception,) as err:
    #         delete_created_instances(service)
    #         return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
    #
    # def put(self, request):
    #     try:
    #         success, data = incoming_request_checks(request=request)
    #         if not success:
    #             return Response(api_response(message=data, status=False), status=status.HTTP_400_BAD_REQUEST)
    #
    #         service_id = data.get('serviceId', None)
    #         service_status = data.get('serviceStatus', False)
    #         service_name = data.get('serviceName', None)
    #         description = data.get('description', None)
    #
    #         if not service_id:
    #             return Response(api_response(message="'serviceID' field is required", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         service = Service.objects.get(id=service_id)
    #
    #         if service_status not in [True, False]:
    #             return Response(api_response(message="'serviceStatus' expects either true or false", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         service.name = str(service_name).capitalize() if service_name else service.name
    #         service.description = description if description else service.description
    #         service.activate = service_status
    #         service.save()
    #
    #         serialized_data = SuperAdminServiceSerializer(service, context={'request': request}).data
    #
    #         return Response(
    #             api_response(message=f"Successfully updated '{service_name}' Service", data=serialized_data,
    #                          status=True))
    #     except (Exception,) as err:
    #         return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
    #
    # def delete(self, request, pk=None):
    #     try:
    #         if pk is None:
    #             return Response(api_response(message="'service id' is not present in the URL", status=False),
    #                             status=status.HTTP_400_BAD_REQUEST)
    #         service = Service.objects.get(id=pk)
    #         service.delete()
    #         # Notification can come in here
    #         return Response(api_response(message=f"Service has been Deleted", status=True))
    #     except (Exception,) as err:
    #         return Response(api_response(message=f"Error: '{err}'", status=False), status=status.HTTP_400_BAD_REQUEST)


# Done
class SubAgencyTransactionView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request):
        """Returns Transaction data for the Sub-Agency.
        :param request:
        :param pk:
        :return:
        """
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            # Fetch all transaction where the owner is the Sub-Agency is the owner, since he made the Transaction
            # from his dashboard.
            transaction_query_set = Transaction.objects.filter(
                agency__userdetail__userrole__user_role="sub-agency", owner=request.user).order_by("id")

            query = request.GET.get("query", None)
            status_query = request.GET.get("statusQuery", None)
            channel_query = request.GET.get("channelQuery", None)
            start_date_query = request.GET.get("startDate", None)
            end_date_query = request.GET.get("endDate", None)
            download = request.GET.get('download', None)

            download = str(download).lower()
            if download == "true":
                download = True
            elif download == "false":
                download = False
            else:
                download = False

            if query:
                transaction_query_set = transaction_query_set.filter(
                    Q(email__icontains=query) | Q(amount__icontains=query))

            if status_query:
                transaction_query_set = transaction_query_set.filter(Q(status__icontains=status_query))

            if channel_query:
                channel_query: str = channel_query
                channel_ids = channel_query.split(",")

                for channel_id in channel_ids:
                    if channel_id and channel_id.isnumeric():
                        transaction_query_set &= transaction_query_set.filter(channel__id=channel_id)

            if start_date_query and end_date_query:
                transaction_query_set = transaction_query_set.filter(
                    created_on__date__range=[start_date_query, end_date_query])

            serialized_data = SubAgencyTransactionSerializer(transaction_query_set, many=True).data
            if download is False:
                serialized_pagination = SubAgencyTransactionSerializer(
                    self.paginate_queryset(transaction_query_set, request), many=True).data
                serialized_data = self.get_paginated_response(serialized_pagination).data

            return Response(
                api_response(message=f"Data for Sub-Agency Transaction", data=serialized_data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


# Done
class SubAgencyServiceView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request):
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            service_detail = ServiceDetail.objects.filter(is_available=True, agency=request.user,
                                                          service__activate=True).order_by("id")
            serialized_data = SubAgencyListServiceDetailSerializer(service_detail, many=True,
                                                                   context={'request': request})
            return Response(
                api_response(message=f"List of Services for Sub-Agency", data=serialized_data.data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class SubAgencyGetServiceInformation(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request, pk=None):
        try:
            if pk:
                # Fetch all transactions that has been done with this Service.
                queryset = Service.objects.filter(id=pk)
                service = Service.objects.filter(id=pk).last()

                if not queryset.exists():
                    return Response(api_response(message=f"Service with ID '{pk}' does not exists", data={},
                                                 status=False), status=status.HTTP_400_BAD_REQUEST)

                transactions_history = Transaction.objects.filter(
                    owner=request.user, service_detail__service=service).order_by('id')

                paginated_query = self.paginate_queryset(transactions_history, request=request)
                response = self.get_paginated_response(
                    SubAgencyServiceHistorySerializer(paginated_query, many=True, context={"user": request.user}).data)
                return Response(
                    api_response(message=f"Services Information for '{service.name}'", data=response.data, status=True))

            return Response(api_response(message=f"service ID is required", data={}, status=False),
                            status=status.HTTP_400_BAD_REQUEST)
        except (Exception,) as err:
            return Response(api_response(message=f"{err}", data={}, status=False), status=status.HTTP_400_BAD_REQUEST)


class SubAgencySettingsView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request):
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            # Get a single service by id

            data = dict()

            return Response(api_response(message=f"Data for Sub Agency Dashboard", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)


class SubAgencyReportView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated, permission.IsSubAgency]

    def get(self, request):
        try:
            check, msg = get_incoming_request_checks(request)
            if not check:
                return Response(
                    api_response(message=msg, data={}, status=False), status=status.HTTP_400_BAD_REQUEST)

            revenue_time_query = request.GET.get("revenueTimeQuery", None)
            user_and_channel_time_query = request.GET.get("userAndChannelTimeQuery", None)
            verified_document_time_query = request.GET.get("verifiedDocumentTimeQuery", None)
            verification_query = request.GET.get("verificationQuery", None)
            verified_document_channel_time_query = request.GET.get("verifiedDocumentChannelTimeQuery", None)

            data = dict()

            # ------------------- Revenue --------------------
            data['revenue'] = dashboard_revenue(request, revenue_time_query=revenue_time_query)

            # ------------------- Channel Usage Count (A) -----------------------
            data['subAgencyChannelUsageCount'] = channel_data_on_sub_agency_report_section(request=request,
                                                                                           time_query_string=user_and_channel_time_query)

            # ---------- User Categories Usage (B) -----------
            data['userCategoryUsageCount'] = user_data_on_sub_agency_report_section(request=request,
                                                                                    time_query_string=user_and_channel_time_query)

            # ---------- Verified Document (A) ------------
            data['verifiedDocuments'] = verified_document(request,
                                                          verified_document_time_query=verified_document_time_query)

            # ---------- Verified Document (B) ------------
            data['verifiedDocumentChannel'] = verified_document_channel_count(request,
                                                                              verified_document_channel_time_query)
            # ---------- END ------------

            # -------------- Verification Section -----------------
            data['verification'] = verification_data_on_sub_agency_report_section(request=request,
                                                                                  verified_query_string=verification_query)

            return Response(api_response(message=f"Data for Sub Agency Dashboard", data=data, status=True))
        except (Exception,) as err:
            return Response(api_response(message=f"Error: {err}", status=False), status=status.HTTP_400_BAD_REQUEST)
