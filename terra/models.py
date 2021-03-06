from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, F

from terra import utils


UNIT_TYPES = (("1", "Library"), ("2", "Executive Division"), ("3", "Managerial Unit"))

EXPENSE_TYPES = (
    ("LDG", "Lodging"),
    ("AIR", "Airfare"),
    ("TRN", "Transit"),
    ("RNT", "Car Rental"),
    ("DRV", "Driving"),
    ("CON", "Conference Registration"),
    ("PRE", "Preconference Fees"),
    ("MEM", "Membership Fees"),
    ("PRK", "Parking"),
    ("EAT", "Meals"),
    ("OTH", "Other"),
)

EMPLOYEE_TYPES = (
    ("ULBR", "University Librarian"),
    ("EXEC", "Executive"),
    ("HEAD", "Unit Head"),
    ("LIBR", "Librarian"),
    ("SENR", "Sr. Exempt Staff"),
    ("OTHR", "Other"),
)


class Unit(models.Model):
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=1, choices=UNIT_TYPES)
    manager = models.ForeignKey(
        "Employee",
        on_delete=models.PROTECT,
        related_name="managed_units",
        null=True,
        blank=True,
    )
    parent_unit = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="subunits", null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Unit {}: {}>".format(self.id, self.name)

    def employee_count(self):
        return self.employee_set.count()

    def super_managers(self, mgrs=None):
        if mgrs is None:
            mgrs = []
        mgrs.append(self.manager)
        if self.parent_unit is None:
            return mgrs
        return self.parent_unit.super_managers(mgrs)

    def all_employees(self):
        team = list(self.employee_set.all())
        for subunit in self.subunits.all():
            team.extend(subunit.all_employees())
        return team


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=32, blank=True)
    unit = models.ForeignKey("Unit", on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    uid = models.CharField(max_length=9, unique=True)
    supervisor = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    type = models.CharField(max_length=4, choices=EMPLOYEE_TYPES, default="OTHR")
    extra_allocation = models.DecimalField(
        max_digits=10, decimal_places=5, null=True, blank=True
    )
    allocation_expire_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = [F("user__last_name"), F("user__first_name")]

    def __str__(self):
        return f"{self.user.last_name}, {self.user.first_name}"

    def __repr__(self):
        return "<Employee {}: {}>".format(self.id, self)

    def name(self):
        return str(self)

    def has_full_report_access(self):
        # Superusers and members of LBS Staff have full access to reports.
        return (
            self.user.is_superuser or self.user.groups.filter(name="LBS Staff").exists()
        )

    def is_UL(self):
        if self.type == "ULBR":
            return True

    def is_unit_manager(self):
        return self.managed_units.count() > 0

    def is_fund_manager(self):
        return self.fund_set.count() > 0

    def direct_reports(self):
        return Employee.objects.filter(supervisor=self)

    def full_team(self):
        staff = [self]
        managers = []
        direct_reports = self.direct_reports()
        if len(direct_reports) > 0:
            managers.append(self)
            for e in direct_reports:
                substaff, submgrs = e.full_team()
                staff.extend(substaff)
                managers.extend(submgrs)
        return staff, managers

    def treqs_in_fiscal_year(self, fiscal_year=None):
        start, end = utils.fiscal_year_bookends(fiscal_year)
        return TravelRequest.objects.filter(
            traveler=self, return_date__lte=end, return_date__gte=start
        )

    def profdev_cap_applies(self):
        if self.type == "HEAD" or self.type == "LIBR" or self.type == "SENR":
            return True

    @property
    def sorted_unit_set(self):
        return self.employee_set.order_by("unit")


class Fund(models.Model):
    account = models.CharField(max_length=6)
    cost_center = models.CharField(max_length=2)
    fund = models.CharField(max_length=5)
    manager = models.ForeignKey("Employee", on_delete=models.PROTECT)
    unit = models.ForeignKey("Unit", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ["account", "cost_center", "fund"]

    def __str__(self):
        return "{}-{}-{}".format(self.account, self.cost_center, self.fund)

    def __repr__(self):
        return "<Fund {}: {}>".format(self.id, self)

    def super_managers(self):
        mgrs = [self.manager]
        while mgrs[-1].supervisor is not None:
            mgrs.append(mgrs[-1].supervisor)
        return mgrs


class TravelRequest(models.Model):
    traveler = models.ForeignKey("Employee", on_delete=models.PROTECT)
    activity = models.ForeignKey("Activity", on_delete=models.PROTECT)
    departure_date = models.DateField()
    return_date = models.DateField()
    days_ooo = models.IntegerField("Days Out of Office")
    closed = models.BooleanField(default=False)
    administrative = models.BooleanField(default=False)
    justification = models.TextField(blank=True)
    funds = models.ManyToManyField("Fund", through="Funding")
    approved_by = models.ForeignKey(
        "Employee",
        on_delete=models.PROTECT,
        related_name="approved_by",
        null=True,
        blank=True,
    )
    approved_on = models.DateField(null=True, blank=True)
    international_approved_on = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)
    canceled = models.BooleanField(default=False)

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<TReq {}: {} {} {}>".format(
            self.id,
            self.traveler,
            self.activity.name,
            self.departure_date.strftime("%Y"),
        )

    def international(self):
        return self.activity.country != "USA"

    def approved(self):
        if self.international():
            return self.international_approved_on is not None
        return self.approved_on is not None

    approved.boolean = True

    def funded(self):
        return self.total_funding() > 0

    funded.boolean = True

    def actual_expenses(self):
        return sum([ae.total for ae in self.actualexpense_set.all()])

    def expenditures_total(self):
        return utils.format_currency(self.actual_expenses())

    def approved_funds(self):
        return sum([a.amount for a in self.funding_set.all()])

    def in_fiscal_year(self, fiscal_year=None):
        return utils.in_fiscal_year(self.return_date, fiscal_year)

    def total_funding(self):
        total = self.funding_set.aggregate(Sum("amount"))["amount__sum"]
        if total is None:
            total = 0
        return total

    in_fiscal_year.boolean = True

    def vacation_days(self):
        return sum([v.vacation_days() for v in self.vacation_set.all()])

    def total_days_out(self):
        total_days = self.vacation_days() + self.days_ooo
        return total_days

    def approved_total(self):
        return utils.format_currency(self.total_funding())


class Vacation(models.Model):
    treq = models.ForeignKey("TravelRequest", on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()
    duration = models.IntegerField(blank=True)

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<Vacation {}: {} - {}>".format(self.id, self.start, self.end)

    def vacation_days(self):
        # Assuming vacation days are inclusive, so add 1 to the difference.
        return (self.end - self.start).days + 1

    def save(self, *args, **kwargs):
        self.duration = self.vacation_days()
        super().save(*args, **kwargs)


class Activity(models.Model):
    name = models.CharField(max_length=128)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    start = models.DateField()
    end = models.DateField()
    city = models.CharField(max_length=32)
    state = models.CharField(max_length=32)
    country = models.CharField(max_length=32, default="USA")

    class Meta:
        ordering = ["name", "-end"]
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Activity {}: {}>".format(self.id, self.name)

    def domestic(self):
        return self.country == "USA"


class Funding(models.Model):
    funded_on = models.DateTimeField(auto_now_add=True)
    funded_by = models.ForeignKey("Employee", on_delete=models.PROTECT)
    treq = models.ForeignKey("TravelRequest", on_delete=models.PROTECT)
    fund = models.ForeignKey("Fund", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=5)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Funding"

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<Funding {}: {} {}>".format(
            self.id, self.treq.activity.name, self.treq.traveler
        )


class ActualExpense(models.Model):
    treq = models.ForeignKey("TravelRequest", on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=EXPENSE_TYPES)
    rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=5)
    fund = models.ForeignKey("Fund", on_delete=models.PROTECT)
    date_paid = models.DateField()
    reimbursed = models.BooleanField(default=False)

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<ActualExpense {}: {} {} {}>".format(
            self.id,
            self.get_type_display(),
            self.treq.activity.name,
            self.treq.traveler,
        )

    def total_dollars(self):
        return "$%.2f" % self.total

    def in_fiscal_year(self, fiscal_year=None):
        return utils.in_fiscal_year(self.date_paid, fiscal_year)
