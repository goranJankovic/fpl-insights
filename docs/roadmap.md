# FPLInsights Roadmap

## Phase 1 — Data Layer
- API fetch
- Normalization
- SQLite storage
- Update pipeline

## Phase 2 — Basic Prediction Engine
- PPG-based EP
- Simple variance
- Team-level MC simulation

## Phase 3 — Advanced Prediction Engine v1
- Fixture-aware EP
- DGW support
- Captain/VC/TC logic
- Bench Boost logic
- Variance from history

## Phase 4 — Advanced Engine v2
- Poisson model for goals/assists
- Clean sheet probability
- Card risk EV
- Autosubs
- Correlation modeling

## Phase 5 — Modular Architecture
Split into:
```
predictions/advanced/
    minutes.py
    goals.py
    assists.py
    clean_sheets.py
    cards.py
    fixtures.py
    player_simulator.py
    team_simulator.py
```

## Phase 6 — AI Layer
- OpenAI prediction commentary
- Upside/volatility analysis
