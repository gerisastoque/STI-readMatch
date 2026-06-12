# 📚 ReadMatch

> Plataforma de recomendación de libros grupales basada en similitud de preferencias lectoras

[![Web App](https://img.shields.io/badge/🌐_Web_App-Vercel-black?style=for-the-badge)](https://sti-readmatch.vercel.app/)
[![Diseño UI](https://img.shields.io/badge/🎨_Diseño_UI-Behance-1769ff?style=for-the-badge)](https://www.behance.net/gallery/250958241/READMATCH)
[![Telegram](https://img.shields.io/badge/💬_Grupo_Telegram-Unirse-2CA5E0?style=for-the-badge)](https://t.me/+d1ARNTYw1ow3YzUx)

ReadMatch es una aplicación móvil que conecta lectores en **círculos de lectura**, generando recomendaciones personalizadas para grupos completos mediante vectores de preferencias y similitud de coseno. Combina un perfil lector único por usuario (el "arquetipo") con la inteligencia colectiva del grupo para sugerir el próximo libro ideal.

---

## 🧠 Contexto del Proyecto

ReadMatch nace de una pregunta: ¿cómo elegir el próximo libro cuando un grupo de amigos tiene gustos distintos?

La solución es un sistema de **vectores de preferencias**: cada usuario completa un onboarding que captura sus géneros favoritos, complejidad narrativa, ritmo de lectura y apertura a nuevos géneros. Estos datos se transforman en un vector numérico. Cuando un grupo quiere una recomendación, el sistema promedia los vectores de todos los miembros y lo compara contra los vectores de más de 50 libros en la base de datos, devolviendo el mejor match por **similitud de coseno**.

Adicionalmente, cada usuario recibe un **arquetipo lector** (como _El Filósofo_, _La Romántica_ o _El Explorador_), asignado mediante la API de Claude a partir de su perfil completo, que personaliza la experiencia y le da identidad a cada lector.

---

## ✨ Funcionalidades Principales

### 📱 App Móvil
- **Onboarding personalizado** – captura géneros preferidos, complejidad narrativa, ritmo, y apertura a nuevos géneros
- **Arquetipo lector** – cada usuario recibe un arquetipo único generado por IA con texto revelador
- **Círculos de lectura** – crea o únete a grupos mediante código de invitación (`RM-XXXX`)
- **Búsqueda global de círculos** – descubre grupos públicos con búsqueda en tiempo real (estilo Instagram/Telegram)
- **Recomendaciones grupales** – genera el libro ideal para el grupo en base a la similitud promedio de preferencias
- **Historial de lecturas** – registro de libros leídos por grupo

### 🤖 Bot de Telegram
- **Vinculación de cuenta** – conecta tu cuenta de ReadMatch con Telegram mediante un comando
- **Recomendaciones por chat** – solicita recomendaciones para tu círculo directamente desde Telegram

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Cliente Móvil                        │
│              React Native / Expo                        │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
┌─────────────────┐      ┌──────────────────────┐
│    Supabase     │      │   FastAPI Backend     │
│                 │      │   (Render.com)        │
│  • Auth         │      │                       │
│  • PostgreSQL   │      │  • Motor de           │
│  • Realtime     │      │    recomendaciones    │
│  • Storage      │      │  • Similitud de       │
│  • RPCs         │      │    coseno             │
└─────────────────┘      └──────────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
             ┌──────────────────┐    ┌───────────────────┐
             │   Claude API     │    │       n8n         │
             │  (Anthropic)     │    │  (Automatización) │
             │                  │    │                   │
             │  • Asignación    │    │  • Bot Telegram   │
             │    de arquetipos │    │  • Workflows      │
             └──────────────────┘    └───────────────────┘
```

---

## 🛠️ Tecnologías Utilizadas

| Capa | Tecnología | Descripción |
|------|-----------|-------------|
| **Frontend** | React Native + Expo | App móvil multiplataforma |
| **Base de datos** | Supabase (PostgreSQL) | Auth, datos, Realtime y RPCs |
| **Backend** | FastAPI (Python) | Motor de recomendaciones por coseno |
| **Deploy Backend** | Render.com | Hosting del servidor FastAPI |
| **IA Arquetipos** | Claude API (Anthropic) | Asignación de arquetipo lector |
| **Automatización** | n8n | Bot de Telegram y flujos de trabajo |
| **Control de versiones** | Git / GitHub | Rama principal: `feat/flaskapi` |

---

## 📦 Estructura del Proyecto

```
readmatch/
├── src/
│   ├── screens/           # Pantallas de la app
│   │   ├── OnboardingScreen.js
│   │   ├── HomeScreen.js
│   │   ├── GroupDetailScreen.js
│   │   ├── BookScreen.js
│   │   ├── JoinGroupScreen.js
│   │   └── ...
│   ├── components/        # Componentes reutilizables
│   ├── navigation/        # Configuración de rutas
│   └── lib/
│       └── supabase.js    # Cliente de Supabase
├── backend/               # FastAPI
│   ├── main.py
│   └── recommendations.py # Lógica de coseno
├── app.json
└── package.json
```

---

## 🚀 Cómo Inicializar el Proyecto

### 🔗 Links de acceso rápido

| Recurso | URL |
|---------|-----|
| 🌐 Web App (Vercel) | [sti-readmatch.vercel.app](https://sti-readmatch.vercel.app/) |
| 🎨 Diseño UI (Behance) | [Galería ReadMatch](https://www.behance.net/gallery/250958241/READMATCH) |
| 💬 Grupo Telegram | [Unirse al grupo](https://t.me/+d1ARNTYw1ow3YzUx) |

---

### Prerrequisitos

- Node.js >= 18
- Python >= 3.10
- Expo CLI (`npm install -g expo-cli`)
- Cuenta en [Supabase](https://supabase.com)
- Cuenta en [Render](https://render.com) (para el backend)
- API Key de [Anthropic](https://console.anthropic.com)

---

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/readmatch.git
cd readmatch
git checkout feat/flaskapi
```

---

### 2. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
EXPO_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key
EXPO_PUBLIC_API_URL=https://sti-readmatch.onrender.com
EXPO_PUBLIC_ANTHROPIC_KEY=tu_api_key_de_anthropic
```

---

### 3. Instalar dependencias del frontend

```bash
npm install
```

---

### 4. Configurar el backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate       # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Ejecutar localmente:

```bash
uvicorn main:app --reload --port 8000
```

El backend también está desplegado en producción en:
```
https://sti-readmatch.onrender.com
```

---

### 5. Migraciones de base de datos (Supabase)

Ejecutar en el SQL Editor de Supabase:

```sql
-- Agregar columna de código de invitación a los grupos
ALTER TABLE recommendation_groups
ADD COLUMN IF NOT EXISTS join_code TEXT UNIQUE;

-- Generar códigos para grupos existentes
UPDATE recommendation_groups
SET join_code = 'RM-' || upper(substring(md5(random()::text), 1, 4))
WHERE join_code IS NULL;
```

---

### 6. Iniciar la app

```bash
npx expo start
```

Escanea el QR con la app **Expo Go** o ejecuta en emulador:

```bash
npx expo run:android
# o
npx expo run:ios
```

---

## 🤖 Bot de Telegram

El bot de Telegram está conectado mediante **n8n** y ofrece dos funcionalidades operativas. Puedes unirte al grupo de prueba aquí: **[→ Unirse al grupo de Telegram](https://t.me/+d1ARNTYw1ow3YzUx)**

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `/vincular tu_email@gmail.com` | Conecta tu cuenta de ReadMatch con Telegram usando el email registrado |
| `/recomendar` | Solicita una recomendación para tu círculo activo |

### Flujo de vinculación

1. Únete al grupo de Telegram: [https://t.me/+d1ARNTYw1ow3YzUx](https://t.me/+d1ARNTYw1ow3YzUx)
2. Envía en el grupo: `/vincular tu_email@gmail.com` (el email con el que te registraste en ReadMatch)
3. El bot confirma la conexión y queda listo para recibir comandos

### Flujo de recomendación

1. Envía `/recomendar` en el grupo
2. El bot consulta tu círculo activo en Supabase
3. Llama al backend FastAPI con los vectores del grupo
4. Responde con el libro recomendado, su sinopsis y puntuación de match

> **Nota:** El backend se despliega en Railway. Si el bot no responde, es posible que el servicio esté iniciando — espera unos segundos y vuelve a intentarlo. Las funcionalidades de búsqueda de grupos y gestión de membresías están disponibles únicamente desde la app móvil.

---

## 🧮 Cómo Funciona el Motor de Recomendaciones

Cada usuario genera un **vector de preferencias** durante el onboarding con dimensiones como:

- Géneros favoritos (Fantasía, Terror, Romance, etc.)
- Complejidad narrativa (1–5)
- Ritmo de lectura preferido
- Apertura a géneros nuevos

Cada libro en la base de datos tiene un **vector de características** equivalente. Al solicitar una recomendación grupal:

1. Se promedian los vectores de todos los miembros del grupo
2. Se calcula la **similitud de coseno** entre el vector promedio y cada libro
3. Se devuelve el libro con mayor similitud (excluyendo ya leídos)

```
similitud(A, B) = (A · B) / (||A|| × ||B||)
```

---

## 🎭 Arquetipos Lectores

Cada usuario recibe un arquetipo único al completar el onboarding. Los 12 arquetipos disponibles son:

| Arquetipo | Perfil |
|-----------|--------|
| El Filósofo | Reflexivo, busca profundidad y ensayo |
| La Romántica | Apasionada, vive las historias de amor |
| El Explorador | Curioso, abierto a cualquier género |
| El Académico Oscuro | Intelectual con gusto por lo oscuro |
| El Visionario | Amante de la ciencia ficción y futuros |
| El Aventurero | Acción, aventura y mundos nuevos |
| El Estratega | Lector analítico y de no ficción |
| El Cronista | Fascinado por historia y biografías |
| El Intrépido | Busca lo perturbador y lo inesperado |
| El Soñador | Fantástico, magia y mundos imaginarios |
| El Empático | Narrativas humanas y emocionales |
| El Inconformista | Lectura experimental y disruptiva |

El arquetipo es asignado por la **API de Claude**, que recibe el perfil completo del usuario y devuelve el arquetipo más afín junto con un texto revelador personalizado.

---

## 👥 Equipo

Proyecto desarrollado como entrega final del curso de Ingeniería de Software / Desarrollo Móvil.

---

## 📄 Licencia

Este proyecto es de uso académico. Todos los derechos reservados © 2025.
