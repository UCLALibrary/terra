from django import forms
from django.forms import ModelForm, Form
from terra.models import ActualExpense, TravelRequest

from django.forms.widgets import Textarea, Input, SelectDateWidget, RadioSelect


class TravelRequestForm(forms.ModelForm):
    class Meta:
        model = TravelRequest
        fields = "__all__"
        # approved_by_id = employee.pk

        # widgets={"departure_date": SelectDateWidget(), 'return_date': SelectDateWidget(), 'funds':RadioSelect() }


class BaseActualExpenseFormSet(forms.BaseModelFormSet):
    class Meta:
        model = TravelRequest

    def __init__(self, *args, **kwargs):
        # self.queryset = TravelRequest.objects.all()
        super().__init__(*args, **kwargs)
        self.can_delete = True
