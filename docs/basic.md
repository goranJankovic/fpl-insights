
# Basic Team Prediction Model

The Basic Team Prediction Model provides a simplified approach to estimating FPL team scores using Monte Carlo simulation.

## 1. Overview
The basic model:
1. Computes player expected points using points-per-game (PPG).
2. Calculates standard deviation using player history or fallback values.
3. Simulates point distributions via a normal distribution.
4. Sums all players to obtain team-level results.

## 2. Player Expected Points
Basic EP is calculated from:
```
expected_points = player.points_per_game
```

## 3. Variance (STD)
If sufficient history exists:
```
std = stdev(last_n_points)
```
Else fallback:
```
std = expected_points * 0.35
```

## 4. Player Simulation
A normal distribution:
```
Normal(mean = expected_points, std = std)
```

## 5. Team Simulation
Sum of all player distributions gives the final team distribution.

## 6. Output
The model outputs:
- expected  
- median  
- p25  
- p75  
- p90  
- raw distribution samples

## 7. Differences vs. Advanced Model
- No fixture difficulty
- No DGW support
- No captain/vice logic
- No bench boost
- No per-fixture EP
- No underlying xG-based calculation
