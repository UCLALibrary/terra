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
    Funding,
    ActualExpense,
)
from .templatetags.terra_extras import check_or_cross, currency, cap, days_cap
from .utils import current_fiscal_year, in_fiscal_year, fiscal_year
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
        self.assertEqual(str(employee), "Gomez, Joshua")
        self.assertEqual(employee.name(), "Gomez, Joshua")
        self.assertEqual(repr(employee), "<Employee 3: Gomez, Joshua>")
        self.assertEqual(employee.type, "HEAD")
        self.assertEqual(employee.extra_allocation, 500.00000)

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

    def test_employee_has_full_report_access(self):
        emp = Employee.objects.get(user=User.objects.get(username="doriswang"))
        self.assertTrue(emp.has_full_report_access())
        emp = Employee.objects.get(user=User.objects.get(username="tawopetu"))
        self.assertFalse(emp.has_full_report_access())
        emp.user.groups.add(1)
        self.assertTrue(emp.has_full_report_access())

    def test_employee_treqs_in_fiscal_year(self):
        emp = Employee.objects.get(user=User.objects.get(username="tawopetu"))
        treqs = emp.treqs_in_fiscal_year(2020)
        self.assertEqual(len(treqs), 1)

    def test_employee_is_ul(self):
        emp = Employee.objects.get(pk=4)
        self.assertTrue(emp.is_UL())
        emp = Employee.objects.get(pk=2)
        self.assertFalse(emp.is_UL())

    def test_employee_profdev_cap_applies(self):
        emp = Employee.objects.get(pk=2)
        self.assertTrue(emp.profdev_cap_applies())
        emp = Employee.objects.get(pk=4)
        self.assertFalse(emp.profdev_cap_applies())

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
        self.assertEqual(repr(treq), "<TReq 1: Prigge, Ashton Code4lib 2020 2020>")
        self.assertEqual(str(treq), "<TReq 1: Prigge, Ashton Code4lib 2020 2020>")

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

    def test_funding(self):
        funding = Funding.objects.get(pk=1)
        self.assertEqual(repr(funding), "<Funding 1: Code4lib 2020 Prigge, Ashton>")
        self.assertEqual(str(funding), "<Funding 1: Code4lib 2020 Prigge, Ashton>")

    def test_actual_expense(self):
        actexp = ActualExpense.objects.get(pk=2)
        self.assertEqual(
            repr(actexp),
            "<ActualExpense 2: Conference Registration Summer Con Prigge, Ashton>",
        )
        self.assertEqual(
            str(actexp),
            "<ActualExpense 2: Conference Registration Summer Con Prigge, Ashton>",
        )

    def test_unit_employee_count(self):
        sdls = Unit.objects.get(pk=3)
        self.assertEqual(sdls.employee_count(), 2)
        for x in range(5):
            u = User.objects.create_user(username=str(x))
            u.save()
            e = Employee(user=u, uid="xxxxxxxx" + str(x), unit=sdls)
            e.save()
        self.assertEqual(sdls.employee_count(), 7)

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
        a = Funding.objects.get(pk=3)
        a.delete()
        self.assertEqual(treq.funded(), False)

    def test_treq_in_fiscal_year(self):
        treq = TravelRequest.objects.get(pk=1)
        self.assertEqual(treq.in_fiscal_year(2020), True)
        self.assertEqual(treq.in_fiscal_year(2019), False)

    def test_treq_actual_expenses(self):
        treq = TravelRequest.objects.get(pk=5)
        self.assertEqual(treq.actual_expenses(), 1855)

    def test_treq_approved_funds(self):
        treq = TravelRequest.objects.get(pk=9)
        self.assertEqual(treq.approved_funds(), 3500)

    def test_expense_total_dollars(self):
        actexp = ActualExpense.objects.get(pk=2)
        self.assertEqual(actexp.total_dollars(), "$325.00")

    def test_treq_expenditures_total(self):
        treq = TravelRequest.objects.get(pk=5)
        self.assertEqual(treq.expenditures_total(), "$1,855.00")

    def test_treq_domestic(self):
        act = Activity.objects.get(pk=4)
        self.assertTrue(act.domestic())
        act = Activity.objects.get(pk=5)
        self.assertFalse(act.domestic())


class TemplateTagsTestCase(TestCase):
    def test_check_or_cross(self):
        self.assertEqual(
            check_or_cross(True),
            '<span class="badge badge-pill badge-success">YES</span>',
        )
        self.assertEqual(
            check_or_cross(False),
            '<span class="badge badge-pill badge-danger">NO</span>',
        )

    def test_currency(self):
        self.assertEqual(currency(0), "$0.00")
        self.assertEqual(currency(3), "$3.00")
        self.assertEqual(currency(-100.0000), "-$100.00")
        self.assertEqual(currency(300000.0000), "$300,000.00")
        self.assertEqual(currency(None), "$0.00")

    def test_cap(self):
        self.assertEqual(cap(3600), '<span class="alert-danger">$3,600.00</span>')
        self.assertEqual(cap(3400), '<span class="alert-warning">$3,400.00</span>')
        self.assertEqual(cap(1600), "$1,600.00")
        self.assertEqual(cap(None), "$0.00")
        self.assertEqual(cap(0), "$0.00")

    def test_days_cap(self):
        self.assertEqual(days_cap(17), '<span class="alert-danger">17</span>')
        self.assertEqual(days_cap(12), '<span class="alert-warning">12</span>')
        self.assertEqual(days_cap(10), 10)
        self.assertEqual(days_cap(None), 0)
        self.assertEqual(days_cap(0), 0)


class TestEmpoyeeDetailView(TestCase):

    fixtures = ["sample_data.json"]

    def test_employee_detail_denies_anonymous(self):
        response = self.client.get("/employee/3/2020/", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/employee/3/2020/", status_code=302
        )

    def test_employee_detail_requires_manager(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/employee/1/2020/")
        self.assertEqual(response.status_code, 200)
        self.client.login(username="tawopetu", password="Staples50141")
        response = self.client.get("/employee/3/2020/")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/employee/5/2020/")
        self.assertEqual(response.status_code, 200)

    def test_employee_detail_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/employee/2/2020/")
        self.assertTemplateUsed(response, "terra/employee.html")
        self.assertEqual(response.status_code, 200)

    def test_employee_detail_loads(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/employee/2/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/employee.html")

    def test_employee_detail_loads(self):
        self.client.login(username="aprigge", password="Staples50141")
        response = self.client.get("/employee/2/2019/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/employee.html")


class TestUnitDetailView(TestCase):

    fixtures = ["sample_data.json"]

    def test_unit_detail_denies_anonymous(self):
        response = self.client.get("/unit/1/2020/", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/unit/1/2020/", status_code=302
        )

    def test_unit_detail_requires_manager(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/unit/1/2020/")
        self.assertEqual(response.status_code, 200)
        self.client.login(username="tgrappone", password="Staples50141")
        response = self.client.get("/unit/1/2020/")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/unit/2/2019/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/unit/3/2019/")
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/unit/1/2020/")
        self.assertTemplateUsed(response, "terra/unit.html")
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_loads(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/unit/1/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/unit.html")


class TestTreqDetailView(TestCase):
    fixtures = ["sample_data.json"]

    def test_treq_detail_denies_anonymous(self):
        response = self.client.get("/treq/1", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/treq/1/", status_code=301
        )

    def test_treq_detail_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/treq/2/")
        self.assertTemplateUsed(response, "terra/treq.html")
        self.assertEqual(response.status_code, 200)

    def test_treq_detail_allows_fund_manager(self):
        self.client.login(username="tawopetu", password="Staples50141")
        response = self.client.get("/treq/5/")
        self.assertEqual(response.status_code, 200)

    def test_treq_detail_loads(self):
        self.client.login(username="aprigge", password="Staples50141")
        response = self.client.get("/treq/1/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/treq.html")


class TestUnitListView(TestCase):

    fixtures = ["sample_data.json"]

    def test_unit_list_denies_anonymous(self):
        response = self.client.get("/unit/", follow=True)
        self.assertRedirects(response, "/accounts/login/?next=/unit/", status_code=302)

    def test_unit_detail_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/unit/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/unit_list.html")

    def test_unit_list_loads(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/unit/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/unit_list.html")


# This test case disabled for now; see bug TRRA-195.
# class DataLoadTestCase(TestCase):

#     @classmethod
#     def setUpTestData(cls):
#         # Travel data requires Employees, which require Units
#         call_command("load_units", "terra/fixtures/test_units.csv")
#         call_command("load_employees", "terra/fixtures/test_employees.csv")
#         call_command("load_travel_data", "terra/fixtures/test_travel_data.csv")

#     def test_load_units(self):
#         unit_count = Unit.objects.all().count()
#         self.assertEqual(unit_count, 3)
#         unit = Unit.objects.get(name__exact="East Asian Library")
#         self.assertEqual(str(unit), "East Asian Library")

#     def test_load_employees(self):
#         emp_count = Employee.objects.all().count()
#         # Edward, Sally, and fake placeholder = 3
#         self.assertEqual(emp_count, 3)
#         # Edward Employee works for Sally Supervisor
#         emp = Employee.objects.get(user=User.objects.get(last_name__exact="Employee"))
#         sup = Employee.objects.get(user=User.objects.get(last_name__exact="Supervisor"))
#         self.assertEqual(emp.supervisor, sup)

#     def test_load_travel_data(self):
#         treq_count = TravelRequest.objects.all().count()
#         self.assertEqual(treq_count, 3)
#         activity_count = Activity.objects.all().count()
#         # 2 people have the same activity, so count is less than treq_count
#         self.assertEqual(activity_count, 2)


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

    def setUp(self):
        self.fy = FiscalYear(2020)
        self.start_date = self.fy.start.date()
        self.end_date = self.fy.end.date()

    def test_unit_totals(self):
        class FakeUser:
            def __init__(self, data):
                self.data = data

        data = [
            FakeUser(
                {
                    "admin_requested": 0,
                    "admin_spent": 0,
                    "name": "Ashton Prigge",
                    "profdev_requested": 10300,
                    "profdev_spent": 7420,
                    "total_requested": 10300,
                    "total_spent": 7420,
                    "traveler__uid": "FAKE002",
                    "uid": "FAKE002",
                    "days_vacation": 5,
                    "profdev_days_away": 0,
                    "admin_days_away": 0,
                    "total_days_ooo": 0,
                }
            ),
            FakeUser(
                {
                    "admin_requested": 1050,
                    "admin_spent": 0,
                    "name": "Joshua Gomez",
                    "profdev_requested": 1750,
                    "profdev_spent": 0,
                    "total_requested": 2800,
                    "total_spent": 0,
                    "traveler__uid": "FAKE003",
                    "uid": "FAKE003",
                    "days_vacation": 9,
                    "profdev_days_away": 0,
                    "admin_days_away": 0,
                    "total_days_ooo": 0,
                }
            ),
            FakeUser(
                {
                    "admin_requested": 0,
                    "admin_spent": 0,
                    "name": "Tinu Awopetu",
                    "profdev_requested": 8300,
                    "profdev_spent": 7360,
                    "total_requested": 8300,
                    "total_spent": 7360,
                    "traveler__uid": "FAKE005",
                    "uid": "FAKE005",
                    "days_vacation": 0,
                    "profdev_days_away": 0,
                    "admin_days_away": 0,
                    "total_days_ooo": 0,
                }
            ),
        ]
        expected = {
            "admin_requested": 1050,
            "admin_spent": 0,
            "admin_days_away": 0,
            "profdev_days_away": 0,
            "days_vacation": 14,
            "profdev_requested": 20350,
            "profdev_spent": 14780,
            "total_requested": 21400,
            "total_days_ooo": 0,
            "total_spent": 14780,
        }
        actual = reports.unit_totals(data)
        for key, expected_value in expected.items():
            with self.subTest(key=key, value=expected_value):
                self.assertEqual(actual[key], expected_value)

    def test_unit_report(self):
        expected = {
            "subunits": {
                2: {
                    "subunit_totals": {
                        "profdev_requested": Decimal("6000"),
                        "admin_requested": Decimal("2350"),
                        "total_requested": Decimal("8350"),
                        "profdev_spent": Decimal("4345"),
                        "admin_spent": Decimal("0"),
                        "total_spent": Decimal("4345"),
                        "days_vacation": Decimal("14"),
                        "profdev_days_away": Decimal("42"),
                        "admin_days_away": Decimal("3"),
                        "total_days_ooo": Decimal("45"),
                    }
                },
                1: {
                    "subunit_totals": {
                        "profdev_requested": 0,
                        "admin_requested": 0,
                        "total_requested": 0,
                        "profdev_spent": 0,
                        "admin_spent": 0,
                        "total_spent": 0,
                        "days_vacation": 0,
                        "profdev_days_away": 0,
                        "admin_days_away": 0,
                        "total_days_ooo": 0,
                    }
                },
                4: {
                    "subunit_totals": {
                        "profdev_requested": 0,
                        "admin_requested": 0,
                        "total_requested": 0,
                        "profdev_spent": 0,
                        "admin_spent": 0,
                        "total_spent": 0,
                        "days_vacation": 0,
                        "profdev_days_away": 0,
                        "admin_days_away": 0,
                        "total_days_ooo": 0,
                    }
                },
            },
            "unit_totals": {
                "admin_requested": Decimal("2350"),
                "admin_spent": Decimal("0"),
                "profdev_requested": Decimal("6000"),
                "profdev_spent": Decimal("4345"),
                "total_requested": Decimal("8350"),
                "total_spent": Decimal("4345"),
                "days_vacation": Decimal("14"),
                "profdev_days_away": Decimal("42"),
                "admin_days_away": Decimal("3"),
                "total_days_ooo": Decimal("45"),
            },
        }
        actual = reports.unit_report(
            Unit.objects.get(pk=1), start_date=self.start_date, end_date=self.end_date
        )
        for sid, subunit in expected["subunits"].items():
            for key, value in subunit["subunit_totals"].items():
                with self.subTest(key=key, value=value):
                    self.assertEqual(
                        actual["subunits"][sid]["subunit_totals"][key], value
                    )
        for key, value in expected["unit_totals"].items():
            with self.subTest(key=key, value=value):
                self.assertEqual(actual["unit_totals"][key], value)

    def test_check_dates_disallows_backward_dates(self):
        self.assertRaises(Exception, reports.check_dates, "2020-01-01", "2019-01-01")

    def test_check_dates_disallows_awkward_dates(self):
        self.assertRaises(Exception, reports.check_dates, None, "2019-01-01")
        self.assertRaises(Exception, reports.check_dates, "2019-01-01", None)

    def test_ooo_is_for_specified_fiscal_year_only(self):
        data = reports.get_individual_data(
            [5], start_date=self.start_date, end_date=self.end_date
        )
        self.assertEqual(data[0]["days_vacation"], 0)
        data = reports.get_individual_data(
            [5], start_date="2018-07-01", end_date="2019-06-30"
        )
        self.assertEqual(data[0]["days_vacation"], 5)


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
            with self.subTest(eid=eid):
                self.assertTrue(eid in expected)
        fund = Fund.objects.get(pk=2)
        eids = reports.get_fund_employee_list(fund, self.start_date, self.end_date)
        expected = [1, 2]
        for eid in eids:
            with self.subTest(eid=eid):
                self.assertTrue(eid in expected)

    def test_get_treq_list(self):
        fund = Fund.objects.get(pk=2)
        treqs = reports.get_treq_list(fund, self.start_date, self.end_date)
        expected = [1, 7]
        for treq in treqs:
            self.assertTrue(treq in expected)

    def test_get_individual_data_for_treq(self):
        fund = Fund.objects.get(pk=3)
        treq_ids = reports.get_treq_list(fund, self.start_date, self.end_date)
        actual = reports.get_individual_data_for_treq(
            treq_ids, fund, self.start_date, self.end_date
        )
        for treq in actual:
            self.assertEqual(treq.profdev_requested, Decimal(0))
            self.assertEqual(treq.profdev_spent, Decimal(180))
            self.assertEqual(treq.admin_requested, Decimal(0))
            self.assertEqual(treq.admin_spent, Decimal(0))

    def test_fund_report(self):
        expected = {
            "admin_requested": Decimal("1050"),
            "admin_spent": Decimal("0"),
            "profdev_requested": Decimal("5500.00000"),
            "profdev_spent": Decimal("4165"),
            "total_requested": Decimal("6550.00000"),
            "total_spent": Decimal("4165"),
        }
        fund = Fund.objects.get(pk=1)
        employees, totals = reports.fund_report(fund)
        self.assertEqual(len(employees), 3)
        for key, value in expected.items():
            with self.subTest(key=key, value=value):
                self.assertEqual(totals[key], value)


class TestFundDetailView(TestCase):

    fixtures = ["sample_data.json"]

    def test_fund_detail_denies_anonymous(self):
        response = self.client.get("/fund/1/2020/", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/fund/1/2020/", status_code=302
        )

    def test_fund_detail_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/fund/1/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/fund.html")

    def test_fund_denies_non_lbs(self):
        self.client.login(username="tawopetu", password="Staples50141")
        response = self.client.get("/fund/1/2020/")
        self.assertEqual(response.status_code, 403)

    def test_fund_detail_loads(self):
        self.client.login(username="aprigge", password="Staples50141")
        response = self.client.get("/fund/1/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/fund.html")


class TestFundListView(TestCase):

    fixtures = ["sample_data.json"]

    def test_fund_list_denies_anonymous(self):
        response = self.client.get("/fund/", follow=True)
        self.assertRedirects(response, "/accounts/login/?next=/fund/", status_code=302)

    def test_fund_detail_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/fund/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/fund_list.html")


class EmployeeTypeReportsTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def setUp(self):
        self.fy = FiscalYear(2020)
        self.start_date = self.fy.start.date()
        self.end_date = self.fy.end.date()

    def test_get_type_and_employees(self):

        expected = {
            "University Librarian": ["<Employee 4: Steel, Virginia>"],
            "Executive": [],
            "Unit Head": [
                "<Employee 1: Grappone, Todd>",
                "<Employee 6: Wang, Doris>",
                "<Employee 3: Gomez, Joshua>",
            ],
            "Librarian": ["<Employee 2: Prigge, Ashton>"],
            "Sr. Exempt Staff": ["<Employee 5: Awopetu, Tinu>"],
            "Other": [],
        }
        actual = reports.get_type_and_employees()
        for employee in expected:
            self.assertTrue(employee in actual)

    def test_type_report(self):
        expected = {
            "type": {
                "University Librarian": {
                    "employees": [
                        {
                            "id": 4,
                            "profdev_requested": Decimal("0.00000"),
                            "profdev_spent": Decimal("0.00000"),
                            "admin_requested": Decimal("0.00000"),
                            "admin_spent": Decimal("0.00000"),
                            "days_vacation": 0,
                            "profdev_days_away": 0,
                            "admin_days_away": 0,
                            "name": "Steel, Virginia",
                            "unit": "Library",
                            "unit_manager": "Steel, Virginia",
                            "total_requested": Decimal("0.00000"),
                            "total_spent": Decimal("0.00000"),
                            "total_days_ooo": 0,
                        }
                    ],
                    "totals": {
                        "admin_requested": Decimal("0.00000"),
                        "admin_spent": Decimal("0.00000"),
                        "admin_days_away": 0,
                        "profdev_days_away": 0,
                        "days_vacation": 0,
                        "profdev_requested": Decimal("0.00000"),
                        "profdev_spent": Decimal("0.00000"),
                        "total_requested": Decimal("0.00000"),
                        "total_days_ooo": 0,
                        "total_spent": Decimal("0.00000"),
                    },
                },
                "Executive": {
                    "employees": [],
                    "totals": {
                        "admin_requested": 0,
                        "admin_spent": 0,
                        "admin_days_away": 0,
                        "profdev_days_away": 0,
                        "days_vacation": 0,
                        "profdev_requested": 0,
                        "profdev_spent": 0,
                        "total_requested": 0,
                        "total_days_ooo": 0,
                        "total_spent": 0,
                    },
                },
                "Unit Head": {
                    "employees": [
                        {
                            "id": 1,
                            "profdev_requested": Decimal("0.00000"),
                            "profdev_spent": Decimal("0.00000"),
                            "admin_requested": Decimal("1300.00000"),
                            "admin_spent": Decimal("0.00000"),
                            "days_vacation": 0,
                            "profdev_days_away": 0,
                            "admin_days_away": 3,
                            "name": "Grappone, Todd",
                            "unit": "DIIT",
                            "unit_manager": "Grappone, Todd",
                            "total_requested": Decimal("1300.00000"),
                            "total_spent": Decimal("0.00000"),
                            "total_days_ooo": 3,
                        },
                        {
                            "id": 6,
                            "profdev_requested": Decimal("0.00000"),
                            "profdev_spent": Decimal("0.00000"),
                            "admin_requested": Decimal("0.00000"),
                            "admin_spent": Decimal("0.00000"),
                            "days_vacation": 0,
                            "profdev_days_away": 0,
                            "admin_days_away": 0,
                            "name": "Wang, Doris",
                            "unit": "Library Business Services",
                            "unit_manager": "Wang, Doris",
                            "total_requested": Decimal("0.00000"),
                            "total_spent": Decimal("0.00000"),
                            "total_days_ooo": 0,
                        },
                        {
                            "id": 3,
                            "profdev_requested": Decimal("2000.00000"),
                            "profdev_spent": Decimal("0.00000"),
                            "admin_requested": Decimal("1050.00000"),
                            "admin_spent": Decimal("0.00000"),
                            "days_vacation": 9,
                            "profdev_days_away": 10,
                            "admin_days_away": 0,
                            "name": "Gomez, Joshua",
                            "unit": "Software Development & Library Systems",
                            "unit_manager": "Gomez, Joshua",
                            "total_requested": Decimal("3050.00000"),
                            "total_spent": Decimal("0.00000"),
                            "total_days_ooo": 10,
                        },
                    ],
                    "totals": {
                        "admin_requested": Decimal("2350.00000"),
                        "admin_spent": Decimal("0.00000"),
                        "admin_days_away": 3,
                        "profdev_days_away": 10,
                        "days_vacation": 9,
                        "profdev_requested": Decimal("2000.00000"),
                        "profdev_spent": Decimal("0.00000"),
                        "total_requested": Decimal("4350.00000"),
                        "total_days_ooo": 13,
                        "total_spent": Decimal("0.00000"),
                    },
                },
                "Librarian": {
                    "employees": [
                        {
                            "id": 2,
                            "profdev_requested": Decimal("4000.00000"),
                            "profdev_spent": Decimal("1420.00000"),
                            "admin_requested": Decimal("0.00000"),
                            "admin_spent": Decimal("0.00000"),
                            "days_vacation": 5,
                            "profdev_days_away": 20,
                            "admin_days_away": 0,
                            "name": "Prigge, Ashton",
                            "unit": "Software Development & Library Systems",
                            "unit_manager": "Gomez, Joshua",
                            "total_requested": Decimal("4000.00000"),
                            "total_spent": Decimal("1420.00000"),
                            "total_days_ooo": 20,
                        }
                    ],
                    "totals": {
                        "admin_requested": Decimal("0.00000"),
                        "admin_spent": Decimal("0.00000"),
                        "admin_days_away": 0,
                        "profdev_days_away": 20,
                        "days_vacation": 5,
                        "profdev_requested": Decimal("4000.00000"),
                        "profdev_spent": Decimal("1420.00000"),
                        "total_requested": Decimal("4000.00000"),
                        "total_days_ooo": 20,
                        "total_spent": Decimal("1420.00000"),
                    },
                },
                "Sr. Exempt Staff": {
                    "employees": [
                        {
                            "id": 5,
                            "profdev_requested": Decimal("0.00000"),
                            "profdev_spent": Decimal("2925.00000"),
                            "admin_requested": Decimal("0.00000"),
                            "admin_spent": Decimal("0.00000"),
                            "days_vacation": 0,
                            "profdev_days_away": 12,
                            "admin_days_away": 0,
                            "name": "Awopetu, Tinu",
                            "unit": "UX Team",
                            "unit_manager": "Awopetu, Tinu",
                            "total_requested": Decimal("0.00000"),
                            "total_spent": Decimal("2925.00000"),
                            "total_days_ooo": 12,
                        }
                    ],
                    "totals": {
                        "admin_requested": Decimal("0.00000"),
                        "admin_spent": Decimal("0.00000"),
                        "admin_days_away": 0,
                        "profdev_days_away": 12,
                        "days_vacation": 0,
                        "profdev_requested": Decimal("0.00000"),
                        "profdev_spent": Decimal("2925.00000"),
                        "total_requested": Decimal("0.00000"),
                        "total_days_ooo": 12,
                        "total_spent": Decimal("2925.00000"),
                    },
                },
                "Other": {
                    "employees": [],
                    "totals": {
                        "admin_requested": 0,
                        "admin_spent": 0,
                        "admin_days_away": 0,
                        "profdev_days_away": 0,
                        "days_vacation": 0,
                        "profdev_requested": 0,
                        "profdev_spent": 0,
                        "total_requested": 0,
                        "total_days_ooo": 0,
                        "total_spent": 0,
                    },
                },
            },
            "all_type_total": {
                "admin_requested": Decimal("2350.00000"),
                "admin_spent": Decimal("0.00000"),
                "profdev_days_away": 42,
                "admin_days_away": 3,
                "days_vacation": 14,
                "profdev_requested": Decimal("6000.00000"),
                "profdev_spent": Decimal("4345.00000"),
                "total_requested": Decimal("8350.00000"),
                "total_days_ooo": 45,
                "total_spent": Decimal("4345.00000"),
            },
        }

        actual = reports.merge_data_type(
            employee_ids=[4, 1, 6, 3, 2, 5],
            start_date=date(2019, 7, 1),
            end_date=date(2020, 6, 30),
        )

        self.assertEqual(expected["type"].keys(), actual["type"].keys())
        self.assertEqual(expected["all_type_total"], actual["all_type_total"])
        for employee_type in expected["type"].keys():
            self.assertEqual(
                expected["type"][employee_type]["totals"],
                actual["type"][employee_type]["totals"],
            )
            self.assertEqual(
                expected["type"][employee_type]["employees"],
                actual["type"][employee_type]["employees"],
            )

    def test_type_report_denies_anonymous(self):
        response = self.client.get("/employee_type_list/2020/", follow=True)
        self.assertRedirects(
            response, "/accounts/login/?next=/employee_type_list/2020/", status_code=302
        )

    def test_type_report_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/employee_type_list/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/employee_type_list.html")

    def test_type_report_denies_non_UL(self):
        self.client.login(username="tgrappone", password="Staples50141")
        response = self.client.get("/employee_type_list/2020/")
        self.assertEqual(response.status_code, 403)

    def test_type_report_allows_UL(self):
        self.client.login(username="vsteel", password="Staples50141")
        response = self.client.get("/employee_type_list/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/employee_type_list.html")


class ReportTestCase(TestCase):

    fixtures = ["sample_report.json"]

    def test_individual_data(self):
        expected = {
            "id": 2,
            "profdev_requested": Decimal("4000.00000"),
            "profdev_spent": Decimal("4000.00000"),
            "admin_requested": Decimal("8000.00000"),
            "admin_spent": Decimal("8220.00000"),
            "days_vacation": 0,
            "profdev_days_away": 15,
            "admin_days_away": 12,
        }
        employee_ids = [2]
        start_date = date(2019, 7, 1)
        end_date = date(2020, 6, 30)
        actual = reports.get_individual_data(employee_ids, start_date, end_date)
        for x in actual:
            for key, value in x.items():
                with self.subTest(key=key, value=value):
                    self.assertEqual(x[key], expected[key])


class EmployeeSubtotalTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def test_subtotal(self):
        expected = {
            "id": 2,
            "admin_requested": Decimal("0.0000"),
            "admin_spent": Decimal("0.0000"),
            "days_away": 20,
            "profdev_days_away": 20,
            "days_vacation": 5,
            "profdev_requested": Decimal("4000.0000"),
            "profdev_spent": Decimal("1420.0000"),
            "total_requested": Decimal(4000),
            "total_days_ooo": 20,
            "total_spent": Decimal("1420.0000"),
        }
        employee_ids = [2]
        start_date = date(2019, 7, 1)
        end_date = date(2020, 6, 30)
        actual = reports.get_individual_data_employee(
            employee_ids, start_date, end_date
        )
        for x in actual:
            for key, value in x.items():
                with self.subTest(key=key, value=value):
                    self.assertEqual(x[key], expected[key])


class ActualExpenseTestCase(TestCase):

    fixtures = ["sample_data.json"]

    def test_actualexpense_report_denies_anonymous(self):
        response = self.client.get("/actual_expense_report/2020/", follow=True)
        self.assertRedirects(
            response,
            "/accounts/login/?next=/actual_expense_report/2020/",
            status_code=302,
        )

    def test_actualexpense_report_allows_full_access(self):
        self.client.login(username="doriswang", password="Staples50141")
        response = self.client.get("/actual_expense_report/2020/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "terra/actual_expense_report.html")

    def test_unit_and_employee(self):
        expected = {
            "subunits": {
                1: {
                    "subunit": "<Unit 1: Library>",
                    "employees": {4: "<Employee 4: Steel, Virginia>"},
                },
                2: {
                    "subunit": "<Unit 2: DIIT>",
                    "employees": {
                        1: "<Employee 1: Grappone, Todd>",
                        5: "<Employee 5: Awopetu, Tinu>",
                        3: "<Employee 3: Gomez, Joshua>",
                        2: "<Employee 2: Prigge, Ashton>",
                    },
                },
                4: {
                    "subunit": "<Unit 4: Library Business Services>",
                    "employees": {6: "<Employee 6: Wang, Doris>"},
                },
            }
        }
        actual = reports.get_subunits_and_employees(Unit.objects.get(pk=1))
        self.assertEqual(actual["subunits"].keys(), expected["subunits"].keys())

        for key in actual["subunits"].keys():
            self.assertEqual(
                actual["subunits"][key]["employees"].keys(),
                expected["subunits"][key]["employees"].keys(),
            )

    def test_actual_expenses(self):
        actualexpense = ActualExpense.objects.get(pk=2)
        self.assertEqual(actualexpense.total, Decimal("325.00000"))
        self.assertEqual(actualexpense.fund.pk, 1)
        self.assertEqual(actualexpense.reimbursed, False)
        self.assertEqual(actualexpense.treq.pk, 5)


class TravelRequestReportTestCase(TestCase):
    fixtures = ["sample_data.json"]

    def test_get_individual_data_treq(self):
        expected = [
            {
                "id": 1,
                "actualexpenses_fy": Decimal("0.00000"),
                "funding_fy": Decimal("4000.00000"),
            },
            {
                "id": 2,
                "actualexpenses_fy": Decimal("0.00000"),
                "funding_fy": Decimal("2000.00000"),
            },
            {
                "id": 3,
                "actualexpenses_fy": Decimal("0.00000"),
                "funding_fy": Decimal("1050.00000"),
            },
            {
                "id": 4,
                "actualexpenses_fy": Decimal("0.00000"),
                "funding_fy": Decimal("0.00000"),
            },
            {
                "id": 5,
                "actualexpenses_fy": Decimal("1420.00000"),
                "funding_fy": Decimal("0.00000"),
            },
        ]
        treq_list = [1, 2, 3, 4, 5]
        fy = fiscal_year(2020)
        actual = reports.get_individual_data_treq(
            treq_ids=treq_list, start_date=fy.start.date(), end_date=fy.end.date()
        )

        # checking each item in each list
        for n in range(0, len(treq_list) - 1):
            self.assertEqual(actual[n], expected[n])
