# OrganizerCLI

OrganizerCLI es una aplicación TUI minimalista para gestionar tareas locales y eventos de Google Calendar desde la terminal.

Versión actual: **1.2.0**

## Funcionalidades

- Crear, completar y eliminar tareas.
- Guardar tareas localmente en `~/.organizer_cli/tasks.json`.
- Ver los próximos eventos de Google Calendar.
- Crear eventos en Google Calendar desde la vista de calendario.
- Navegar con teclado entre tareas y calendario.
- Mostrar errores de almacenamiento o calendario dentro de la interfaz.

## Requisitos

- Python 3.12+
- Terminal compatible con aplicaciones TUI.
- Cuenta de Google Calendar para usar la vista de calendario.

## Instalación

```bash
pip install -r requirements.txt
```

Para ejecutar los tests también instala las dependencias de test:

```bash
pip install -r test/requirements.txt
```

## Configuración de Google Calendar

La integración usa OAuth2 mediante variables de entorno:

```bash
export GOOGLE_CLIENT_ID="tu-client-id"
export GOOGLE_CLIENT_SECRET="tu-client-secret"
export GOOGLE_REFRESH_TOKEN="tu-refresh-token"
```

Para obtener estas credenciales:

1. Crea un proyecto en Google Cloud Console.
2. Habilita la API de Google Calendar.
3. Crea credenciales OAuth2.
4. Genera un refresh token con permisos para Google Calendar.

La aplicación usa el calendario `primary` y el scope `https://www.googleapis.com/auth/calendar.events`.

## Uso

```bash
python organizer_cli.py
```

Atajos principales:

| Tecla | Acción |
|-------|--------|
| `1` | Ver tareas |
| `2` | Ver calendario |
| `n` | Nueva tarea o nuevo evento, según la vista activa |
| `d` | Eliminar tarea seleccionada |
| `x` | Completar o reabrir tarea seleccionada |
| `↑` / `↓` | Mover selección |
| `q` / `Esc` | Mostrar menú de salida |

En la vista de calendario, `n` abre un formulario de evento con formato de fecha `AAAA-MM-DD HH:MM`.

## Arquitectura

El proyecto es deliberadamente pequeño:

```text
ProyectoIA/
├── organizer_cli.py       # App Textual, modelo de tarea, persistencia y calendario
├── requirements.txt       # Dependencias de ejecución
├── test/
│   ├── requirements.txt   # Dependencias de test
│   └── test_organizer.py  # Tests unitarios
├── SPEC.md                # Especificación funcional original
└── README.md              # Documentación principal
```

La lógica de tareas está desacoplada del montaje de Textual: los métodos de dominio pueden probarse sin abrir la interfaz. Los refrescos de UI se ejecutan solo cuando la app tiene una pantalla montada.

## Persistencia

Las tareas se guardan como JSON en:

```text
~/.organizer_cli/tasks.json
```

La escritura se realiza mediante un archivo temporal y reemplazo final para reducir el riesgo de archivos parciales. Si hay un error al leer o guardar, se muestra en la interfaz en lugar de fallar silenciosamente.

## Calendario

La vista de calendario:

- Comprueba que existan las variables de entorno requeridas.
- Lista hasta 10 próximos eventos.
- Permite crear eventos nuevos.
- Muestra errores de credenciales, dependencias o API dentro de la TUI.

Los eventos creados incluyen:

- Título obligatorio.
- Inicio obligatorio.
- Fin obligatorio y posterior al inicio.
- Descripción opcional.

## Desarrollo

Ejecutar tests:

```bash
python -m pytest -q
```

Comprobar compilación:

```bash
python -m compileall organizer_cli.py test
```

El workflow de GitHub Actions ejecuta compilación y tests en pushes a `main`/`feature/**` y en pull requests hacia `main`.

## Cambios en la versión 1.2.0

- Corregido el fallo de tests causado por refrescar widgets Textual antes de montar la app.
- Añadido flujo real para crear eventos de Google Calendar.
- `n` ahora crea tareas o eventos según la vista activa.
- Sustituido el fallo silencioso de calendario por errores visibles en la UI.
- Mejorado el guardado de tareas con escritura temporal.
- Añadidos tests para fechas de eventos y creación de eventos con servicio simulado.
- Actualizado CI para ejecutar tests antes del merge, no después.

## Estado de pruebas

Estado local verificado:

```text
18 passed
```
