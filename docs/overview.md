# Prediction Engine Overview

This document provides a high-level overview of the FPLInsights prediction engine.

## 1. Basic Prediction Model
- Uses PPG + normal distribution.
- Fast and simple.
- Ideal for quick checks.

## 2. Advanced Prediction Model
- Fixture-based expected points
- Difficulty adjustments
- DGW support
- Captain/VC/TC logic
- Bench boost support
- Player variance from history
- Full Monte Carlo simulation

## 3. Monte Carlo Engine
Generates thousands of possible outcomes and computes:
- mean (expected)
- median
- p25
- p75
- p90
- full raw distribution

## 4. Future Expansions
- Poisson goal/assist modeling
- Clean sheet probability
- Autosubs logic
- GK vs attacker correlation
- Advanced modular simulation system
