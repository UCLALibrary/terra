from .utils import current_fiscal_year_int
from django.conf import settings


def add_variable_to_context(request):
    return {
        "fy_year": current_fiscal_year_int(),
        "inception_year": settings.INCEPTION_DATE,
    }
