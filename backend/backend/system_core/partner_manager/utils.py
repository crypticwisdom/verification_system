from django.db.models import Q
from django.utils import timezone
from account.models import UserRole, Transaction, Channel, ServiceDetail
from util.utils import date_periods

from super_admin.serializers import VerificationTransactionSerializer


def partner_manager_report_and_filter(request, partner_manager_report_and_filter):
    container = []
    agencies = UserRole.objects.filter(user_role="agency", user_detail__user_type="agency",
                                       user_detail__managed_by=request.user)

    if partner_manager_report_and_filter:
        date_query = date_periods(query=partner_manager_report_and_filter)
        for agency in agencies:
            transactions = Transaction.objects.filter(agency=agency.user_detail.user,
                                                      agency__userdetail__managed_by=request.user,
                                                      status="success", created_on__date__range=[date_query, timezone.now().date()])
            amount: float = 0.0
            for transaction in transactions:
                amount += float(transaction.amount)

            container.append(
                {"agencyID": agency.user_detail.user.id, "name": agency.user_detail.name, "amount": amount})
    else:

        for agency in agencies:
            transactions = Transaction.objects.filter(agency=agency.user_detail.user,
                                                      agency__userdetail__managed_by=request.user,
                                                      status="success")
            amount: float = 0.0
            for transaction in transactions:
                amount += float(transaction.amount)

            container.append({"agencyID": agency.user_detail.user.id, "name": agency.user_detail.name, "amount": amount})
    return container


def partner_manager_report_verification_section(request, verification_time_query):
    container1 = []
    agencies = UserRole.objects.filter(user_role="agency", user_detail__user_type="agency",
                                       user_detail__managed_by=request.user)
    if verification_time_query:
        date_query = date_periods(query=verification_time_query)

        for agency in agencies:
            success_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                    agency__userdetail__managed_by=request.user,
                                                                    status="success", created_on__date__range=[date_query, timezone.now().date()]).count()
            failed_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                   agency__userdetail__managed_by=request.user,
                                                                   status="failed", created_on__date__range=[date_query, timezone.now().date()]).count()
            container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                               "failed": failed_transactions_count})

    else:
        for agency in agencies:
            success_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                    agency__userdetail__managed_by=request.user,
                                                                    status="success").count()
            failed_transactions_count = Transaction.objects.filter(agency=agency.user_detail.user,
                                                                   agency__userdetail__managed_by=request.user,
                                                                   status="failed").count()
            container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                               "failed": failed_transactions_count})

    return container1


def partner_manager_report_user_verified_section(request, verified_document_time_query):
    """
        Fetch all Transaction count where this partner-manager is related to the Agency used (Agency's service).
    """
    container2 = []
    agencies = UserRole.objects.filter(user_detail__user_type="agency", user_role="agency",
                                       user_detail__managed_by=request.user)

    if verified_document_time_query:
        date_query = date_periods(query=verified_document_time_query)
        for agency in agencies:
            transaction = Transaction.objects.filter(agency=agency.user_detail.user, status="success",
                                                     created_on__date__range=[date_query, timezone.now().date()]).count()
            container2.append({"name": agency.user_detail.name, "count": transaction})
    else:
        for agency in agencies:
            transaction = Transaction.objects.filter(agency=agency.user_detail.user, status="success").count()
            container2.append({"name": agency.user_detail.name, "count": transaction})
    return container2


def partner_manager_report_channel_verified_section(request, verified_document_time_query):
    # ------------- Verified Document (B) --------------------
    """
        Fetch all Channel's count where this partner-manager is related to the Agency used (Agency's service).
    """
    channel_document_verified_document = []
    channels = Channel.objects.filter()

    if verified_document_time_query:
        date_query = date_periods(query=verified_document_time_query)

        for channel in channels:
            transaction = Transaction.objects.filter(channel=channel, agency__userdetail__managed_by=request.user,
                                                     agency__userdetail__user_type="agency", created_on__date__range=[date_query, timezone.now().date()])
            channel_document_verified_document.append({"name": channel.name, "count": transaction.count()})

    else:
        for channel in channels:
            transaction = Transaction.objects.filter(channel=channel, agency__userdetail__managed_by=request.user,
                                                     agency__userdetail__user_type="agency")
            channel_document_verified_document.append({"name": channel.name, "count": transaction.count()})

    return channel_document_verified_document
    # --------------------------------------------------


def partner_manager_report_user_category(request, user_and_channel_time_query):
    """
        This section shows the number of Agencies, Sub-Agencies, Business, Individuals related to this partner manager
    """
    if user_and_channel_time_query:
        date_query = date_periods(query=user_and_channel_time_query)

        # ------ User Channels (A) ------
        container3 = []
        # - Get all agencies related to this partner manager.
        query_set = UserRole.objects.filter(user_role="agency", user_detail__user_type='agency',
                                            user_detail__managed_by=request.user, user_detail__user__date_joined__date__range=[date_query, timezone.now().date()])
        container3.append({"numberOfAgencies": query_set.count()})

        # - Get sub-agencies related to each agency that is also managed_by this partner-manager.
        # - Now loop through the 'query_set' to sum the total number of sub-agencies under each Agency.
        sub_agencies_count = 0
        for each_agency in query_set:
            sub_agencies_user_each_agency_count = UserRole.objects.filter(
                user_role="sub-agency", user_detail__parent_agency=each_agency.user_detail.user).count()
            sub_agencies_count += sub_agencies_user_each_agency_count
        container3.append({"numberOfSubAgencies": sub_agencies_count})

        # - Get the number of businesses that has used any agency managed_by this partner-manager.
        business_count, individual_count = 0, 0

        for each in query_set:
            business_transaction_count = Transaction.objects.filter(agency=each.user_detail.user,
                                                                    owner__userdetail__user_type='corporate-business',
                                                                    status="success", created_on__date__range=[date_query, timezone.now().date()])
            business_count += business_transaction_count.count()

            individual_transaction_count = Transaction.objects.filter(agency=each.user_detail.user,
                                                                      owner__userdetail__user_type='individual',
                                                                      status="success", created_on__date__range=[date_query, timezone.now().date()])
            individual_count += individual_transaction_count.count()

    else:
        # ------ User Channels (A) ------
        container3 = []
        # - Get all agencies related to this partner manager.
        query_set = UserRole.objects.filter(user_role="agency", user_detail__user_type='agency',
                                            user_detail__managed_by=request.user)
        container3.append({"numberOfAgencies": query_set.count()})

        # - Get sub-agencies related to each agency that is also managed_by this partner-manager.
        # - Now loop through the 'query_set' to sum the total number of sub-agencies under each Agency.
        sub_agencies_count = 0
        for each_agency in query_set:
            sub_agencies_user_each_agency_count = UserRole.objects.filter(
                user_role="sub-agency", user_detail__parent_agency=each_agency.user_detail.user).count()
            sub_agencies_count += sub_agencies_user_each_agency_count
        container3.append({"numberOfSubAgencies": sub_agencies_count})

        # - Get the number of businesses that has used any agency managed_by this partner-manager.
        business_count, individual_count = 0, 0

        for each in query_set:
            business_transaction_count = Transaction.objects.filter(agency=each.user_detail.user,
                                                                    owner__userdetail__user_type='corporate-business',
                                                                    status="success")
            business_count += business_transaction_count.count()

            individual_transaction_count = Transaction.objects.filter(agency=each.user_detail.user,
                                                                      owner__userdetail__user_type='individual',
                                                                      status="success")
            individual_count += individual_transaction_count.count()

        # developer_transaction_count = Transaction.objects.filter(agency=each.user_detail.user,
        # owner__userdetail__user_type='developer', status="success") developer_count +=
        # developer_transaction_count.count()

    container3.append({"numberOfBusinessUser": business_count})
    container3.append({"numberOfIndividualUser": individual_count})
    # container3.append({"numberOfDeveloperUser": developer_count})

    return container3


def partner_manager_report_user_channel(request, user_and_channel_time_query):
    # ------------ User Channels (B) -----------------
    """
        This section gives a break-down of all users using each channel on the agency managed by this manager.
    """
    channel_records = []
    channels = Channel.objects.all()

    if user_and_channel_time_query:
        date_query = date_periods(query=user_and_channel_time_query)

        for channel in channels:
            count = Transaction.objects.filter(Q(channel=channel, agency__userdetail__managed_by=request.user,
                                                 created_on__date__range=[date_query, timezone.now().date()])).count()
            channel_records.append({"channelName": channel.name, "channelCount": count})

    else:
        for channel in channels:
            count = Transaction.objects.filter(Q(channel=channel, agency__userdetail__managed_by=request.user)).count()
            channel_records.append({"channelName": channel.name, "channelCount": count})

    return channel_records


def partner_manager_dashboard_transaction(request, transaction_time_query):
    # ------------ User Channels (B) -----------------
    """
        This section gives agencies that are being managed_by this partner-manager successful and failed verifications.
    """
    container1 = []
    agencies = UserRole.objects.filter(user_role="agency", user_detail__managed_by=request.user)

    if transaction_time_query:
        date_query = date_periods(query=transaction_time_query)
        container1 = []
        for agency in agencies:
            transactions = Transaction.objects.filter(agency=agency.user_detail.user, status="success", created_on__date__range=[date_query, timezone.now().date()])
            success_transactions_count = transactions.filter(status="success").count()
            failed_transactions_count = transactions.filter(status="failed").count()
            container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                               "failed": failed_transactions_count})

    else:
        for agency in agencies:
            transactions = Transaction.objects.filter(agency=agency.user_detail.user, status="success")
            success_transactions_count = transactions.filter(status="success").count()
            failed_transactions_count = transactions.filter(status="failed").count()
            container1.append({"name": agency.user_detail.name, "success": success_transactions_count,
                               "failed": failed_transactions_count})

    return container1


def partner_manager_dashboard_revenue(request, revenue_time_query):
    """
        This section gives the revenue of agencies that are being managed_by this partner-manager.
    """
    container = []
    agencies = UserRole.objects.filter(user_role="agency", user_detail__managed_by=request.user)

    if revenue_time_query:
        date_query = date_periods(query=revenue_time_query)
        for agency in agencies:
            query = Transaction.objects.filter(agency=agency.user_detail.user, status="success", created_on__date__range=[date_query, timezone.now().date()])
            amount = 0.0
            for T in query:
                amount += float(T.amount)
            container.append({"name": agency.user_detail.name, "amount": amount})
    else:
        for agency in agencies:
            query = Transaction.objects.filter(agency=agency.user_detail.user, status="success")
            amount = 0.0
            for T in query:
                amount += float(T.amount)
            container.append({"name": agency.user_detail.name, "amount": amount})
    return container


def partner_manager_dashboard_channel_usage(request, channel_usage_time_query):
    """
        This section gives the channel usage of agencies that are being managed_by this partner-manager.
    """
    container = []
    channels = Channel.objects.filter()

    if channel_usage_time_query:
        date_query = date_periods(query=channel_usage_time_query)
        for channel in channels:
            counts = Transaction.objects.filter(channel=channel,
                                                agency__userdetail__managed_by=request.user, created_on__date__range=[date_query, timezone.now().date()]).count()
            container.append({"name": channel.name, "count": counts})

    else:
        for channel in channels:
            counts = Transaction.objects.filter(channel=channel, agency__userdetail__managed_by=request.user).count()
            container.append({"name": channel.name, "count": counts})

    return container


def partner_manager_dashboard_service_used(request, service_used_time_query):
    """
        This section gives the service-used by agencies that are being managed_by this partner-manager.
    """
    container = []
    service_details = ServiceDetail.objects.filter(agency__userdetail__managed_by=request.user)

    if service_used_time_query:
        date_query = date_periods(query=service_used_time_query)
        for service_detail in service_details:
            counts = Transaction.objects.filter(service_detail=service_detail, created_on__date__range=[date_query, timezone.now().date()]).count()
            container.append({"name": service_detail.service.name, "count": counts})

    else:
        for service_detail in service_details:
            counts = Transaction.objects.filter(service_detail=service_detail).count()
            container.append({"name": service_detail.service.name, "count": counts})

    return container


def partner_manager_dashboard_verification_history(request, verification_transactions_time_query):
    """
        This section gives the verification history by agencies that are being managed_by this partner-manager.
    """
    if verification_transactions_time_query:
        date_query = date_periods(query=verification_transactions_time_query)
        recent_transactions = Transaction.objects.filter(agency__userdetail__managed_by=request.user, created_on__date__range=[date_query, timezone.now().date()])

    else:
        recent_transactions = Transaction.objects.filter(agency__userdetail__managed_by=request.user)
    serialized_data = VerificationTransactionSerializer(recent_transactions, many=True).data
    return serialized_data

