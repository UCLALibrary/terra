from datetime import date
import fiscalyear as FY


FY.START_MONTH = 7


def current_fiscal_year(today=None):
    today = date.today() if today is None else today
    return FY.FiscalDate(today.year, today.month, today.day).fiscal_year


def in_fiscal_year(date, fiscal_year=None):
    if fiscal_year is None:
        fiscal_year = current_fiscal_year()
    fiscal_date = FY.FiscalDate(date.year, date.month, date.day)
    return fiscal_date.fiscal_year == fiscal_year


def allocations_and_expenditures(treqs):
    expenditures = [t for t in treqs if t.closed]
    expenditures_total = sum([t.actual_expenses() for t in expenditures])
    expenditures_mean = (
        expenditures_total / len(expenditures) if len(expenditures) else 0
    )
    allocations = [t for t in treqs if not t.closed]
    allocations_total = sum([t.estimated_expenses() for t in allocations])
    allocations_total += expenditures_total
    allocations_mean = allocations_total / len(treqs) if len(treqs) else 0
    return {
        "allocations_treqs": allocations,
        "allocations_total": allocations_total,
        "allocations_mean": allocations_mean,
        "expenditures_treqs": expenditures,
        "expenditures_total": expenditures_total,
        "expenditures_mean": expenditures_mean,
    }
