from django import forms

from app.infrastructure.database.models import Lesson, Room, StudentGroup, Subject, Teacher, TimeSlot


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


class TimeSlotForm(BaseStyledModelForm):
    class Meta:
        model = TimeSlot
        fields = ["day", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


class LessonForm(BaseStyledModelForm):
    class Meta:
        model = Lesson
        fields = ["teacher", "subject", "room", "student_group", "time_slot", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
