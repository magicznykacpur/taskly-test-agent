from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.features.todos.models import TodoRecord
from app.features.todos.repository import TodoRepository
from app.features.todos.schemas import TodoCreate, TodoUpdate


def test_list_maps_models_and_orders_tasks_newest_first(model_factory, todo_values, todo):
    session = Mock(spec=Session)
    session.scalars.return_value = [model_factory(todo_values)]
    assert TodoRepository(session).list() == [todo]
    statement = session.scalars.call_args.args[0]
    expected = select(TodoRecord).order_by(TodoRecord.created_at.desc(), TodoRecord.id.desc())
    assert statement.compare(expected)
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "ORDER BY todos.created_at DESC, todos.id DESC" in compiled


def test_get_returns_none_for_missing_task():
    session = Mock(spec=Session)
    session.get.return_value = None
    assert TodoRepository(session).get(404) is None
    session.get.assert_called_once_with(TodoRecord, 404)


def test_get_maps_existing_record(model_factory, todo_values, todo):
    session = Mock(spec=Session)
    session.get.return_value = model_factory(todo_values)
    assert TodoRepository(session).get(7) == todo


@patch("app.features.todos.repository.datetime")
def test_create_persists_record_with_fixed_timestamps(datetime_mock, todo_values):
    now = datetime(2026, 10, 2, 8, tzinfo=timezone.utc)
    datetime_mock.now.return_value = now
    session = Mock(spec=Session)
    session.refresh.side_effect = lambda record: setattr(record, "id", 7)
    created = TodoRepository(session).create(TodoCreate(title="Plan", priority="high"))
    record = session.add.call_args.args[0]
    assert (record.title, record.priority) == ("Plan", "high")
    assert record.created_at == record.updated_at == now
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(record)
    assert created.title == "Plan"


def test_update_returns_none_for_missing_task():
    session = Mock(spec=Session)
    session.get.return_value = None
    assert TodoRepository(session).update(404, TodoUpdate(title="x")) is None
    session.commit.assert_not_called()


@patch("app.features.todos.repository.datetime")
def test_update_changes_only_provided_fields(datetime_mock, model_factory, todo_values):
    now = datetime(2026, 10, 3, 9, tzinfo=timezone.utc)
    datetime_mock.now.return_value = now
    record = model_factory(todo_values)
    session = Mock(spec=Session)
    session.get.return_value = record
    updated = TodoRepository(session).update(7, TodoUpdate(completed=True))
    assert record.completed is True
    assert record.title == "Plan the sprint"
    assert record.updated_at == now
    assert record.created_at == todo_values["created_at"]
    assert updated.completed is True
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(record)


def test_update_can_clear_due_date(model_factory, todo_values):
    record = model_factory({**todo_values, "due_date": date(2026, 11, 1)})
    session = Mock(spec=Session)
    session.get.return_value = record
    TodoRepository(session).update(7, TodoUpdate(due_date=None))
    assert record.due_date is None


def test_delete_removes_existing_record(model_factory, todo_values):
    record = model_factory(todo_values)
    session = Mock(spec=Session)
    session.get.return_value = record
    assert TodoRepository(session).delete(7) is True
    session.delete.assert_called_once_with(record)
    session.commit.assert_called_once_with()


def test_delete_returns_false_for_missing_task():
    session = Mock(spec=Session)
    session.get.return_value = None
    assert TodoRepository(session).delete(404) is False
    session.delete.assert_not_called()
    session.commit.assert_not_called()
