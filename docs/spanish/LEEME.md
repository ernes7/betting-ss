# Herramienta de Analisis de Apuestas Deportivas

Plataforma de analisis de apuestas con valor esperado positivo (EV+) impulsada por IA. Identifica oportunidades de apuestas rentables (+3% EV minimo, tipicamente 3-15%) usando Claude Sonnet 4.5 y seguimiento completo de ganancias/perdidas.

## Caracteristicas

- **Analisis EV+**: Encuentra apuestas con valor esperado positivo comparando probabilidad predicha por IA vs cuotas de casas de apuestas
- **Pipeline Automatizado**: Extrae rankings de equipos, perfiles, reportes de lesiones y cuotas de DraftKings
- **Predicciones con IA**: Claude Sonnet 4.5 analiza 40K+ tokens para generar las 5 mejores apuestas EV+
- **Seguimiento de P&L**: Analisis post-partido con ROI, tasa de aciertos y edge realizado
- **Dashboard Streamlit**: Interfaz web interactiva con graficos de ganancias, predicciones filtrables y overlay de analisis
- **Arquitectura de Servicios**: Diseno modular OOP con 5 servicios independientes

## Deportes Soportados

- **NFL** (32 equipos) - Pro-Football-Reference.com + cuotas de DraftKings
- **NBA** (30 equipos) - Proximamente para apuestas EV+

## Arquitectura

```
betting-ss/
├── services/                # Servicios backend (arquitectura OOP)
│   ├── odds/               # Obtiene cuotas de apuestas de DraftKings
│   ├── prediction/         # Predicciones basadas en IA y EV
│   ├── results/            # Obtiene resultados de partidos
│   ├── analysis/           # Compara predicciones con resultados
│   └── cli/                # Orquestacion de flujos de trabajo
│
├── frontend/               # Dashboard Streamlit
│   ├── app.py              # Aplicacion principal
│   ├── theme.py            # Estilos personalizados
│   ├── components/         # Componentes UI (tarjetas, graficos, metricas)
│   ├── utils/              # Carga de datos, colores, helpers
│   └── tests/              # Tests del frontend
│
├── shared/                 # Utilidades compartidas
│   ├── base/               # Interfaces abstractas (Predictor, Analyzer)
│   ├── config/             # Gestion de configuracion
│   ├── errors/             # Manejo de errores
│   ├── logging/            # Logging por servicio
│   ├── models/             # Modelos de datos y calculadora EV
│   ├── repositories/       # Capa de acceso a datos
│   ├── scraping/           # Utilidades de web scraping
│   └── utils/              # I/O de archivos, validacion, optimizacion
│
├── sports/                 # Implementaciones por deporte
│   ├── nfl/
│   │   ├── data/           # Predicciones, analisis, cuotas, resultados
│   │   ├── nfl_config.py   # Configuracion del deporte
│   │   ├── nfl_analyzer.py # Analisis P&L
│   │   ├── teams.py        # Metadata de equipos
│   │   └── constants.py    # Constantes NFL
│   └── nba/
│       ├── data/
│       └── ...
│
├── config/                 # Configuracion YAML
│   └── settings.yaml       # Config de scraping, API, rutas
│
├── logs/                   # Archivos de log por servicio
├── cli.py                  # Punto de entrada CLI
└── pyproject.toml
```

## Configuracion

```bash
# Instalar dependencias
poetry install

# Instalar navegador para web scraping
playwright install chromium

# Configurar clave API
echo "ANTHROPIC_API_KEY=tu_clave_aqui" > .env
```

## Uso

### Interfaz CLI
```bash
poetry run python cli.py
```

**Flujo de trabajo**: Seleccionar deporte → Extraer rankings/perfiles → Proporcionar URL de cuotas DraftKings → Generar predicciones EV+ → Obtener resultados → Analizar P&L

### Dashboard Streamlit
```bash
streamlit run frontend/app.py
```

**Caracteristicas**: Ver todas las predicciones, filtrar por fecha/estado, visualizar ganancias con graficos interactivos, analizar resultados apuesta por apuesta

## Ejecutar Tests

```bash
# Ejecutar todos los tests
poetry run pytest

# Ejecutar tests de un servicio especifico
poetry run pytest services/odds/tests/
poetry run pytest frontend/tests/

# Ejecutar con cobertura
poetry run pytest --cov=services --cov=shared --cov=frontend
```

## Ejemplos de Salida

**Predicciones EV+**: Top 5 apuestas individuales ordenadas por valor esperado (+3% minimo), probabilidad implicita vs real, razonamiento para cada edge

**Analisis P&L**: Ganancia/perdida por apuesta, profit/loss con stake fijo de $100, ROI total, tasa de aciertos, edge realizado vs predicho, insights de precision

## Agregar Nuevos Deportes (NHL/MLB)

1. Crear `sports/{deporte}/{deporte}_config.py` implementando interfaz `SportConfig`
2. Crear `sports/{deporte}/prompt_components.py` con tipos de apuesta enfocados en EV
3. Crear `sports/{deporte}/{deporte}_analyzer.py` extendiendo `BaseAnalyzer`
4. Registrar en `shared/register_sports.py`

## Arquitectura de Servicios

| Servicio | Proposito | Tests |
|----------|-----------|-------|
| ODDS | Obtiene cuotas de apuestas de DraftKings | 58 |
| PREDICTION | Predicciones basadas en IA y EV | 48 |
| RESULTS | Obtiene resultados de partidos | 57 |
| ANALYSIS | Compara predicciones con resultados | 55 |
| CLI | Orquestacion de flujos de trabajo | 23 |
| FRONTEND | Utilidades del dashboard | 53 |

**Total: 294 tests**
