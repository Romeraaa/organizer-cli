"""
OrganizerCLI - Terminal-based task manager
A simple, minimal TUI for tasks and calendar events
"""

import os
import json
import datetime
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import work

DATA_FILE = Path.home() / ".organizer_cli" / "tasks.json"

SCREEN_STYLES = """
Screen {
    background: #0d1117;
}

#main-container {
    height: 100%;
    padding: 1 2;
}

#header-bar {
    height: 3;
    background: #58a6ff;
    color: #c9d1d9;
    text-align: center;
}

#nav-bar {
    height: 3;
    background: #161b22;
    align: center middle;
}

#content {
    height: auto;
    border: solid #30363d;
    padding: 1;
}

#footer-bar {
    height: 3;
    background: #161b22;
    align: center middle;
}

ListView {
    background: #0d1117;
}

ListItem {
    height: auto;
    padding: 0 1;
}

ListItem:hover {
    background: #388bfd;
    color: #ffffff;
}

.task-completed {
    text-style: strike;
    color: #6e7681;
}

.task-pending {
    color: #c9d1d9;
}

#new-task-form {
    height: auto;
    padding: 1 2;
    background: #161b22;
    border: solid #58a6ff;
}

Button {
    margin: 0 1;
}

Button:hover {
    background: #388bfd;
}

#exit-menu {
    align: center middle;
    background: #0d1117;
    border: solid #d29922;
    width: 40;
    height: auto;
    padding: 1 2;
}
"""

class Task:
    def __init__(self, title, description="", completed=False):
        self.id = datetime.datetime.now().isoformat()
        self.title = title
        self.description = description
        self.completed = completed
        self.created_at = datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        task = cls(data["title"], data.get("description", ""), data.get("completed", False))
        task.id = data["id"]
        task.created_at = data.get("created_at", data["id"])
        return task


def load_tasks():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
            return [Task.from_dict(t) for t in data]
    except:
        return []


def save_tasks(tasks):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2)


class ExitMenu(ModalScreen):
    """Confirmation menu to exit the app, styled like btop."""
    
    def compose(self) -> ComposeResult:
        with Vertical(id="exit-menu"):
            yield Static("┌──────────────────────────┐", id="exit-border-top")
            yield Static("│     [b]Salir?[/b]          │", id="exit-title")
            yield Static("│                          │")
            yield Static("│  [green]Y[/green] / [red]N[/red]  ", id="exit-options")
            yield Static("└──────────────────────────┘", id="exit-border-bottom")
    
    def on_mount(self) -> None:
        self.query_one("#exit-title").focus()
    
    def on_key(self, event) -> None:
        if event.key == "y":
            self.app.exit()
        elif event.key == "n" or event.key == "escape":
            self.app.pop_screen()


class NewTaskModal(ModalScreen):
    """Modal to create a new task."""
    
    def compose(self) -> ComposeResult:
        with Container(id="new-task-form"):
            yield Static("[b]Nueva Tarea[/b]", id="form-title")
            yield Input(placeholder="Título de la tarea...", id="task-title")
            yield Input(placeholder="Descripción (opcional)", id="task-desc")
            with Horizontal():
                yield Button("Guardar", variant="primary", id="save-btn")
                yield Button("Cancelar", variant="default", id="cancel-btn")
    
    def on_mount(self) -> None:
        self.query_one("#task-title").focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            title = self.query_one("#task-title").value.strip()
            desc = self.query_one("#task-desc").value.strip()
            if title:
                self.app.add_task(title, desc)
                self.dismiss()
        else:
            self.dismiss()
    
    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()
        elif event.key == "enter":
            title = self.query_one("#task-title").value.strip()
            desc = self.query_one("#task-desc").value.strip()
            if title:
                self.app.add_task(title, desc)
                self.dismiss()


class OrganizerApp(App):
    """Fullscreen terminal task manager."""
    
    CSS = SCREEN_STYLES
    BINDINGS = [
        Binding("1", "show_tasks", "Tareas"),
        Binding("2", "show_calendar", "Calendario"),
        Binding("n", "new_task", "Nueva"),
        Binding("d", "delete_task", "Eliminar"),
        Binding("x", "toggle_task", "Completar"),
        Binding("q", "show_exit_menu", "Salir"),
        Binding("escape", "show_exit_menu", "Salir"),
        Binding("up", "cursor_up", "Arriba"),
        Binding("down", "cursor_down", "Abajo"),
    ]
    
    def __init__(self):
        super().__init__()
        self.tasks = load_tasks()
        self.current_view = "tasks"
        self.selected_index = 0
        self.calendar_events = []
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Vertical(id="header-bar"):
                yield Static(" ═════════════════════════════════════════════════ ", id="title-bar")
                yield Static(" │  📋  ORGANIZER CLI v2.0  │ ", id="app-title")
                yield Static(" ═════════════════════════════════════════════════ ", id="title-bar-bottom")
            
            with Horizontal(id="nav-bar"):
                yield Button("1. Tareas", variant="primary", id="nav-tasks")
                yield Button("2. Calendario", variant="default", id="nav-calendar")
            
            with Vertical(id="content"):
                yield ListView(id="task-list")
            
            with Horizontal(id="footer-bar"):
                yield Static("[n] Nueva  [d] Eliminar  [x] Completar  [↑↓] Mover  [q] Salir", id="footer-keys")
        
        yield Footer()
    
    def on_mount(self) -> None:
        self.refresh_tasks()
    
    def action_show_tasks(self) -> None:
        self.current_view = "tasks"
        self.query_one("#nav-tasks", Button).variant = "primary"
        self.query_one("#nav-calendar", Button).variant = "default"
        self.query_one("#content").border_title = "TAREAS"
        self.refresh_tasks()
    
    def action_show_calendar(self) -> None:
        self.current_view = "calendar"
        self.query_one("#nav-tasks", Button).variant = "default"
        self.query_one("#nav-calendar", Button).variant = "primary"
        self.query_one("#content").border_title = "GOOGLE CALENDAR"
        self.refresh_calendar()
    
    def action_new_task(self) -> None:
        self.push_screen(NewTaskModal())
    
    def action_delete_task(self) -> None:
        if self.current_view == "tasks" and 0 <= self.selected_index < len(self.tasks):
            self.tasks.pop(self.selected_index)
            save_tasks(self.tasks)
            self.refresh_tasks()
            self.selected_index = max(0, min(self.selected_index, len(self.tasks) - 1))
    
    def action_toggle_task(self) -> None:
        if self.current_view == "tasks" and 0 <= self.selected_index < len(self.tasks):
            self.tasks[self.selected_index].completed = not self.tasks[self.selected_index].completed
            save_tasks(self.tasks)
            self.refresh_tasks()
    
    def action_show_exit_menu(self) -> None:
        self.push_screen(ExitMenu())
    
    def action_cursor_up(self) -> None:
        max_items = len(self.tasks) if self.current_view == "tasks" else max(len(self.calendar_events), 1)
        if max_items > 0:
            self.selected_index = max(0, self.selected_index - 1)
            self.update_selection()
    
    def action_cursor_down(self) -> None:
        max_items = len(self.tasks) if self.current_view == "tasks" else max(len(self.calendar_events), 1)
        if max_items > 0:
            self.selected_index = min(max_items - 1, self.selected_index + 1)
            self.update_selection()
    
    def update_selection(self) -> None:
        list_view = self.query_one("#task-list", ListView)
        if 0 <= self.selected_index < len(list_view.children):
            list_view.index = self.selected_index
    
    def add_task(self, title: str, description: str = "") -> None:
        self.tasks.append(Task(title, description))
        save_tasks(self.tasks)
        self.refresh_tasks()
    
    def refresh_tasks(self) -> None:
        list_view = self.query_one("#task-list", ListView)
        list_view.clear()
        
        if not self.tasks:
            list_view.append(ListItem(Static("  No hay tareas. Pulsa [n] para crear una.", classes="muted")))
            return
        
        for i, task in enumerate(self.tasks):
            marker = "✓" if task.completed else "○"
            classes = "task-completed" if task.completed else "task-pending"
            display_text = f"  {marker}  {task.title}"
            if task.description:
                display_text += f"\n      {task.description}"
            
            item = ListItem(Static(display_text, classes=classes), id=f"task-{i}")
            list_view.append(item)
        
        if 0 <= self.selected_index < len(list_view.children):
            list_view.index = self.selected_index
    
    def refresh_calendar(self) -> None:
        list_view = self.query_one("#task-list", ListView)
        list_view.clear()
        
        if not self.has_google_creds():
            list_view.append(ListItem(Static("  ⚠ Configura credenciales de Google para usar el calendario.", classes="muted")))
            list_view.append(ListItem(Static("  Ver README.md para instrucciones.", classes="muted")))
            return
        
        events = self.get_calendar_events()
        if not events:
            list_view.append(ListItem(Static("  No hay eventos próximos. Pulsa [n] para crear uno.", classes="muted")))
            return
        
        for event in events:
            display_text = f"  📅 {event['summary']}\n      {event['start']} → {event['end']}"
            if event.get('description'):
                display_text += f"\n      {event['description'][:50]}..."
            list_view.append(ListItem(Static(display_text, classes="task-pending")))
        
        self.calendar_events = events
    
    def has_google_creds(self):
        return bool(os.environ.get("GOOGLE_CLIENT_ID") and 
                   os.environ.get("GOOGLE_CLIENT_SECRET") and 
                   os.environ.get("GOOGLE_REFRESH_TOKEN"))
    
    def get_calendar_events(self):
        if not self.has_google_creds():
            return []
        
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds = Credentials.from_authorized_user_info(
                info={
                    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                    "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": os.environ.get("GOOGLE_REFRESH_TOKEN")
                },
                scopes=["https://www.googleapis.com/auth/calendar.events"]
            )
            
            service = build("calendar", "v3", credentials=creds)
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = []
            for event in events_result.get("items", []):
                start = event.get("start", {})
                end = event.get("end", {})
                
                start_str = start.get("dateTime", start.get("date", ""))
                end_str = end.get("dateTime", end.get("date", ""))
                
                if "T" in start_str:
                    start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end_dt = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    start_fmt = start_dt.strftime("%d/%m %H:%M")
                    end_fmt = end_dt.strftime("%H:%M")
                else:
                    start_fmt = start_str
                    end_fmt = end_str
                
                events.append({
                    "summary": event.get("summary", "Sin título"),
                    "start": start_fmt,
                    "end": end_fmt,
                    "description": event.get("description", "")
                })
            
            return events
        except Exception as e:
            return []
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "nav-tasks":
            self.action_show_tasks()
        elif event.button.id == "nav-calendar":
            self.action_show_calendar()


if __name__ == "__main__":
    app = OrganizerApp()
    app.run()
