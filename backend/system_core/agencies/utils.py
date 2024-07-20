from django.db.models import Q
from django.utils import timezone

from account.models import UserRole, Transaction, Channel
from util.utils import date_periods


def agency_revenue_section(revenue_time_query: str) -> list:
    """
        This function handles time filters and also fetches all revenue data if the 'revenue_time_query' is empty / False.
    """
    revenue_list = list()
    if revenue_time_query:
        date_query = date_periods(query=revenue_time_query)
        all_users = UserRole.objects.exclude(Q(user_role="super-admin", user_detail__user_type="platform") |
                                             Q(user_role="partner-manager", user_detail__user_type="platform") |
                                             Q(user_role="agency", user_detail__user_type="agency"))

        for role in all_users:
            each_user_role_transactions = Transaction.objects.filter(owner__userdetail__userrole=role, status="success", created_on__date__range=[date_query, timezone.now().date()])
            amount = 0.0
            for transaction in each_user_role_transactions:
                amount += float(transaction.amount)
            revenue_list.append({"name": role.user_detail.name, "amount": amount})

    else:
        all_users = UserRole.objects.exclude(Q(user_role="super-admin", user_detail__user_type="platform") |
                                             Q(user_role="partner-manager", user_detail__user_type="platform") |
                                             Q(user_role="agency", user_detail__user_type="agency"))

        for role in all_users:
            each_user_role_transactions = Transaction.objects.filter(owner__userdetail__userrole=role, status="success")
            amount = 0.0
            for transaction in each_user_role_transactions:
                amount += float(transaction.amount)
            revenue_list.append({"name": role.user_detail.name, "amount": amount})

    return revenue_list


def channel_data_on_agency_report_section(request, time_query_string):
    """
        Shows break down of each channel where this agency was used overtime.
    """
    channel_usage_count = list()

    channels = Channel.objects.filter()
    if time_query_string:
        date_query = date_periods(time_query_string)

        for channel in channels:
            channel_query_set = Transaction.objects.filter(agency=request.user, channel=channel, created_on__date__range=[date_query, timezone.now().date()])
            channel_usage_count.append({"name": channel.name, "count": channel_query_set.count()})

    else:
        for channel in channels:
            channel_query_set = Transaction.objects.filter(agency=request.user, channel=channel)
            channel_usage_count.append({"name": channel.name, "count": channel_query_set.count()})

    return channel_usage_count


def user_data_on_agency_report_section(request, time_query_string):
    """
        This gives the Categories of users' usage of this agency on the Platform
    """

    user_usage_count = list()
    # Add more roles if more 'user_roles' has been added to the database.
    roles = ['partner-manager', 'individual', 'developer', 'sub-agency', 'corporate-business',
             'individual']  # 'sub-corporate-business'

    if time_query_string:
        date_query = date_periods(query=time_query_string)
        for each_role in roles:
            trans_query_set = Transaction.objects.filter(agency=request.user,
                                                         owner__userdetail__userrole__user_role__icontains=each_role,
                                                         created_on__date__range=[date_query, timezone.now().date()]
                                                         )
            user_usage_count.append({"name": each_role.capitalize(), "count": trans_query_set.count()})

    else:
        for each_role in roles:
            trans_query_set = Transaction.objects.filter(agency=request.user,
                                                         owner__userdetail__userrole__user_role__icontains=each_role
                                                         )
            user_usage_count.append({"name": each_role.capitalize(), "count": trans_query_set.count()})
    return user_usage_count


def verification_data_on_agency_report_section(request, verified_query_string):
    # -------------- Verified Section -----------------
    """
        Fetch all Transactions made by all users except platforms and Agencies
    """
    verified_document = list()

    # 1. Exclude all user roles and  user types of platform and agencies.
    all_users = UserRole.objects.exclude(Q(user_role="super-admin", user_detail__user_type="platform") |
                                         Q(user_role="partner-manager", user_detail__user_type="platform") |
                                         Q(user_role="agency", user_detail__user_type="agency"))

    if verified_query_string:
        date_query = date_periods(verified_query_string)
        for role in all_users:
            success_count = Transaction.objects.filter(
                Q(agency=request.user, owner__userdetail__userrole=role, status="success", created_on__date__range=[date_query, timezone.now().date()])).count()

            failed_count = Transaction.objects.filter(
                Q(agency=request.user, owner__userdetail__userrole=role, status="failed", created_on__date__range=[date_query, timezone.now().date()])).count()
            verified_document.append({"name": role.user_detail.name, "success": success_count, "failed": failed_count})

    else:
        for role in all_users:
            success_count = Transaction.objects.filter(
                Q(agency=request.user) & Q(owner__userdetail__userrole=role) & Q(status="success")).count()
            failed_count = Transaction.objects.filter(
                Q(agency=request.user) & Q(owner__userdetail__userrole=role) & Q(status="failed")).count()
            verified_document.append({"name": role.user_detail.name, "success": success_count, "failed": failed_count})
    return verified_document
    # -------------- End: Verified Section -----------------


def transaction_data_on_agency_report_section(request):
    # -------------- Transactions Count -------------------
    query2 = Transaction.objects.filter(agency=request.user)
    success_count = query2.filter(status='success').count()
    failed_count = query2.filter(status='failed').count()

    # -------------- This week ---------------
    this_week = date_periods(query="this_week")
    this_week_success_count = query2.filter(status='success',
                                            created_on__date__range=[this_week, timezone.now().date()]).count()
    this_week_failed_count = query2.filter(status='failed',
                                           created_on__date__range=[this_week, timezone.now().date()]).count()

    # -------------- Last week ---------------
    last_week = date_periods(query="last_week")
    last_week_success_count = query2.filter(status='success',
                                            created_on__date__range=[last_week, timezone.now().date()]).count()
    last_week_failed_count = query2.filter(status='failed',
                                           created_on__date__range=[last_week, timezone.now().date()]).count()

    # ------------- This month ---------------
    this_month = date_periods(query="this_month")
    this_month_success_count = query2.filter(status='success',
                                             created_on__date__range=[this_month, timezone.now().date()]).count()
    this_month_failed_count = query2.filter(status='failed',
                                            created_on__date__range=[this_month, timezone.now().date()]).count()

    # -------------- Last month -----------------
    last_month = date_periods(query="last_month")
    last_month_success_count = query2.filter(status='success',
                                             created_on__date__range=[last_month, timezone.now().date()]).count()
    last_month_failed_count = query2.filter(status='failed',
                                            created_on__date__range=[last_month, timezone.now().date()]).count()

    return [
        {"successTransactionCount": success_count, "failedTransactionCount": failed_count, "filter": "Total Count"},
        {"thisWeekSuccessCount": this_week_success_count, "thisWeekFailedCount": this_week_failed_count, "filter": "This Week"},
        {"lastWeekSuccessCount": last_week_success_count, "lastWeekFailedCount": last_week_failed_count, "filter": "Last Week"},
        {"thisMonthSuccessCount": this_month_success_count, "thisMonthFailedCount": this_month_failed_count, "filter": "This Month"},
        {"lastMonthSuccessCount": last_month_success_count, "lastMonthFailedCount": last_month_failed_count, "filter": "Last Month"}
    ]


