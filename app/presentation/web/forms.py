from django import forms

from app.domain.models import Day
from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)


class BaseStyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css_class)


class TeacherForm(BaseStyledModelForm):
    class Meta:
        model = Teacher
        fields = ["name", "email"]


class RoomForm(BaseStyledModelForm):
    class Meta:
        model = Room
        fields = ["name", "capacity"]


class SubjectForm(BaseStyledModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code"]


class StudentGroupForm(BaseStyledModelForm):
    class Meta:
        model = StudentGroup
        fields = ["name", "size"]


class AcademicYearForm(BaseStyledModelForm):
    class Meta:
        model = AcademicYear
        fields = ["name", "default_period_duration"]


class PeriodForm(BaseStyledModelForm):
    class Meta:
        model = Period
        fields = ["academic_year", "name", "order", "start_time", "end_time", "kind"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean_order(self) -> int:
        order = self.cleaned_data["order"]
        if order < 1:
            raise forms.ValidationError("Order must be at least 1.")
        return order


class LessonForm(BaseStyledModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["planned_substitute"].label = "Substitution Teacher"
        self.fields["planned_substitute"].empty_label = "No substitution teacher"

    class Meta:
        model = Lesson
        fields = [
            "teacher",
            "planned_substitute",
            "subject",
            "room",
            "student_group",
            "day",
            "start_period",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class TeacherSubstitutionForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all())
    day = forms.ChoiceField(
        choices=[(day.value, day.name.replace("_", " ").title()) for day in Day]
    )
    period = forms.ModelChoiceField(queryset=Period.objects.all())

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["academic_year"].queryset = AcademicYear.objects.all()
        self.fields["period"].queryset = Period.objects.select_related(
            "academic_year"
        ).all()

        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-select" if isinstance(field.widget, forms.Select) else "form-control",
            )

    def clean_period(self) -> Period:
        period = self.cleaned_data["period"]
        academic_year = self.cleaned_data["academic_year"]
        if period.academic_year_id != academic_year.pk:
            raise forms.ValidationError("Choose a period from the selected academic year.")
        return period
