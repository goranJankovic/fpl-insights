# Advanced Team Prediction Model (Version 1.0)

This document describes the logic, assumptions, and structure of the Advanced Team Prediction Model used in the FPLInsights project.  
The advanced model builds on top of the basic Monte Carlo summation engine, adding per-fixture expected points, DGW handling, captain/vice logic, and player variance modeling.

## 1. Overview
The Advanced Team Model simulates total expected points for a full FPL squad in a specific gameweek using a multi-layer system:
1. Per-player expected points based on performance metrics.
2. Fixture-aware adjustments.
3. Support for double gameweeks (DGW) and blank gameweeks.
4. Player-level Monte Carlo simulation.
5. Team-level aggregation.
6. Accurate handling of captain, vice-captain, and triple captain.
7. Optional bench boost support.

## 2. Player Expected Points (Fixture-Based)
EP is computed using PPG, form, xG, xA, and fixture difficulty.  
Formula:
```
base_ep = 0.5 * PPG + 0.3 * form + 0.2 * (xG + xA)
```

Difficulty modifier:
```
adjustment = 1 + (3 - difficulty) * 0.1
```

Total EP for GW is the sum of all fixtures. Supports DGW.

## 3. Variance (Standard Deviation)
If history exists (≥3 matches):
```
std = stdev(last_n_points)
```
Else:
```
std = total_ep * 0.35
```

## 4. Player Simulation
Normal distribution per fixture:
```
Normal(mean = fixture_ep, std = fixture_std)
```
Summed per fixture → full GW distribution.

## 5. Team Simulation
Team points = sum of all player simulations. Bench added only if Bench Boost.

## 6. Captain and Vice-Captain Logic
- Captain → doubled  
- Triple Captain → tripled  
- Vice replaces captain **only if captain scores 0** (DNP)

## 7. Output
Model outputs:
- expected  
- median  
- p25  
- p75  
- p90  
- full sample distribution  

## 8. Limitations (to be added later)
- Poisson goal/assist modeling
- Clean sheet probability model
- Card risk model
- Autosubs
- Correlation modeling
- Module split into advanced/
