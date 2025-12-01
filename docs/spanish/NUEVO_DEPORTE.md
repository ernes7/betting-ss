# Agregar un Nuevo Deporte

Esta guia explica como agregar un nuevo deporte/liga a la Plataforma de Analisis de Apuestas Deportivas.

## Descripcion General

Agregar un nuevo deporte requiere implementar varios componentes:

1. **Configuracion del Deporte** - Implementa la interfaz `SportConfig`
2. **Archivo de Equipos** - Metadatos de equipos con abreviaturas
3. **Archivo de Constantes** - URLs, mapeo de tablas, limites de tasa
4. **Componentes de Prompt** - Plantillas de prompt especificas del deporte
5. **Scraper de Cuotas** - Parsing de cuotas de DraftKings (opcional)
6. **Extractor de Resultados** - Parsing de boxscores/resultados
7. **Registro en Factory** - Registrar el nuevo deporte

## Requisitos Previos

Antes de comenzar, necesitas:

- **Fuente de Datos**: Un sitio web de estadisticas (ej. Baseball-Reference para MLB, Hockey-Reference para NHL)
- **Comprension de Tablas HTML**: IDs de tablas del sitio fuente para scraping
- **Lista de Equipos**: Todos los equipos con abreviaturas usadas por el sitio fuente
- **Patron de URL de DraftKings**: Si vas a obtener cuotas de DraftKings

## Estructura de Directorios

Crea la siguiente estructura bajo `sports/`:

```
sports/
└── {deporte}/
    ├── __init__.py
    ├── {deporte}_config.py      # Implementacion de SportConfig
    ├── teams.py                 # Metadatos de equipos
    ├── constants.py             # URLs, tablas, limites de tasa
    ├── prompt_components.py     # Plantillas de prompt para IA
    ├── odds_scraper.py          # Parsing de DraftKings (opcional)
    ├── {deporte}_results_fetcher.py  # Parsing de boxscores
    └── data/
        ├── rankings/            # Estadisticas de toda la liga
        ├── profiles/            # Datos especificos por equipo
        ├── predictions/         # Predicciones de IA
        ├── predictions_ev/      # Predicciones de calculadora EV
        ├── odds/                # Cuotas de DraftKings
        ├── results/             # Resultados de partidos
        └── analysis/            # Analisis P&L
```

---

## Paso 1: Crear teams.py

Define todos los equipos con sus metadatos.

**Archivo**: `sports/{deporte}/teams.py`

```python
"""Constantes y metadatos de equipos para {DEPORTE}."""

# Todos los equipos con metadatos
TEAMS = [
    {
        "name": "Nombre Completo del Equipo",  # ej. "Boston Bruins"
        "abbreviation": "ABBR",                # Abreviatura de DraftKings (ej. "BOS")
        "ref_abbr": "abbr",                    # Abreviatura del sitio de referencia (ej. "bos")
        "city": "Ciudad",                      # ej. "Boston"
        "mascot": "Mascota",                   # ej. "Bruins"
    },
    # ... agregar todos los equipos
]

# Mapeos de utilidad (auto-generados)
TEAM_NAMES = sorted([team["name"] for team in TEAMS])
TEAM_ABBR_MAP = {team["abbreviation"]: team["name"] for team in TEAMS}
TEAM_NAME_TO_ABBR = {team["name"]: team["abbreviation"] for team in TEAMS}
DK_TO_REF_ABBR = {team["abbreviation"]: team["ref_abbr"] for team in TEAMS}
REF_TO_DK_ABBR = {team["ref_abbr"]: team["abbreviation"] for team in TEAMS}
```

**Puntos Clave**:
- `abbreviation`: Lo que usa DraftKings (usualmente codigos estandar de 2-3 letras)
- `ref_abbr`: Lo que usa el sitio de referencia (puede diferir del estandar)

---

## Paso 2: Crear constants.py

Define URLs, mapeo de tablas y configuracion.

**Archivo**: `sports/{deporte}/constants.py`

```python
"""Constantes de configuracion para scraping y analisis de {DEPORTE}."""

from shared.config import (
    SPORTS_REFERENCE_RATE_LIMIT_CALLS,
    SPORTS_REFERENCE_RATE_LIMIT_PERIOD,
)

# Ano de temporada actual
CURRENT_YEAR = 2025

# Monto fijo de apuesta para calculos de P&L
FIXED_BET_AMOUNT = 100

# Limitacion de tasa (usar limites globales de Sports-Reference)
REF_RATE_LIMIT_CALLS = SPORTS_REFERENCE_RATE_LIMIT_CALLS
REF_RATE_LIMIT_PERIOD = SPORTS_REFERENCE_RATE_LIMIT_PERIOD

# URLs del sitio de referencia
STATS_URL = f"https://www.{deporte}-reference.com/years/{CURRENT_YEAR}/"
DEFENSIVE_STATS_URL = None  # Configurar si el deporte tiene pagina defensiva separada

# Tablas de rankings a extraer (nombre_tabla: id_tabla_html)
# Inspeccionar el HTML para encontrar IDs de tablas
RANKING_TABLES = {
    "standings": "standings",
    "team_stats": "team_stats",
    # ... agregar mas segun sea necesario
}

# Tablas de rankings defensivos (si aplica)
DEFENSIVE_RANKING_TABLES = {
    # "team_defense": "defense_stats",
}

# Tablas de perfil de equipo a extraer de paginas de equipos
TEAM_PROFILE_TABLES = {
    "roster": "roster",
    "schedule": "games",
    "stats": "team_stats",
    # ... agregar mas segun sea necesario
}

# Tablas de resultados a extraer de paginas de boxscore
RESULT_TABLES = {
    "scoring": "scoring",
    "team_stats": "team_stats",
    "player_stats": "player_stats",
    # ... agregar mas segun sea necesario
}

# Rutas de carpetas de datos
DATA_RANKINGS_DIR = "{deporte}/data/rankings"
DATA_PROFILES_DIR = "{deporte}/data/profiles"
DATA_ODDS_DIR = "{deporte}/data/odds"

# Tipos de mercado de cuotas (para DraftKings)
ODDS_MARKET_TYPES = {
    "game_lines": ["Moneyline", "Spread", "Total"],
    "player_props": [
        # Mercados de props de jugadores especificos del deporte
    ],
}
```

**Encontrar IDs de Tablas**:
1. Abre el sitio de referencia en un navegador
2. Clic derecho en una tabla → Inspeccionar
3. Busca `id="nombre_tabla"` en el HTML

---

## Paso 3: Crear {deporte}_config.py

Implementa la interfaz `SportConfig`.

**Archivo**: `sports/{deporte}/{deporte}_config.py`

```python
"""Configuracion especifica del deporte implementando interfaz SportConfig."""

from shared.base.sport_config import SportConfig
from sports.{deporte}.teams import TEAMS
from sports.{deporte}.constants import (
    CURRENT_YEAR,
    REF_RATE_LIMIT_CALLS,
    REF_RATE_LIMIT_PERIOD,
    STATS_URL,
    DEFENSIVE_STATS_URL,
    RANKING_TABLES,
    DEFENSIVE_RANKING_TABLES,
    TEAM_PROFILE_TABLES,
    RESULT_TABLES,
    DATA_RANKINGS_DIR,
    DATA_PROFILES_DIR,
)
from sports.{deporte}.prompt_components import {Deporte}PromptComponents


class {Deporte}Config(SportConfig):
    """Configuracion especifica del deporte."""

    @property
    def sport_name(self) -> str:
        return "{deporte}"

    @property
    def teams(self) -> list[dict]:
        return TEAMS

    @property
    def ranking_tables(self) -> dict[str, str]:
        return RANKING_TABLES

    @property
    def profile_tables(self) -> dict[str, str]:
        return TEAM_PROFILE_TABLES

    @property
    def result_tables(self) -> dict[str, str]:
        return RESULT_TABLES

    @property
    def stats_url(self) -> str:
        return STATS_URL

    @property
    def defensive_stats_url(self) -> str:
        return DEFENSIVE_STATS_URL

    @property
    def defensive_ranking_tables(self) -> dict[str, str]:
        return DEFENSIVE_RANKING_TABLES

    @property
    def rate_limit_calls(self) -> int:
        return REF_RATE_LIMIT_CALLS

    @property
    def rate_limit_period(self) -> int:
        return REF_RATE_LIMIT_PERIOD

    @property
    def data_rankings_dir(self) -> str:
        return DATA_RANKINGS_DIR

    @property
    def data_profiles_dir(self) -> str:
        return DATA_PROFILES_DIR

    @property
    def predictions_dir(self) -> str:
        return "{deporte}/data/predictions"

    @property
    def predictions_ev_dir(self) -> str:
        return "{deporte}/data/predictions_ev"

    @property
    def results_dir(self) -> str:
        return "{deporte}/data/results"

    @property
    def analysis_dir(self) -> str:
        return "{deporte}/data/analysis"

    @property
    def analysis_ev_dir(self) -> str:
        return "{deporte}/data/analysis_ev"

    @property
    def prompt_components(self) -> {Deporte}PromptComponents:
        return {Deporte}PromptComponents()

    def build_team_url(self, team_abbr: str) -> str:
        """Construye URL de equipo usando patron del sitio de referencia."""
        return f"https://www.{deporte}-reference.com/teams/{team_abbr}/{CURRENT_YEAR}.htm"

    def build_boxscore_url(self, game_date: str, home_team_abbr: str) -> str:
        """Construye URL de boxscore para resultados de partidos."""
        date_str = game_date.replace("-", "")
        return f"https://www.{deporte}-reference.com/boxscores/{date_str}0{home_team_abbr}.htm"
```

---

## Paso 4: Crear prompt_components.py

Define prompts especificos del deporte para predicciones de IA.

**Archivo**: `sports/{deporte}/prompt_components.py`

```python
"""Componentes de prompt especificos del deporte para predicciones de IA."""


class {Deporte}PromptComponents:
    """Plantillas de prompt para analisis de apuestas de {DEPORTE}."""

    @property
    def sport_name(self) -> str:
        return "{DEPORTE}"

    @property
    def bet_types(self) -> str:
        """Retorna tipos de apuesta disponibles para este deporte."""
        return """
Tipos de Apuesta Disponibles:
- Moneyline (ganador del partido)
- Spread (diferencial de puntos/goles/carreras)
- Total (mas/menos del puntaje combinado)
- Props de Jugadores:
  - Puntos/Goles anotados
  - Asistencias
  - Tiros al arco
  - Otras estadisticas especificas del deporte
"""

    @property
    def key_factors(self) -> str:
        """Retorna factores clave para el analisis."""
        return """
Factores Clave a Considerar:
- Forma reciente (ultimos 5-10 partidos)
- Historial frente a frente
- Rendimiento local/visitante
- Lesiones y cambios de alineacion
- Dias de descanso entre partidos
- Dificultad del calendario
"""

    @property
    def analysis_instructions(self) -> str:
        """Retorna instrucciones de analisis."""
        return """
Instrucciones de Analisis:
1. Comparar estadisticas de equipos
2. Evaluar enfrentamientos de jugadores
3. Considerar factores situacionales
4. Calcular probabilidad real
5. Identificar valor vs cuotas de casas de apuestas
6. Enfocarse en umbral minimo de EV +3%
"""
```

---

## Paso 5: Registrar el Deporte

Agrega el nuevo deporte al factory.

**Archivo**: `shared/register_sports.py`

```python
"""Registrar todos los deportes disponibles con el factory."""

from shared.factory import SportFactory


def register_all_sports():
    """Registrar todas las configuraciones de deportes con el factory."""
    from sports.nfl.nfl_config import NFLConfig
    from sports.nba.nba_config import NBAConfig
    from sports.{deporte}.{deporte}_config import {Deporte}Config  # AGREGAR ESTO

    SportFactory.register("nfl", NFLConfig)
    SportFactory.register("nba", NBAConfig)
    SportFactory.register("{deporte}", {Deporte}Config)  # AGREGAR ESTO


register_all_sports()
```

---

## Paso 6: Crear Directorios de Datos

Crea la estructura de carpetas de datos:

```bash
mkdir -p sports/{deporte}/data/rankings
mkdir -p sports/{deporte}/data/profiles
mkdir -p sports/{deporte}/data/predictions
mkdir -p sports/{deporte}/data/predictions_ev
mkdir -p sports/{deporte}/data/odds
mkdir -p sports/{deporte}/data/results
mkdir -p sports/{deporte}/data/analysis
```

---

## Paso 7: Agregar al CLI (Opcional)

Agrega el deporte al menu del CLI en `cli.py`:

```python
SPORTS = {
    "1": {"name": "NFL", "emoji": "🏈", "code": "nfl"},
    "2": {"name": "NBA", "emoji": "🏀", "code": "nba"},
    "3": {"name": "{DEPORTE}", "emoji": "🏒", "code": "{deporte}"},  # AGREGAR ESTO
}
```

---

## Probando tu Implementacion

1. **Verificar Registro**:
   ```python
   from shared.factory import SportFactory
   config = SportFactory.create("{deporte}")
   print(config.config.sport_name)  # Deberia imprimir "{deporte}"
   ```

2. **Probar Busqueda de Equipo**:
   ```python
   team = config.config.get_team_by_name("Nombre del Equipo")
   print(team)  # Deberia retornar diccionario del equipo
   ```

3. **Probar Construccion de URL**:
   ```python
   url = config.config.build_team_url("abbr")
   print(url)  # Deberia retornar URL valida
   ```

4. **Ejecutar Tests**:
   ```bash
   poetry run pytest sports/{deporte}/tests/ -v
   ```

---

## Lista de Verificacion

- [ ] Creada estructura de directorios `sports/{deporte}/`
- [ ] Implementado `teams.py` con todos los equipos
- [ ] Implementado `constants.py` con URLs y mapeo de tablas
- [ ] Implementado `{deporte}_config.py` extendiendo `SportConfig`
- [ ] Implementado `prompt_components.py`
- [ ] Registrado deporte en `shared/register_sports.py`
- [ ] Creados directorios de datos
- [ ] Agregado al menu CLI (opcional)
- [ ] Probados registro y busqueda de equipos
- [ ] Agregados tests unitarios

---

## Referencia: Implementacion de NFL

Para un ejemplo completo funcionando, ver la implementacion de NFL:

- `sports/nfl/nfl_config.py` - Implementacion de SportConfig
- `sports/nfl/teams.py` - Metadatos de equipos
- `sports/nfl/constants.py` - URLs y mapeo de tablas
- `sports/nfl/prompt_components.py` - Plantillas de prompts

---

## Problemas Comunes

1. **IDs de Tabla No Encontrados**: Usa herramientas de desarrollo del navegador para inspeccionar elementos de tablas
2. **Limitacion de Tasa**: Usa los limites de tasa compartidos de Sports-Reference
3. **Discrepancia de Abreviaturas**: Asegurate de que las abreviaturas de DraftKings y del sitio de referencia esten mapeadas correctamente
4. **Imports Circulares**: Importa configs de deportes dentro de la funcion `register_all_sports()`
