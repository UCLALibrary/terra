from .utils import current_fiscal_year_int


def add_variable_to_context(request):
    return {"fy_year": current_fiscal_year_int()}
