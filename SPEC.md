# OrganizerCLI - Especificación

## 1. Project Overview

- **Nombre**: OrganizerCLI
- **Tipo**: Terminal User Interface (TUI) app
- **Funcionalidad**: Gestor de tareas y eventos de calendario con diseño minimalista estilo terminal
- **Usuario objetivo**: Personas que prefieren interfaces rápidas y minimalistas

## 2. UI/UX Specification

### Layout Structure

- **Header**: Barra de título con logo ASCII y navegación
- **Main Area**: Panel central con las vistas activas
- **Sidebar**: Navegación lateral con tabs/icons
- **Footer**: Barra de status y shortcuts

### Visual Design

- **Paleta de colores** (tema oscuro terminal):
  - Background: `#0d1117` (negro profundo)
  - Surface: `#161b22` (gris oscuro)
  - Primary: `#58a6ff` (azul brillante)
  - Secondary: `#8b949e` (gris medio)
  - Accent: `#3fb950` (verde éxito)
  - Warning: `#d29922` (amarillo)
  - Error: `#f85149` (rojo)
  - Text: `#c9d1d9` (blanco grisáceo)
  - Muted: `#484f58` (gris muted)

- **Tipografía**:
  - Font principal: Sistema monospace
  - Títulos: Bold
  - Body: Regular

- **Efectos**:
  - Bordes simples
  - Subtle highlights en hover
  - Animaciones suaves en transiciones

### Componentes

1. **TaskItem**: Checkbox + texto + fecha + acciones
2. **EventCard**: Título + hora + descripción + botón eliminar
3. **InputField**: Campo de entrada estilo terminal
4. **Button**: Botones minimalistas con atajos de teclado
5. **TabNav**: Navegación entre secciones

## 3. Functionality Specification

### Vista de Tareas (TODO)

- **Crear tarea**: Botón "+" o shortcut "n" → input modal
- **Completar tarea**: Click en checkbox o "x" toggle
- **Eliminar tarea**: Shortcut "d" sobre tarea seleccionada
- **Filtrar**: Ver todas / pendientes / completadas
- **Datos**: título, descripción (opcional), fecha creación

### Vista de Calendario

- **Crear evento**: Formulario con:
  - Título (requerido)
  - Fecha y hora inicio
  - Fecha y hora fin
  - Descripción (opcional)
- **Sincronización**: Se crea directamente en Google Calendar
- **Listar eventos**: Ver próximos eventos del calendario

### Keyboard Shortcuts

- `n`: Nueva tarea / nuevo evento
- `d`: Eliminar item seleccionado
- `x`: Toggle completar tarea
- `1/2/3`: Cambiar entre vistas (Tareas/ Calendario/ Ajustes)
- `q`: Salir
- `?`: Ver ayuda

## 4. Acceptance Criteria

- [ ] La app inicia y muestra interfaz estilo terminal
- [ ] Se pueden crear tareas que se guardan localmente
- [ ] Se pueden marcar tareas como completadas
- [ ] Se pueden eliminar tareas
- [ ] Se puede crear un evento que se sincroniza con Google Calendar
- [ ] La navegación entre vistas funciona con keyboard shortcuts
- [ ] El diseño es minimalista y coherente con la estética terminal
