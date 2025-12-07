
# FPLInsights

FPLInsights is a Python project for simulating, analyzing, and predicting Fantasy Premier League outcomes.  
It combines structured statistical models (Monte Carlo simulation, probabilistic scoring, trend tracking) with optional AI-assisted components for transfer, captaincy, and Free Hit recommendations.

## Features
- Local SQLite storage with full player, fixture, and gameweek history
- Update pipeline that imports all required FPL API data
- Team-level prediction models
- Player-level prediction models
- Monte Carlo engine for expected points distributions
- AI modules for:
  - captaincy advice
  - transfer evaluation
  - Free Hit squad building
  - H2H predictions

## Documentation
Full documentation is located in the `docs/` directory:

- overview.md — high-level explanation of FPLInsights  
- basic.md — basic prediction concepts  
- advanced.md — advanced fixture-aware and model-aware logic  
- architecture.md — how the project is structured internally  
- api.md — description of available CLI interfaces  
- roadmap.md — planned features and improvements  

## Environment Setup
Create a `.env` file in the project root with:

```
OPENAI_API_KEY=your_key_here
```

This is required only for the AI modules.  
Core predictive models (Monte Carlo, player/team stats) do *not* require an API key.

## Usage
Update FPL data first:

```
python update_fpl.py
```

Run prediction modules or AI tools via the CLI:

```
python ai.py captaincy --team <entry> --gw <gw>
python ai.py transfers --team <entry> --gw <gw>
python ai.py freehit --gw <gw> --budget <value>
python ai.py h2h --teamA <id> --teamB <id> --gw <gw>
```

FPLInsights is built for extensibility.  
Future planned extensions include Poisson-based scoring, enhanced xMins modeling, improved autosubs simulation, and richer AI reasoning.

e-mail: jankovicsrb@gmail.com