from datetime import date
from decimal import Decimal
import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder

from fiscalyear import FiscalYear

from .models import (
    Unit,
    Employee,
    Fund,
    TravelRequest,
    Vacation,
    Activity,
    Approval,
    EstimatedExpense,
    ActualExpense,
)
from .templatetags.terra_extras import check_or_cross, currency
from .utils import current_fiscal_year, in_fiscal_year
from terra import reports


class ModelsTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def test_unit(self):
        unit = Unit.objects.get(pk=2)
        self.assertEqual(str(unit), "DIIT")
        self.assertEqual(repr(unit), "<Unit 2: DIIT>")

    def test_unit_super_managers(self):
        u3 = Unit.objects.get(pk=3)
        self.assertEqual(len(u3.super_managers()), 3)

    def test_employee(self):
        employee = Employee.objects.get(pk=3)
        self.assertEqual(str(employee), "Joshua Gomez")
        self.assertEqual(employee.name(), "Joshua Gomez")
        self.assertEqual(repr(employee), "<Employee 3: Joshua Gomez>")
        self.assertEqual(employee.type, "HEAD")

    def test_employee_direct_reports(self):
        mgr1 = Employee.objects.get(pk=3)
        dr1 = mgr1.direct_reports()
        self.assertEqual(len(dr1), 2)
        mgr2 = Employee.objects.get(pk=1)
        dr2 = mgr2.direct_reports()
        self.assertEqual(len(dr2), 1)

    def test_employee_full_team(self):
        head = Employee.objects.get(pk=4)
        staff, mgrs = head.full_team()
        self.assertEqual(len(staff), 6)
        self.assertEqual(len(mgrs), 3)
        sub = Employee.objects.get(pk=3)
        staff, mgrs = sub.full_team()
        self.assertEqual(len(staff), 3)
        self.assertEqual(len(mgrs), 1)

    def test_employee_manager_methods(self):
        emp = Employee.objects.get(pk=2)
        self.assertFalse(emp.is_unit_manager())
        self.assertFalse(emp.is_fund_manager())
        emp = Employee.objects.get(pk=3)
        self.assertTrue(emp.is_unit_manager())
        self.assertTrue(emp.is_fund_manager())

    def test_fund(self):
        fund = Fund.objects.get(pk=1)
        self.assertEqual(str(fund), "605000-LD-19900")
        self.assertEqual(repr(fund), "<Fund 1: 605000-LD-19900>")

    def test_fund_super_managers(self):
        f = Fund.objects.get(pk=1)
        smgrs = f.super_managers()
        self.assertEqual(len(smgrs), 3)
        eids = [mgr.id for mgr in smgrs]
        self.assertEqual(eids, [3, 1, 4])

    def test_treq(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(repr(treq), "<TReq 1: Ashton Prigge Code4lib 2020 2020>")
        self.assertEqual(str(treq), "<TReq 1: Ashton Prigge Code4lib 2020 2020>")

    def test_vacation(self):
        vac = Vacation.objects.get(pk=1)
        self.assertEqual(repr(vac), "<Vacation 1: 2020-02-17 - 2020-02-21>")
        self.assertEqual(str(vac), "<Vacation 1: 2020-02-17 - 2020-02-21>")

    def test_vacation_duration(self):
        treq = TravelRequest.objects.get(pk=1)
        start = date(2020, 2, 10)
        end = date(2020, 2, 12)
        vac = Vacation.objects.create(treq=treq, start=start, end=end)
        self.assertEqual(vac.duration, 3)

    def test_activity(self):
        activity = Activity.objects.get(pk=1)
        self.assertEqual(str(activity), "Code4lib 2020")
        self.assertEqual(repr(activity), "<Activity 1: Code4lib 2020>")

    def test_approval(self):
        approval = Approval.objects.get(pk=1)
        self.assertEqual(repr(approval), "<Approval 1: Code4lib 2020 Ashton Prigge>")
        self.assertEqual(str(approval), "<Approval 1: Code4lib 2020 Ashton Prigge>")

    def test_estimated_expense(self):
        estexp = EstimatedExpense.objects.get(pk=1)
        self.assertEqual(
            repr(estexp),
            "<EstimatedExpense 1: Conference Registration Code4lib 2020 Ashton Prigge>",
        )
        self.assertEqual(
            str(estexp),
            "<EstimatedExpense 1: Conference Registration Code4lib 2020 Ashton Prigge>",
        )

    def test_actual_expense(self):
        actexp = ActualExpense.objects.get(pk=2)
        self.assertEqual(
            repr(actexp),
            "<ActualExpense 2: Conference Registration Summer Con Ashton Prigge>",
        )
        self.assertEqual(
            str(actexp),
            "<ActualExpense 2: Conference Registration Summer Con Ashton Prigge>",
        )

    def test_unit_employee_count(self):
        sdls = Unit.objects.get(pk=3)
        self.assertEqual(sdls.employee_count(), 3)
        for x in range(5):
            u = User.objects.create_user(username=str(x))
            u.save()
            e = Employee(user=u, uid="xxxxxxxx" + str(x), unit=sdls)
            e.save()
        self.assertEqual(sdls.employee_count(), 8)

    def test_treq_international(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(treq.international(), False)
        treq.activity.country = "Germany"
        treq.activity.save()
        self.assertEqual(treq.international(), True)

    def test_treq_approved(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(treq.approved(), True)
        treq.activity.country = "Germany"
        treq.activity.save()
        self.assertEqual(treq.approved(), False)

    def test_treq_funded(self):
        treq = TravelRequest.objects.get(pk=2)
        self.assertEqual(treq.funded(), True)
        a = Approval.objects.get(pk=3)
        a.delete()
        self.assertEqual(treq.funded(), False)

    def test_treq_in_fiscal_year(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(treq.in_fiscal_year(2020), True)
        self.assertEqual(treq.in_fiscal_year(2019), False)

    def test_treq_estimated_expenses(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(treq.estimated_expenses(), 2000)

    def test_treq_actual_expenses(self):
        treq = TravelRequest.objects.get(pk=5)
        self.assertEqual(treq.actual_expenses(), 1855)

    def test_expense_total_dollars(self):
        estexp = EstimatedExpense.objects.get(pk=1)
        self.assertEqual(estexp.total_dollars(), "$250.00")
        actexp = ActualExpense.objects.get(pk=2)
        self.assertEqual(actexp.total_dollars(), "$325.00")

    def test_treq_allocations_total(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(treq.allocations_total(), "$2,000.00")

    def test_treq_expenditures_total(self):
        treq = TravelRequest.objects.get(pk=5)
        self.assertEqual(treq.expenditures_total(), "$1,855.00")


class TemplateTagsTestCase(TestCase):
    def test_check_or_cross(self):
        self.assertEqual(
            check_or_cross(True),
            '<span class="badge badge-pill badge-success">&#10004;</span>',
        )
        self.assertEqual(
            check_or_cross(False),
            '<span class="badge badge-pill badge-danger">&times;</span>',
        )

    def test_currency(self):
        self.assertEqual(currency(0), "$0.00")
        self.assertEqual(currency(3), "$3.00")
        self.assertEqual(currency(-100.0000), "-$100.00")
        self.assertEqual(currency(300000.0000), "$300,000.00")
        self.assertEqual(currency(None), "$0.00")


class TestDashboardView(TestCase):

    fixtures = ["sample_data.json"]

    def test_dashboard_denies_anonymous(self):
        response = self.client.get("/dashboard", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/dashboard/", status_code=301
        )

    def test_dashboard_loads(self):
        self.client.login(username="aprigge", password="Staples50141")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/dashboard.html")
        self.assertEqual(len(response.context["treqs"]), 3)


class TestUnitDetailView(TestCase):

    fixtures = ["sample_data.json"]

    def test_unit_detail_denies_anonymous(self):
        response = self.client.get("/unit/1", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/unit/1/", status_code=301
        )

    def test_unit_detail_requires_manager(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/unit/1/")
        self.assertEqual(response.status_code, 200)
        self.client.login(username="tgrappone", password="Staples50141")
        response = self.client.get("/unit/1/")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/unit/2/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/unit/3/")
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_allows_superuser(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/unit/1/")
        self.assertTemplateUsed(response, "terra/unit.html")
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_loads(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/unit/1/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/unit.html")


class TestUnitListView(TestCase):

    fixtures = ["sample_data.json"]

    def test_unit_list_denies_anonymous(self):
        response = self.client.get("/unit/", follow=True)
        self.assertRedirects(response, "/accounts/login/?next=/unit/", status_code=302)

    def test_unit_detail_allows_superuser(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/unit/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/unit_list.html")

    def test_unit_list_loads(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/unit/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/unit_list.html")


class DataLoadTestCase(TestCase):
    def test_load_units(self):
        call_command("load_units", "terra/fixtures/test_units.csv")
        unit_count = Unit.objects.all().count()
        self.assertEqual(unit_count, 2)
        arts = Unit.objects.get(name__exact="Arts Library")
        self.assertEqual(str(arts), "Arts Library")

    def test_load_employees(self):
        # Employees require Units
        call_command("load_units", "terra/fixtures/test_units.csv")
        call_command("load_employees", "terra/fixtures/test_employees.csv")
        emp_count = Employee.objects.all().count()
        self.assertEqual(emp_count, 2)
        # Edward Employee works for Sally Supervisor
        emp = Employee.objects.get(user=User.objects.get(last_name__exact="Employee"))
        sup = Employee.objects.get(user=User.objects.get(last_name__exact="Supervisor"))
        self.assertEqual(emp.supervisor, sup)

    def test_load_travel_data(self):
        # Travel data requires Employees, which require Units
        call_command("load_units", "terra/fixtures/test_units.csv")
        call_command("load_employees", "terra/fixtures/test_employees.csv")
        call_command("load_travel_data", "terra/fixtures/test_travel_data.csv")
        treq_count = TravelRequest.objects.all().count()
        self.assertEqual(treq_count, 3)
        activity_count = Activity.objects.all().count()
        # 2 people have the same activity, so count is less than treq_count
        self.assertEqual(activity_count, 2)


class UtilsTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def test_current_fiscal_year(self):
        self.assertEqual(current_fiscal_year(date(2018, 7, 1)), 2019)
        self.assertEqual(current_fiscal_year(date(2018, 6, 30)), 2018)

    def test_in_fiscal_year(self):
        self.assertTrue(in_fiscal_year(date(2018, 7, 1), 2019))
        self.assertFalse(in_fiscal_year(date(2018, 7, 1), 2018))
        self.assertTrue(in_fiscal_year(date(2018, 6, 30), 2018))
        self.assertFalse(in_fiscal_year(date(2018, 6, 30), 2019))


class UnitReportsTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def test_unit_totals(self):
        class FakeUser:
            def __init__(self, data):
                self.data = data

        data = [
            FakeUser(
                {
                    "admin_alloc": 0,
                    "admin_expend": 0,
                    "name": "Ashton Prigge",
                    "profdev_alloc": 10300,
                    "profdev_expend": 7420,
                    "total_alloc": 10300,
                    "total_expend": 7420,
                    "traveler__uid": "FAKE002",
                    "uid": "FAKE002",
                    "days_vacation": 5,
                    "days_away": 0,
                    "total_days_ooo": 5,
                }
            ),
            FakeUser(
                {
                    "admin_alloc": 1050,
                    "admin_expend": 0,
                    "name": "Joshua Gomez",
                    "profdev_alloc": 1750,
                    "profdev_expend": 0,
                    "total_alloc": 2800,
                    "total_expend": 0,
                    "traveler__uid": "FAKE003",
                    "uid": "FAKE003",
                    "days_vacation": 9,
                    "days_away": 0,
                    "total_days_ooo": 9,
                }
            ),
            FakeUser(
                {
                    "admin_alloc": 0,
                    "admin_expend": 0,
                    "name": "Tinu Awopetu",
                    "profdev_alloc": 8300,
                    "profdev_expend": 7360,
                    "total_alloc": 8300,
                    "total_expend": 7360,
                    "traveler__uid": "FAKE005",
                    "uid": "FAKE005",
                    "days_vacation": 0,
                    "days_away": 0,
                    "total_days_ooo": 0,
                }
            ),
        ]
        expected = {
            "admin_alloc": 1050,
            "admin_expend": 0,
            "days_away": 0,
            "days_vacation": 14,
            "profdev_alloc": 20350,
            "profdev_expend": 14780,
            "total_alloc": 21400,
            "total_days_ooo": 14,
            "total_expend": 14780,
        }
        actual = reports.unit_totals(data)
        for key, expected_value in expected.items():
            self.assertEqual(actual[key], expected_value)

    def test_unit_report(self):
        expected = {
            "subunits": {
                2: {
                    "subunit_totals": {
                        "profdev_alloc": Decimal("7695"),
                        "admin_alloc": Decimal("2350"),
                        "total_alloc": Decimal("10045"),
                        "profdev_expend": Decimal("3695"),
                        "admin_expend": Decimal("0"),
                        "total_expend": Decimal("3695"),
                        "days_vacation": Decimal("14"),
                        "days_away": Decimal("33"),
                    }
                },
                1: {
                    "subunit_totals": {
                        "profdev_alloc": 0,
                        "admin_alloc": 0,
                        "total_alloc": 0,
                        "profdev_expend": 0,
                        "admin_expend": 0,
                        "total_expend": 0,
                        "days_vacation": 0,
                        "days_away": 0,
                    }
                },
                4: {
                    "subunit_totals": {
                        "profdev_alloc": 0,
                        "admin_alloc": 0,
                        "total_alloc": 0,
                        "profdev_expend": 0,
                        "admin_expend": 0,
                        "total_expend": 0,
                        "days_vacation": 0,
                        "days_away": 0,
                    }
                },
            },
            "unit_totals": {
                "admin_alloc": Decimal("2350"),
                "admin_expend": Decimal("0"),
                "profdev_alloc": Decimal("7695"),
                "profdev_expend": Decimal("3695"),
                "total_alloc": Decimal("10045"),
                "total_expend": Decimal("3695"),
                "days_vacation": Decimal("14"),
                "days_away": Decimal("33"),
            },
        }
        actual = reports.unit_report(Unit.objects.get(pk=1))
        for sid, subunit in expected["subunits"].items():
            for key, value in subunit["subunit_totals"].items():
                self.assertEqual(actual["subunits"][sid]["subunit_totals"][key], value)
        for key, value in expected["unit_totals"].items():
            self.assertEqual(actual["unit_totals"][key], value)

    def test_check_dates_disallows_backward_dates(self):
        self.assertRaises(Exception, reports.check_dates, "2020-01-01", "2019-01-01")

    def test_check_dates_disallows_awkward_dates(self):
        self.assertRaises(Exception, reports.check_dates, None, "2019-01-01")
        self.assertRaises(Exception, reports.check_dates, "2019-01-01", None)


class FundReportsTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def setUp(self):
        self.fy = FiscalYear(2020)
        self.start_date = self.fy.start.date()
        self.end_date = self.fy.end.date()

    def test_get_fund_employee_list(self):
        fund = Fund.objects.get(pk=1)
        eids = reports.get_fund_employee_list(fund, self.start_date, self.end_date)
        expected = [2, 3, 5]
        for eid in eids:
            self.assertTrue(eid in expected)
        fund = Fund.objects.get(pk=2)
        eids = reports.get_fund_employee_list(fund, self.start_date, self.end_date)
        expected = [1, 2]
        for eid in eids:
            self.assertTrue(eid in expected)

    def test_fund_report(self):
        expected = {
            "admin_alloc": Decimal("1050"),
            "admin_expend": Decimal("0"),
            "profdev_alloc": Decimal("7195"),
            "profdev_expend": Decimal("3695"),
            "total_alloc": Decimal("8245"),
            "total_expend": Decimal("3695"),
        }
        fund = Fund.objects.get(pk=1)
        employees, totals = reports.fund_report(fund)
        self.assertEqual(len(employees), 3)
        for key, value in expected.items():
            self.assertEqual(totals[key], value)


class TestFundDetailView(TestCase):

    fixtures = ["sample_data.json"]

    def test_fund_detail_denies_anonymous(self):
        response = self.client.get("/fund/1/", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/fund/1/", status_code=302
        )

    def test_fund_detail_allows_superuser(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/fund/1/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/fund.html")

    def test_fund_detail_loads(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/fund/1/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/fund.html")


class TestFundListView(TestCase):

    fixtures = ["sample_data.json"]

    def test_fund_list_denies_anonymous(self):
        response = self.client.get("/fund/", follow=True)
        self.assertRedirects(response, "/accounts/login/?next=/fund/", status_code=302)

    def test_fund_detail_allows_superuser(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/fund/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/fund_list.html")
