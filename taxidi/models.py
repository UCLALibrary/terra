from django.db import models
from django.contrib.auth.models import User


class Team(models.Model):
	name = models.CharField(max_length=128)
	email = models.EmailField()
	phone = models.CharField(max_length=12, null=True, blank=True)
	manager = models.ForeignKey('Employee', on_delete=models.PROTECT)
	parent_team = models.ForeignKey('self', on_delete=models.CASCADE)


class Employee(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	team = models.ForeignKey('Team', on_delete=models.PROTECT)
	boss = models.ForeignKey('self', on_delete=models.PROTECT)


class Vacation(models.Model):
	start = models.DateField()
	end = models.DateField()


class Activity(models.Model):
	name = models.CharField()
	url = models.URLField()
	start = models.DateField()
	end = models.DateField()
	city = models.CharField(max_length=32)
	state = models.CharField(max_length=32)
	country = models.CharField(max_length=32, default='USA')


class TravelRequest(models.Model):
	requestor = models.ForeignKey('Employee', on_delete=models.PROTECT)
	activity = models.ForeignKey('Activity', on_delete=models.PROTECT)
	departure_date = models.DateField()
	return_date = models.DateField()


