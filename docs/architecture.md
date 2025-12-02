# Project Architecture

## Structure
```
FPLInsights/
    config.py
    db/
    models/
    pipeline/
    predictions/
    tests/
    docs/
```

## Module Roles

### config.py
Central configuration.

### db/
SQLite connection helpers and schema.

### pipeline/
Fetch + normalize + update FPL data.

### models/
Core models like Monte Carlo engine.

### predictions/
Basic and advanced prediction engines.

### tests/
All test scripts.

### docs/
Documentation files.

## Future Changes
The predictions/ folder will be split into a modular advanced/ system in Phase 5.
