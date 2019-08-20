from django.db import models
from django.contrib.auth.models import User


APPROVAL_TYPES = (
	('S', 'Supervisor'),
	('F', 'Funding'),
	('I', 'International'),
)

EXPENSE_TYPES = (
	('LDG', 'Lodging'),
	('AIR', 'Airfare'),
	('TRN', 'Transit'),
	('RNT', 'Car Rental'),
	('DRV', 'Driving'),
	('CON', 'Conference Registration'),
	('PRE', 'Preconference Fees'),
	('MEM', 'Membership Fees'),
	('PRK', 'Parking'),
	('EAT', 'Meals'),
	('OTH', 'Other')
)


class Unit(models.Model):
	name = models.CharField(max_length=128)
	manager = models.ForeignKey('Employee', on_delete=models.PROTECT, 
		related_name='managed_units', null=True, blank=True)
	parent_unit = models.ForeignKey('self', on_delete=models.PROTECT,
		null=True, blank=True)

	def __str__(self):
		return self.name

	def __repr__(self):
		return '<Unit {}: {}>'.format(self.id, self.name)


class Employee(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	phone = models.CharField(max_length=32, blank=True)
	unit = models.ForeignKey('Unit', on_delete=models.PROTECT)
	active = models.BooleanField(default=True)
	uid = models.CharField(max_length=9, unique=True)
	supervisor = models.ForeignKey('self', on_delete=models.PROTECT,
		null=True, blank=True)

	def __str__(self):
		return self.user.get_full_name()

	def __repr__(self):
		return '<Employee {}: {}>'.format(self.id, self)


class Fund(models.Model):
	account = models.CharField(max_length=6)
	cost_center = models.CharField(max_length=2)
	fund = models.CharField(max_length=5)
	manager = models.ForeignKey('Employee', on_delete=models.PROTECT)

	def __str__(self):
		return '{}-{}-{}'.format(self.account, self.cost_center, self.fund)

	def __repr__(self):
		return '<Fund {}: {}>'.format(self.id, self)


class TravelRequest(models.Model):
	traveler = models.ForeignKey('Employee', on_delete=models.PROTECT)
	activity = models.ForeignKey('Activity', on_delete=models.PROTECT)
	departure_date = models.DateField()
	return_date = models.DateField()
	days_ooo = models.IntegerField('Days Out of Office')
	closed = models.BooleanField(default=False)
	administrative = models.BooleanField(default=False)
	justification = models.TextField(blank=True)
	funding = models.ManyToManyField(Fund)

	def __str__(self):
		return str(repr(self))

	def __repr__(self):
		return '<TReq {}: {} {} {}>'.format(self.id, self.traveler, 
			self.activity.name, self.departure_date.strftime('%Y'))


class Vacation(models.Model):
	treq = models.ForeignKey('TravelRequest', on_delete=models.CASCADE)
	start = models.DateField()
	end = models.DateField()

	def __str__(self):
		return str(repr(self))

	def __repr__(self):
		return '<Vacation {}: {} - {}>'.format(self.id, self.start, self.end)


class Activity(models.Model):
	name = models.CharField(max_length=128)
	url = models.URLField(blank=True)
	description = models.TextField(blank=True)
	start = models.DateField()
	end = models.DateField()
	city = models.CharField(max_length=32)
	state = models.CharField(max_length=32)
	country = models.CharField(max_length=32, default='USA')

	class Meta:
		verbose_name_plural = 'Activities'

	def __str__(self):
		return self.name

	def __repr__(self):
		return '<Activity {}: {}>'.format(self.id, self.name)


class Approval(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True)
	approver = models.ForeignKey('Employee', on_delete=models.PROTECT)
	treq = models.ForeignKey('TravelRequest', on_delete=models.CASCADE)
	type = models.CharField(max_length=1, choices=APPROVAL_TYPES)

	def __str__(self):
		return str(repr(self))

	def __repr__(self):
		return '<Approval {}: {} {} {}>'.format(self.id,
			self.get_type_display(), self.treq.activity.name,
			self.treq.traveler)


class EstimatedExpense(models.Model):
	treq = models.ForeignKey('TravelRequest', on_delete=models.CASCADE)
	type = models.CharField(max_length=3, choices=EXPENSE_TYPES)
	rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, 
		blank=True)
	quantity = models.IntegerField(null=True, blank=True)
	total = models.DecimalField(max_digits=10, decimal_places=5)

	def __str__(self):
		return str(repr(self))

	def __repr__(self):
		return '<EstimatedExpense {}: {} {} {}>'.format(self.id,
			self.get_type_display(), self.treq.activity.name,
			self.treq.traveler)


class ActualExpense(models.Model):
	treq = models.ForeignKey('TravelRequest', on_delete=models.CASCADE)
	type = models.CharField(max_length=3, choices=EXPENSE_TYPES)
	rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, 
		blank=True)
	quantity = models.IntegerField(null=True, blank=True)
	total = models.DecimalField(max_digits=10, decimal_places=5)
	fund = models.ForeignKey('Fund', on_delete=models.PROTECT)

	def __str__(self):
		return str(repr(self))

	def __repr__(self):
		return '<ActualExpense {}: {} {} {}>'.format(self.id,
			self.get_type_display(), self.treq.activity.name,
			self.treq.traveler)
