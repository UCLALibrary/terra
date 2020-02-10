from datetime import date
from django.conf import settings

import fiscalyear as FY
import locale


FY.START_MONTH = 7


def current_fiscal_year(today=None):
    today = date.today() if today is None else today
    return FY.FiscalDate(today.year, today.month, today.day).fiscal_year


def current_fiscal_year_int(today=None):
    year = current_fiscal_year(today=today)
    return year


def add_variable_to_context(request):
    return {"fy_year": current_fiscal_year_int()}
