import pytest

from app.presentation.web.forms import RegistrationForm


def test_registration_form_has_expected_fields_and_no_school_selection():
    form = RegistrationForm()

    assert set(form.fields) == {"username", "password1", "password2", "school_name"}
    assert "school" not in form.fields
    assert "school_id" not in form.fields


@pytest.mark.django_db
def test_registration_form_valid_with_matching_passwords_and_school_name():
    form = RegistrationForm(
        data={
            "username": "ada",
            "password1": "xQ7!vB29zRk4",
            "password2": "xQ7!vB29zRk4",
            "school_name": "Riverside School",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["school_name"] == "Riverside School"


@pytest.mark.django_db
def test_registration_form_rejects_blank_school_name():
    form = RegistrationForm(
        data={
            "username": "ada",
            "password1": "xQ7!vB29zRk4",
            "password2": "xQ7!vB29zRk4",
            "school_name": "   ",
        }
    )

    assert not form.is_valid()
    assert "school_name" in form.errors


@pytest.mark.django_db
def test_registration_form_save_is_disabled():
    form = RegistrationForm(
        data={
            "username": "ada",
            "password1": "xQ7!vB29zRk4",
            "password2": "xQ7!vB29zRk4",
            "school_name": "Riverside School",
        }
    )
    assert form.is_valid(), form.errors

    try:
        form.save()
    except NotImplementedError:
        pass
    else:
        raise AssertionError("RegistrationForm.save() should be disabled")
