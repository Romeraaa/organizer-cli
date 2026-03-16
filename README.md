# OrganizerCLI

Una aplicación de terminal (TUI) minimalista para gestionar tareas y eventos de calendario.

## Características

- **Gestión de tareas**: Crear, completar y eliminar tareas
- **Calendario**: Crear eventos que se sincronizan con Google Calendar
- **Diseño**: Interfaz estilo terminal, minimalista y rápida

## Requisitos

- Python 3.12+
- Cuenta de Google Calendar

## Instalación

```bash
pip install textual google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

O simplemente:
```bash
pip install -r requirements.txt
```

## Configuración de Google Calendar

Para que funcione la integración con Google Calendar, necesitas configurar variables de entorno con tus credenciales de Google:

```bash
export GOOGLE_CLIENT_ID="tu-client-id"
export GOOGLE_CLIENT_SECRET="tu-client-secret"  
export GOOGLE_REFRESH_TOKEN="tu-refresh-token"
```

Para obtener estas credenciales:
1. Ve a Google Cloud Console
2. Crea un proyecto y habilita la API de Google Calendar
3. Crea credenciales OAuth2 (Client ID y Client Secret)
4. Obtén un refresh token usando las credenciales

## Uso

```bash
python organizer_cli.py
```

### Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `n` | Nueva tarea / evento |
| `d` | Eliminar elemento |
| `x` | Completar tarea |
| `1` | Ver tareas |
| `2` | Ver calendario |
| `q` | Salir |

## Estructura del proyecto

```
ProyectoIA/
├── organizer_cli.py   # Aplicación principal
├── requirements.txt   # Dependencias
├── SPEC.md           # Especificación
└── README.md         # Este archivo
```

## Notas

- Las tareas se guardan localmente en `~/.organizer_cli/tasks.json`
- Los eventos se crean directamente en tu Google Calendar
- La app funciona en cualquier terminal que soporte colores
