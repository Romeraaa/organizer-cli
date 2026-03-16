import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from organizer_cli import Task, load_tasks, save_tasks


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


class TestOrganizerApp:
    def test_organizer_init(self, tmp_path):
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = tmp_path / "tasks.json"
        
        try:
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            assert app.tasks == []
            assert app.current_view == "tasks"
            assert app.selected_index == 0
        finally:
            organizer_cli.DATA_FILE = original_path

    def test_has_google_creds_no_env(self):
        with patch.dict(os.environ, {}, clear=True):
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            assert app.has_google_creds() is False

    def test_has_google_creds_with_env(self):
        env_vars = {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
            "GOOGLE_REFRESH_TOKEN": "test-refresh-token"
        }
        with patch.dict(os.environ, env_vars):
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            assert app.has_google_creds() is True

    def test_has_google_creds_partial_env(self):
        env_vars = {
            "GOOGLE_CLIENT_ID": "test-client-id",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            assert app.has_google_creds() is False

    def test_add_task(self, tmp_path):
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = tmp_path / "tasks.json"
        
        try:
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            app.add_task("New Task", "Description")
            
            assert len(app.tasks) == 1
            assert app.tasks[0].title == "New Task"
            assert app.tasks[0].description == "Description"
        finally:
            organizer_cli.DATA_FILE = original_path

    def test_toggle_task(self, tmp_path):
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = tmp_path / "tasks.json"
        
        try:
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            app.add_task("Task to toggle")
            
            assert app.tasks[0].completed is False
            
            app.selected_index = 0
            app.action_toggle_task()
            
            assert app.tasks[0].completed is True
            
            app.action_toggle_task()
            
            assert app.tasks[0].completed is False
        finally:
            organizer_cli.DATA_FILE = original_path

    def test_delete_task(self, tmp_path):
        import organizer_cli
        original_path = organizer_cli.DATA_FILE
        organizer_cli.DATA_FILE = tmp_path / "tasks.json"
        
        try:
            from organizer_cli import OrganizerApp
            app = OrganizerApp()
            app.add_task("Task 1")
            app.add_task("Task 2")
            app.add_task("Task 3")
            
            assert len(app.tasks) == 3
            
            app.selected_index = 1
            app.action_delete_task()
            
            assert len(app.tasks) == 2
            assert app.tasks[0].title == "Task 1"
            assert app.tasks[1].title == "Task 3"
        finally:
            organizer_cli.DATA_FILE = original_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
