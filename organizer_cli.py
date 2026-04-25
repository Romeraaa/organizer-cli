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
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, OptionList
from textual.screen import ModalScreen
from textual.binding import Binding

APP_VERSION = "1.2.0"
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

#new-task-form, #new-event-form {
    height: auto;
    padding: 1 2;
    background: #161b22;
    border: solid #58a6ff;
}

.muted {
    color: #6e7681;
}

.error {
    color: #f85149;
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
    width: 100%;
    height: 100%;
}

#exit-title {
    text-align: center;
    color: #58a6ff;
    text-style: bold;
}

#exit-sep, #exit-sep2 {
    color: #30363d;
}

#exit-hint {
    text-align: center;
    color: #6e7681;
}

#exit-options-container {
    height: auto;
    align: center middle;
}

OptionList {
    background: #161b22;
    border: solid #30363d;
}

OptionList > .option-list--option {
    color: #c9d1d9;
}

OptionList > .option-list--option-highlighted {
    background: #388bfd;
    color: #ffffff;
}
"""


class TaskStorageError(Exception):
    """Raised when local task storage cannot be read or written."""


class CalendarError(Exception):
    """Raised when Google Calendar cannot be reached or updated."""


class Task:
    def __init__(self, title, description="", completed=False):
        now = datetime.datetime.now().isoformat()
        self.id = now
        self.title = title
        self.description = description
        self.completed = completed
        self.created_at = now

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
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise TaskStorageError("El archivo de tareas no contiene una lista.")
        return [Task.from_dict(t) for t in data]
    except TaskStorageError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise TaskStorageError(f"No se pudieron cargar las tareas: {exc}") from exc


def save_tasks(tasks):
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = DATA_FILE.with_suffix(f"{DATA_FILE.suffix}.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=2, ensure_ascii=False)
        temp_file.replace(DATA_FILE)
    except OSError as exc:
        raise TaskStorageError(f"No se pudieron guardar las tareas: {exc}") from exc


def parse_event_datetime(value: str) -> datetime.datetime:
    """Parse a local event datetime from CLI-friendly input."""
    cleaned = value.strip()
    normalized = cleaned.replace("T", " ")

    if not normalized or " " not in normalized:
        raise ValueError("Usa el formato AAAA-MM-DD HH:MM.")

    try:
        parsed = datetime.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("Usa el formato AAAA-MM-DD HH:MM.") from exc

    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


class ExitMenu(ModalScreen):
    """Confirmation menu to exit the app, styled like btop."""

    def compose(self) -> ComposeResult:
        with Vertical(id="exit-menu"):
            yield Static("┌──────────────────────────────────────────────┐", id="exit-border-top")
            yield Static("│              ORGANIZER CLI                 │", id="exit-title")
            yield Static("├──────────────────────────────────────────────┤", id="exit-sep")
            with Vertical(id="exit-options-container"):
                yield OptionList(
                    "           Sí, salir de la aplicación            ",
                    "           No, volver al programa                 ",
                    id="exit-option-list"
                )
            yield Static("├──────────────────────────────────────────────┤", id="exit-sep2")
            yield Static("│   [↑↓] navegar  [Enter] confirmar  [Esc] cancelar   │", id="exit-hint")
            yield Static("└──────────────────────────────────────────────┘", id="exit-border-bottom")

    def on_mount(self) -> None:
        self.query_one("#exit-option-list", OptionList).focus()

    def on_option_list_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_index == 0:
            self.app.exit()
        else:
            self.app.pop_screen()

    def on_key(self, event) -> None:
        if event.key == "enter":
            selected = self.query_one("#exit-option-list", OptionList).index
            if selected == 0:
                self.app.exit()
            else:
                self.app.pop_screen()
        elif event.key == "escape":
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


class NewEventModal(ModalScreen):
    """Modal to create a Google Calendar event."""

    def compose(self) -> ComposeResult:
        now = datetime.datetime.now().astimezone()
        start = (now + datetime.timedelta(hours=1)).replace(second=0, microsecond=0)
        end = start + datetime.timedelta(hours=1)

        with Container(id="new-event-form"):
            yield Static("[b]Nuevo Evento[/b]", id="event-form-title")
            yield Input(placeholder="Título del evento...", id="event-title")
            yield Input(
                value=start.strftime("%Y-%m-%d %H:%M"),
                placeholder="Inicio: AAAA-MM-DD HH:MM",
                id="event-start",
            )
            yield Input(
                value=end.strftime("%Y-%m-%d %H:%M"),
                placeholder="Fin: AAAA-MM-DD HH:MM",
                id="event-end",
            )
            yield Input(placeholder="Descripción (opcional)", id="event-desc")
            yield Static("", id="event-error", classes="error")
            with Horizontal():
                yield Button("Guardar", variant="primary", id="save-event-btn")
                yield Button("Cancelar", variant="default", id="cancel-event-btn")

    def on_mount(self) -> None:
        self.query_one("#event-title").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-event-btn":
            self.submit_event()
        else:
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()
        elif event.key == "enter":
            self.submit_event()

    def submit_event(self) -> None:
        title = self.query_one("#event-title", Input).value.strip()
        start = self.query_one("#event-start", Input).value.strip()
        end = self.query_one("#event-end", Input).value.strip()
        desc = self.query_one("#event-desc", Input).value.strip()

        try:
            self.app.add_calendar_event(title, start, end, desc)
        except (ValueError, CalendarError) as exc:
            self.query_one("#event-error", Static).update(str(exc))
            return

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
        self.tasks_error = None
        try:
            self.tasks = load_tasks()
        except TaskStorageError as exc:
            self.tasks = []
            self.tasks_error = str(exc)
        self.current_view = "tasks"
        self.selected_index = 0
        self.calendar_events = []
        self.calendar_error = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="main-container"):
            with Vertical(id="header-bar"):
                yield Static(" ═════════════════════════════════════════════════ ", id="title-bar")
                yield Static(f"│            ORGANIZER CLI v{APP_VERSION}            │", id="app-title")
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

    def ui_ready(self) -> bool:
        return bool(getattr(self, "_screen_stack", []))

    def refresh_current_view(self) -> None:
        if not self.ui_ready():
            return
        if self.current_view == "calendar":
            self.refresh_calendar()
        else:
            self.refresh_tasks()

    def save_tasks_or_report(self) -> None:
        try:
            save_tasks(self.tasks)
            self.tasks_error = None
        except TaskStorageError as exc:
            self.tasks_error = str(exc)

    def action_show_tasks(self) -> None:
        self.current_view = "tasks"
        self.selected_index = 0
        if self.ui_ready():
            self.query_one("#nav-tasks", Button).variant = "primary"
            self.query_one("#nav-calendar", Button).variant = "default"
            self.query_one("#content").border_title = "TAREAS"
            self.refresh_tasks()

    def action_show_calendar(self) -> None:
        self.current_view = "calendar"
        self.selected_index = 0
        if self.ui_ready():
            self.query_one("#nav-tasks", Button).variant = "default"
            self.query_one("#nav-calendar", Button).variant = "primary"
            self.query_one("#content").border_title = "GOOGLE CALENDAR"
            self.refresh_calendar()

    def action_new_task(self) -> None:
        if self.current_view == "calendar":
            self.push_screen(NewEventModal())
        else:
            self.push_screen(NewTaskModal())

    def action_delete_task(self) -> None:
        if self.current_view == "tasks" and 0 <= self.selected_index < len(self.tasks):
            self.tasks.pop(self.selected_index)
            self.selected_index = max(0, min(self.selected_index, len(self.tasks) - 1))
            self.save_tasks_or_report()
            self.refresh_current_view()

    def action_toggle_task(self) -> None:
        if self.current_view == "tasks" and 0 <= self.selected_index < len(self.tasks):
            self.tasks[self.selected_index].completed = not self.tasks[self.selected_index].completed
            self.save_tasks_or_report()
            self.refresh_current_view()

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
        if not self.ui_ready():
            return
        list_view = self.query_one("#task-list", ListView)
        if 0 <= self.selected_index < len(list_view.children):
            list_view.index = self.selected_index

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.selected_index = event.list_view.index

    def add_task(self, title: str, description: str = "") -> None:
        self.tasks.append(Task(title, description))
        self.save_tasks_or_report()
        self.refresh_current_view()

    def refresh_tasks(self) -> None:
        list_view = self.query_one("#task-list", ListView)
        list_view.clear()

        if self.tasks_error:
            list_view.append(ListItem(Static(f"  ⚠ {self.tasks_error}", classes="error")))

        if not self.tasks:
            list_view.append(ListItem(Static("  No hay tareas. Pulsa [n] para crear una.", classes="muted")))
            return

        for i, task in enumerate(self.tasks):
            marker = "✓" if task.completed else "○"
            classes = "task-completed" if task.completed else "task-pending"
            display_text = f"  {marker}  {task.title}"
            if task.description:
                display_text += f"\n      {task.description}"

            item = ListItem(Static(display_text, classes=classes))
            list_view.append(item)

        if 0 <= self.selected_index < len(list_view.children):
            list_view.index = self.selected_index

    def refresh_calendar(self) -> None:
        list_view = self.query_one("#task-list", ListView)
        list_view.clear()
        self.calendar_events = []

        if not self.has_google_creds():
            list_view.append(ListItem(Static("  ⚠ Configura credenciales de Google para usar el calendario.", classes="muted")))
            list_view.append(ListItem(Static("  Ver README.md para instrucciones.", classes="muted")))
            return

        try:
            events = self.get_calendar_events()
            self.calendar_error = None
        except Exception as exc:
            self.calendar_error = str(exc)
            list_view.append(ListItem(Static(f"  ⚠ Error de calendario: {exc}", classes="error")))
            return

        if not events:
            list_view.append(ListItem(Static("  No hay eventos próximos. Pulsa [n] para crear uno.", classes="muted")))
            return

        for event in events:
            display_text = f"  📅 {event['summary']}\n      {event['start']} → {event['end']}"
            if event.get('description'):
                description = event["description"]
                suffix = "..." if len(description) > 50 else ""
                display_text += f"\n      {description[:50]}{suffix}"
            list_view.append(ListItem(Static(display_text, classes="task-pending")))

        self.calendar_events = events

    def has_google_creds(self):
        return bool(os.environ.get("GOOGLE_CLIENT_ID") and
                   os.environ.get("GOOGLE_CLIENT_SECRET") and
                   os.environ.get("GOOGLE_REFRESH_TOKEN"))

    def build_calendar_service(self):
        if not self.has_google_creds():
            raise CalendarError("Faltan GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET o GOOGLE_REFRESH_TOKEN.")

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise CalendarError("Instala las dependencias de Google Calendar con pip install -r requirements.txt.") from exc

        try:
            creds = Credentials.from_authorized_user_info(
                info={
                    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                    "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": os.environ.get("GOOGLE_REFRESH_TOKEN"),
                },
                scopes=["https://www.googleapis.com/auth/calendar.events"],
            )
            return build("calendar", "v3", credentials=creds, cache_discovery=False)
        except Exception as exc:
            raise CalendarError(str(exc)) from exc

    def get_calendar_events(self):
        service = self.build_calendar_service()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        try:
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        except Exception as exc:
            raise CalendarError(str(exc)) from exc

        events = []
        for event in events_result.get("items", []):
            start = event.get("start", {})
            end = event.get("end", {})

            start_str = start.get("dateTime", start.get("date", ""))
            end_str = end.get("dateTime", end.get("date", ""))

            if "T" in start_str and end_str:
                start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_dt = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                start_fmt = start_dt.strftime("%d/%m %H:%M")
                end_fmt = end_dt.strftime("%H:%M")
            else:
                start_fmt = start_str
                end_fmt = end_str

            events.append({
                "id": event.get("id", ""),
                "summary": event.get("summary", "Sin título"),
                "start": start_fmt,
                "end": end_fmt,
                "description": event.get("description", ""),
                "html_link": event.get("htmlLink", ""),
            })

        return events

    def add_calendar_event(self, title: str, start: str, end: str, description: str = ""):
        start_dt = parse_event_datetime(start)
        end_dt = parse_event_datetime(end)
        return self.create_calendar_event(title, start_dt, end_dt, description)

    def create_calendar_event(
        self,
        title: str,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        description: str = "",
    ):
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("El título del evento es obligatorio.")
        if end_dt <= start_dt:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio.")

        service = self.build_calendar_service()
        body = {
            "summary": clean_title,
            "description": description.strip(),
            "start": {"dateTime": start_dt.isoformat()},
            "end": {"dateTime": end_dt.isoformat()},
        }

        try:
            event = service.events().insert(calendarId="primary", body=body).execute()
            self.calendar_error = None
            self.refresh_current_view()
            return event
        except Exception as exc:
            raise CalendarError(str(exc)) from exc

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "nav-tasks":
            self.action_show_tasks()
        elif event.button.id == "nav-calendar":
            self.action_show_calendar()


if __name__ == "__main__":
    app = OrganizerApp()
    app.run()
