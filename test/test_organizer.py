import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from organizer_cli import Task, load_tasks, save_tasks, OrganizerCLI


class TestTask:
    def test_task_creation(self):
        task = Task("Test task", "Description")
        assert task.title == "Test task"
        assert task.description == "Description"
        assert task.completed is False
        assert task.id is not None
        assert task.created_at is not None

    def test_task_to_dict(self):
        task = Task("Test task", "Description", completed=True)
        task_dict = task.to_dict()
        
        assert task_dict["title"] == "Test task"
        assert task_dict["description"] == "Description"
        assert task_dict["completed"] is True
        assert "id" in task_dict
        assert "created_at" in task_dict

    def test_task_from_dict(self):
        data = {
            "id": "test-id-123",
            "title": "Test task",
            "description": "Test description",
            "completed": True,
            "created_at": "2024-01-01T00:00:00"
        }
        
        task = Task.from_dict(data)
        
        assert task.id == "test-id-123"
        assert task.title == "Test task"
        assert task.description == "Test description"
        assert task.completed is True

    def test_task_from_dict_defaults(self):
        data = {
            "id": "test-id-123",
            "title": "Test task"
        }
        
        task = Task.from_dict(data)
        
        assert task.description == ""
        assert task.completed is False


class TestLoadSaveTasks:
    def test_save_and_load_tasks(self, tmp_path):
        test_file = tmp_path / "tasks.json"
        
        original_data_file = Task.__module__.split('.')[0] + '.DATA_FILE'
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = test_file
        
        try:
            tasks = [
                Task("Task 1", "Description 1"),
                Task("Task 2", "Description 2", completed=True)
            ]
            
            save_tasks(tasks)
            loaded_tasks = load_tasks()
            
            assert len(loaded_tasks) == 2
            assert loaded_tasks[0].title == "Task 1"
            assert loaded_tasks[1].completed is True
        finally:
            organizer_cli.DATA_FILE = original_path

    def test_load_empty_file(self, tmp_path):
        test_file = tmp_path / "tasks.json"
        test_file.write_text("[]")
        
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = test_file
        
        try:
            tasks = load_tasks()
            assert tasks == []
        finally:
            organizer_cli.DATA_FILE = original_path

    def test_load_nonexistent_file(self, tmp_path):
        test_file = tmp_path / "nonexistent.json"
        
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = test_file
        
        try:
            tasks = load_tasks()
            assert tasks == []
        finally:
            organizer_cli.DATA_FILE = original_path


class TestOrganizerCLI:
    def test_organizer_init(self):
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = Path(tempfile.gettempdir()) / "test_tasks.json"
        
        try:
            app = OrganizerCLI()
            assert app.tasks == []
            assert app.view == "tasks"
            assert app.selected == 0
        finally:
            organizer_cli.DATA_FILE = original_path

    def test_has_google_creds_no_env(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_REFRESH_TOKEN", raising=False)
        
        app = OrganizerCLI()
        assert app.has_google_creds() is False

    def test_has_google_creds_with_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
        monkeypatch.setenv("GOOGLE_REFRESH_TOKEN", "test-refresh-token")
        
        app = OrganizerCLI()
        assert app.has_google_creds() is True

    def test_has_google_creds_partial_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_REFRESH_TOKEN", raising=False)
        
        app = OrganizerCLI()
        assert app.has_google_creds() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
