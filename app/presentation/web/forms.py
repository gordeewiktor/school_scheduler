from django import forms

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
    class Meta:
        model = Lesson
        fields = [
            "teacher",
            "subject",
            "room",
            "student_group",
            "day",
            "start_period",
            "duration",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def clean_duration(self) -> int:
        duration = self.cleaned_data["duration"]
        if duration < 1:
            raise forms.ValidationError("Duration must be at least 1.")
        return duration
