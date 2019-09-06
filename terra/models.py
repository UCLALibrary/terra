from django.db import models
from django.contrib.auth.models import User

from terra import utils


UNIT_TYPES = (
    ("1", "Library"),
    ("2", "Executive Division"),
    ("3", "Managerial Unit"),
    ("4", "Team"),
)

APPROVAL_TYPES = (("S", "Supervisor"), ("F", "Funding"), ("I", "International"))

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Unit {}: {}>".format(self.id, self.name)

    def employee_count(self):
        return self.employee_set.count()

    def full_team(self):
        team = list(self.employee_set.all())
        for subunit in self.subunits.all():
            team.extend(subunit.full_team())
        return team

    def sub_teams(self):
        output = {self.name: self.employee_set.all()}
        for subunit in self.subunits.all():
            output[subunit.name] = subunit.full_team()
        return output


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=32, blank=True)
    unit = models.ForeignKey("Unit", on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    uid = models.CharField(max_length=9, unique=True)
    supervisor = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )

    def __str__(self):
        return self.user.get_full_name()

    def __repr__(self):
        return "<Employee {}: {}>".format(self.id, self)

    def name(self):
        return str(self)

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


class Fund(models.Model):
    account = models.CharField(max_length=6)
    cost_center = models.CharField(max_length=2)
    fund = models.CharField(max_length=5)
    manager = models.ForeignKey("Employee", on_delete=models.PROTECT)

    def __str__(self):
        return "{}-{}-{}".format(self.account, self.cost_center, self.fund)

    def __repr__(self):
        return "<Fund {}: {}>".format(self.id, self)


class TravelRequest(models.Model):
    traveler = models.ForeignKey("Employee", on_delete=models.PROTECT)
    activity = models.ForeignKey("Activity", on_delete=models.PROTECT)
    departure_date = models.DateField()
    return_date = models.DateField()
    days_ooo = models.IntegerField("Days Out of Office")
    closed = models.BooleanField(default=False)
    administrative = models.BooleanField(default=False)
    justification = models.TextField(blank=True)
    funding = models.ManyToManyField(Fund)

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
            return len(self.approval_set.filter(type="I")) == 1
        return len(self.approval_set.filter(type="S")) == 1

    approved.boolean = True

    def funded(self):
        return len(self.approval_set.filter(type="F")) == 1

    funded.boolean = True

    def estimated_expenses(self):
        total = 0
        for ee in self.estimatedexpense_set.all():
            total += ee.total
        return total

    def allocations_total(self):
        return utils.format_currency(self.estimated_expenses())

    def actual_expenses(self):
        total = 0
        for ae in self.actualexpense_set.all():
            total += ae.total
        return total

    def expenditures_total(self):
        return utils.format_currency(self.actual_expenses())

    def in_fiscal_year(self, fiscal_year=None):
        return utils.in_fiscal_year(self.return_date, fiscal_year)

    in_fiscal_year.boolean = True


class Vacation(models.Model):
    treq = models.ForeignKey("TravelRequest", on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<Vacation {}: {} - {}>".format(self.id, self.start, self.end)


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
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Activity {}: {}>".format(self.id, self.name)


class Approval(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    approver = models.ForeignKey("Employee", on_delete=models.PROTECT)
    treq = models.ForeignKey("TravelRequest", on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=APPROVAL_TYPES)

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<Approval {}: {} {} {}>".format(
            self.id,
            self.get_type_display(),
            self.treq.activity.name,
            self.treq.traveler,
        )


class EstimatedExpense(models.Model):
    treq = models.ForeignKey("TravelRequest", on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=EXPENSE_TYPES)
    rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=5)

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        return "<EstimatedExpense {}: {} {} {}>".format(
            self.id,
            self.get_type_display(),
            self.treq.activity.name,
            self.treq.traveler,
        )

    def total_dollars(self):
        return "$%.2f" % self.total


class ActualExpense(models.Model):
    treq = models.ForeignKey("TravelRequest", on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=EXPENSE_TYPES)
    rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=5)
    fund = models.ForeignKey("Fund", on_delete=models.PROTECT)

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
