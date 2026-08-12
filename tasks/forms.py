from django import forms

from .models import Task, Status


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["name", "description", "deadline", "status", "priority"]
        widgets = {
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["deadline"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_status(self):
        status = self.cleaned_data.get("status")

        if self.instance.pk and self.instance.status == Status.DONE and status != Status.DONE:
            raise forms.ValidationError("Выполненную задачу нельзя вернуть в работу.")

        return status