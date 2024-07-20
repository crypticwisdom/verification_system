import base64, logging, re, secrets
from django.conf import settings
from django.db.models import Q
from cryptography.fernet import Fernet
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from account.models import UserDetail


def incoming_request_checks(request, require_data_field: bool = True) -> tuple:
    try:
        x_api_key = request.headers.get('X-Api-Key', None) or request.META.get("HTTP_X_API_KEY", None)
        request_type = request.data.get('requestType', None)
        data = request.data.get('data', {})

        if not x_api_key:
            return False, "Missing or Incorrect Request-Header field 'X-Api-Key'"

        if x_api_key != settings.X_API_KEY:
            return False, "Invalid value for Request-Header field 'X-Api-Key'"

        if not request_type:
            return False, "'requestType' field is required"

        if request_type != "inbound":
            return False, "Invalid 'requestType' value"

        if require_data_field:
            if not data:
                return False, "'data' field was not passed or is empty. It is required to contain all request data"

        return True, data
    except (Exception,) as err:
        return False, f"{err}"


def get_incoming_request_checks(request) -> tuple:
    try:
        x_api_key = request.headers.get('X-Api-Key', None) or request.META.get("HTTP_X_API_KEY", None)

        if not x_api_key:
            return False, "Missing or Incorrect Request-Header field 'X-Api-Key'"

        if x_api_key != settings.X_API_KEY:
            return False, "Invalid value for Request-Header field 'X-Api-Key'"

        return True, ""
        # how do I handle requestType and also client ID e.g 'inbound', do I need to expect it as a query parameter.
    except (Exception,) as err:
        return False, f"{err}"


def validate_email(email):
    try:
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.fullmatch(regex, email):
            return True
        return False
    except (TypeError, Exception) as err:
        # Log error
        return False


def api_response(message, status, data: dict = {}, **kwargs) -> dict:
    try:
        reference_id = secrets.token_hex(30)
        response = dict(requestTime=timezone.now(), requestType='outbound', referenceId=reference_id,
                        status=status, message=message, data=data, **kwargs)

        # if "accessToken" in data and 'refreshToken' in data:
        if "accessToken" in data:
            # Encrypting tokens to be
            response['data']['accessToken'] = encrypt_text(text=data['accessToken'])
            # response['data']['refreshToken'] = encrypt_text(text=data['refreshToken'])
            logging.info(msg=response)

            response['data']['accessToken'] = decrypt_text(text=data['accessToken'])
            # response['data']['refreshToken'] = encrypt_text(text=data['refreshToken'])

        else:
            logging.info(msg=response)

        return response
    except (Exception,) as err:
        return err


def encrypt_text(text):
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    fernet = Fernet(key)
    secure = fernet.encrypt(f"{text}".encode())
    return secure.decode()


def decrypt_text(text):
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    fernet = Fernet(key)
    decrypt = fernet.decrypt(text.encode())
    return decrypt.decode()


def phone_number_check(phone_number: str) -> (bool, str):
    try:
        if len(phone_number) != 11 or not phone_number.isnumeric():
            return False, "phone number must be of length 11 and must contain only digits"

        phone_number = "+234" + phone_number[-10:]

        phone_number_exists = UserDetail.objects.filter(phone_number=phone_number).exists()
        if phone_number_exists:
            return False, "phone number already exists"

        return True, phone_number
    except (Exception,) as err:
        return False, str(err)


def delete_created_instances(*args):
    for instance in args:
        if instance is not None:
            instance.delete()


def get_month(month: int = 0):
    """
        returns the datetime after subtracting the months from the current datetime.
        passing 0 to 'relativedelta(months=0) mean getting the current month.
    """
    return timezone.now() - relativedelta(months=month)


def transaction_queryset_date_range_filter(start_date, end_date, query_set):
    # ------- Date range filter -------
    """
        Can only receive a query set with model that has the 'created_on' field
    """
    if start_date and end_date:
        query_set = query_set.filter(Q(created_on__date__range=[start_date, end_date]))
    return query_set


def transaction_queryset_status_filter(status_query, query_set):
    # ------- status filter--------
    if status_query:
        status_query: str = status_query
        if status_query.lower() == 'success':
            query_set = query_set.filter(status="success")
        elif status_query.lower() == 'failed':
            query_set = query_set.filter(status="failed")
    return query_set


def date_periods(query: str):
    query = query.lower()
    date_ = None
    if query in ['today', 'this_week', 'last_week', 'this_month', 'last_month', 'last_6_month']:
        if query == "today":
            date_ = timezone.now().date() - relativedelta(days=0)
        elif query == "this_week":
            date_ = timezone.now().date() - relativedelta(weeks=1)
        elif query == "last_week":
            date_ = timezone.now().date() - relativedelta(weeks=2)
        elif query == "this_month":
            date_ = timezone.now().date() - relativedelta(months=0)
        elif query == "last_month":
            date_ = timezone.now().date() - relativedelta(months=1)
        elif query == "last_6_month":
            date_ = timezone.now().date() - relativedelta(months=6)
    else:
        date_ = timezone.now().date() - relativedelta(days=0)
    return date_





