import pytest
from pydantic import ValidationError

from app.features.todos.schemas import Priority, TodoCreate, TodoUpdate


def test_create_applies_defaults():
    todo = TodoCreate(title="Write")
    assert todo.description == ""
    assert todo.priority is Priority.medium
    assert todo.due_date is None
    assert todo.completed is False


def test_create_strips_whitespace_from_title():
    assert TodoCreate(title="  Write  ").title == "Write"


@pytest.mark.parametrize("title", ["", "   ", "x" * 121])
def test_create_rejects_invalid_title(title):
    with pytest.raises(ValidationError):
        TodoCreate(title=title)


def test_create_accepts_title_of_120_characters():
    assert len(TodoCreate(title="x" * 120).title) == 120


def test_create_rejects_description_over_2000_characters():
    with pytest.raises(ValidationError):
        TodoCreate(title="a", description="x" * 2001)


def test_create_rejects_unknown_priority():
    with pytest.raises(ValidationError):
        TodoCreate(title="a", priority="urgent")


def test_create_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="Extra inputs"):
        TodoCreate(title="a", owner="me")


@pytest.mark.parametrize("value", ["true", 1])
def test_completed_is_strict_boolean(value):
    with pytest.raises(ValidationError):
        TodoCreate(title="a", completed=value)


def test_update_rejects_empty_patch():
    with pytest.raises(ValidationError, match="at least one field"):
        TodoUpdate()


@pytest.mark.parametrize("field", ["title", "description", "priority", "completed"])
def test_update_rejects_explicit_null_for_required_fields(field):
    with pytest.raises(ValidationError, match=f"Field {field} cannot be null"):
        TodoUpdate(**{field: None})


def test_update_allows_null_due_date():
    patch = TodoUpdate(due_date=None)
    assert patch.model_fields_set == {"due_date"}
    assert patch.due_date is None


def test_update_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="Extra inputs"):
        TodoUpdate(title="a", id=3)
