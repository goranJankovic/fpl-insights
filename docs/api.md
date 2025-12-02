# Prediction API

## Player Simulation API
```
simulate_player_points_advanced(player_id, gw, n_sims)
```
Returns an np.ndarray.

## Team Simulation API
```
predict_team_points_advanced(starting, gw, captain_id, vice_captain_id, bench, triple_captain, bench_boost, n_sims)
```
Returns a PredictionDistribution.

## PredictionDistribution Fields
- samples
- expected
- median
- p25
- p75
- p90

## Upcoming API Additions
- Poisson-based prediction functions
- Clean sheet API
- Autosubs API
