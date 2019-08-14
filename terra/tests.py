from django.test import TestCase

from .models import Unit, Employee, Fund, TravelRequest, Vacation, Activity, \
	Approval, EstimatedExpense, ActualExpense


class ModelsTestCase(TestCase):
	fixtures = ['sample_data.json']

	def test_unit(self):
		unit = Unit.objects.get(pk=2)
		self.assertEqual(str(unit), 'DIIT')
		self.assertEqual(repr(unit), '<Unit 2: DIIT>')

	def test_employee(self):
		employee = Employee.objects.get(pk=3)
		self.assertEqual(str(employee), 'Joshua Gomez')
		self.assertEqual(repr(employee), '<Employee 3: Joshua Gomez>')

	def test_fund(self):
		fund = Fund.objects.get(pk=1)
		self.assertEqual(str(fund), '605000-LD-19900')
		self.assertEqual(repr(fund), '<Fund 1: 605000-LD-19900>')

	def test_treq(self):
		treq = TravelRequest.objects.get(pk=1)
		self.assertEqual(repr(treq), '<TReq 1: Ashton Prigge Code4lib 2020 2020>')
		self.assertEqual(str(treq), '<TReq 1: Ashton Prigge Code4lib 2020 2020>')

	def test_vacation(self):
		vac = Vacation.objects.get(pk=1)
		self.assertEqual(repr(vac), '<Vacation 1: 2020-02-17 - 2020-02-22>')
		self.assertEqual(str(vac), '<Vacation 1: 2020-02-17 - 2020-02-22>')

	def test_activity(self):
		activity = Activity.objects.get(pk=1)
		self.assertEqual(str(activity), 'Code4lib 2020')
		self.assertEqual(repr(activity), '<Activity 1: Code4lib 2020>')

	def test_approval(self):
		approval = Approval.objects.get(pk=1)
		self.assertEqual(repr(approval), '<Approval 1: Supervisor Code4lib 2020 Ashton Prigge>')
		self.assertEqual(str(approval), '<Approval 1: Supervisor Code4lib 2020 Ashton Prigge>')

	def test_estimated_expense(self):
		estexp = EstimatedExpense.objects.get(pk=1)
		self.assertEqual(repr(estexp), '<EstimatedExpense 1: Conference Registration Code4lib 2020 Ashton Prigge>')
		self.assertEqual(str(estexp), '<EstimatedExpense 1: Conference Registration Code4lib 2020 Ashton Prigge>')

	def actual_expense(self):
		actexp = ActualExpense.objects.get(pk=1)
		self.assertEqual(repr(actexp), '<ActualExpense 1: Conference Registration Code4lib 2020 Ashton Prigge>')
		self.assertEqual(str(actexp), '<ActualExpense 1: Conference Registration Code4lib 2020 Ashton Prigge>')
