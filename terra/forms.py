from django import forms
from django.forms import ModelForm, Form
from terra.models import TravelRequest, EstimatedExpense, Employee, Activity

from django.forms.widgets import Textarea, Input, SelectDateWidget, RadioSelect


class TravelRequestForm(forms.ModelForm):
    class Meta:
        model = TravelRequest
        fields = [
            "traveler",
            "activity",
            "departure_date",
            "return_date",
            "days_ooo",
            "closed",
            "administrative",
            "note",
            "justification",
        ]
        # widgets={"departure_date": SelectDateWidget(), 'return_date': SelectDateWidget() }


class EstimatedExpenseForm(forms.ModelForm):
    class Meta:
        model = EstimatedExpense
        fields = ["treq", "type", "rate", "quantity", "total"]


class NewActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            "name",
            "url",
            "description",
            "start",
            "end",
            "city",
            "state",
            "country",
        ]


class BaseTravelRequestFormSet(forms.BaseModelFormSet):
    class Meta:
        model = TravelRequest

    def __init__(self, *args, **kwargs):
        # self.queryset = TravelRequest.objects.all()
        super().__init__(*args, **kwargs)
        self.can_delete = True
