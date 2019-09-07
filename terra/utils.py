from datetime import date
import fiscalyear as FY
import locale


FY.START_MONTH = 7


def format_currency(value, grouping=True):
    return locale.currency(value, grouping=grouping)


def current_fiscal_year(today=None):
    today = date.today() if today is None else today
    return FY.FiscalDate(today.year, today.month, today.day).fiscal_year


def fiscal_year_bookends(fiscal_year=None):
    if fiscal_year is None:
        fiscal_year = current_fiscal_year()
    fy = FY.FiscalYear(fiscal_year)
    return (fy.start.date(), fy.end.date())


def in_fiscal_year(date, fiscal_year=None):
    if fiscal_year is None:
        fiscal_year = current_fiscal_year()
    fiscal_date = FY.FiscalDate(date.year, date.month, date.day)
    return fiscal_date.fiscal_year == fiscal_year
