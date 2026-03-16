"""
OrganizerCLI - Terminal-based task manager
A simple, minimal TUI for tasks and calendar events
"""

import os
import sys
import json
import datetime
from pathlib import Path

DATA_FILE = Path.home() / ".organizer_cli" / "tasks.json"

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

class OrganizerCLI:
    def __init__(self):
        self.tasks = load_tasks()
        self.view = "tasks"
        self.selected = 0
        
    def clear(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def render(self):
        self.clear()
        
        print("\033[1;36m" + "═" * 50 + "\033[0m")
        print("\033[1;36m║\033[0m" + " 📋 ORGANIZER CLI v1.0 ".center(48) + "\033[1;36m║\033[0m")
        print("\033[1;36m" + "═" * 50 + "\033[0m")
        
        print(f"\n [\033[1;34m1\033[0m] Tareas  [\033[1;34m2\033[0m] Calendario  [\033[1;34mq\033[0m] Salir")
        print("\033[1;36m" + "─" * 50 + "\033[0m")
        
        if self.view == "tasks":
            self.render_tasks()
        elif self.view == "calendar":
            self.render_calendar()
        
        print("\033[1;36m" + "─" * 50 + "\033[0m")
        print("\033[1;33mAtajos:\033[0m  [n] nueva tarea  [d] eliminar  [x] completar  [↑↓] mover")
    
    def render_tasks(self):
        if not self.tasks:
            print("\n  \033[90mNo hay tareas. Pulsa [n] para crear una.\033[0m\n")
            return
        
        print("\n  \033[1mTAREAS:\033[0m\n")
        for i, task in enumerate(self.tasks):
            marker = "✓" if task.completed else "○"
            color = "\033[32m" if task.completed else "\033[37m"
            sel = "► " if i == self.selected else "  "
            print(f"  {sel}{color}{marker}\033[0m {task.title}")
            if task.description:
                print(f"      \033[90m{task.description}\033[0m")
        print()
    
    def render_calendar(self):
        print("\n  \033[1mCALENDARIO (Google Calendar):\033[0m\n")
        
        if not self.has_google_creds():
            print("  \033[90mConfigura credenciales de Google para usar el calendario.\033[0m")
            print("  \033[90mVer README.md para instrucciones.\033[0m\n")
            return
        
        events = self.get_calendar_events()
        if not events:
            print("  \033[90mNo hay eventos próximos. Pulsa [n] para crear uno.\033[0m\n")
            return
        
        for event in events:
            print(f"  ▸ \033[36m{event['summary']}\033[0m")
            print(f"    📅 {event['start']} → {event['end']}")
            if event.get('description'):
                print(f"    \033[90m{event['description'][:50]}...\033[0m")
            print()
    
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
    
    def create_calendar_event(self, title, date, start, end, description):
        if not self.has_google_creds():
            return False
        
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
            
            start_dt = f"{date}T{start}:00"
            end_dt = f"{date}T{end}:00"
            
            event = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start_dt, "timeZone": "Europe/Madrid"},
                "end": {"dateTime": end_dt, "timeZone": "Europe/Madrid"},
            }
            
            service.events().insert(calendarId="primary", body=event).execute()
            return True
        except Exception as e:
            return False
    
    def run(self):
        while True:
            self.render()
            try:
                key = input("\n\033[1;34m>\033[0m ").strip()
                
                if key == "1":
                    self.view = "tasks"
                    self.selected = 0
                elif key == "2":
                    self.view = "calendar"
                    self.selected = 0
                elif key == "q":
                    print("\n\033[32m¡Hasta luego! 👋\033[0m\n")
                    break
                elif key == "n":
                    self.add_new()
                elif key == "d":
                    self.delete_selected()
                elif key == "x":
                    self.toggle_selected()
                elif key == "w" or key == "↑":
                    self.selected = max(0, self.selected - 1)
                elif key == "s" or key == "↓":
                    max_items = len(self.tasks) if self.view == "tasks" else 10
                    self.selected = min(max(0, max_items - 1), self.selected + 1)
            except (KeyboardInterrupt, EOFError):
                print("\n\033[32m¡Hasta luego! 👋\033[0m\n")
                break
    
    def add_new(self):
        if self.view == "tasks":
            print("\n\033[1;33mNueva tarea:\033[0m")
            title = input("  Título: ").strip()
            if title:
                desc = input("  Descripción (opcional): ").strip()
                self.tasks.append(Task(title, desc))
                save_tasks(self.tasks)
        else:
            if not self.has_google_creds():
                print("\n\033[31mError: Configura las credenciales de Google primero.\033[0m")
                return
            
            print("\n\033[1;33mNuevo evento:\033[0m")
            title = input("  Título: ").strip()
            date = input("  Fecha (YYYY-MM-DD): ").strip()
            start = input("  Hora inicio (HH:MM): ").strip()
            end = input("  Hora fin (HH:MM): ").strip()
            desc = input("  Descripción (opcional): ").strip()
            
            if title and date and start and end:
                if self.create_calendar_event(title, date, start, end, desc):
                    print("\n\033[32m✓ Evento creado en Google Calendar\033[0m")
                else:
                    print("\n\033[31m✗ Error al crear el evento\033[0m")
    
    def delete_selected(self):
        if self.view == "tasks" and self.tasks and 0 <= self.selected < len(self.tasks):
            self.tasks.pop(self.selected)
            save_tasks(self.tasks)
            self.selected = max(0, self.selected - 1)
    
    def toggle_selected(self):
        if self.view == "tasks" and self.tasks and 0 <= self.selected < len(self.tasks):
            self.tasks[self.selected].completed = not self.tasks[self.selected].completed
            save_tasks(self.tasks)

if __name__ == "__main__":
    app = OrganizerCLI()
    app.run()
