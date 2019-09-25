from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import render, render_to_response
from django.views.generic import CreateView
from django.views import View
from django.http import JsonResponse
import json
import pprint
from django.views.generic.list import BaseListView
from django.contrib.admin.views.autocomplete import AutocompleteJsonView as Base

from .models import TravelRequest


class UserDashboard(LoginRequiredMixin, ListView):

    model = TravelRequest
    context_object_name = "treqs"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(traveler__user=self.request.user)

class AutocompleteJsonView(Base):
    """Overriding django admin's AutocompleteJsonView"""

    def get(self, request, *args, **kwargs):
        self.term = request.GET.get('term', '')
        self.paginator_class = self.model_admin.paginator
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {'id': str(obj.pk), 'text': str(obj)}
                for obj in context['object_list']
            ],
            'pagination': {'more': context['page_obj'].has_next()},
        })
        
class UnitManagerView(AutocompleteJsonView):
    def get_queryset(self):
        queryset = Employee.objects.all().order_by('name')
        return queryset