from django.shortcuts import render
from .models import Employee
from django.views.generic import DetailView
from django.contrib.auth import views as auth_views

class EmployeeDetailView(DetailView):
	model = Employee




# Create your views here.
