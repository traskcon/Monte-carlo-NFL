# Monte-carlo-NFL
Play-by-play simulations of NFL matchups

### Time Test
* Single Game Simulation (verbose=True): 0.1868s
* Single Game Simulation (verbose=False): 0.1309s

Serial vs Parallel:
* 100 Games: 17.04s (Serial), 12.05s (Parallel, 8 cores)
* 1,000 Games: 171.42s (Serial), 27.22s (Parallel, 8 cores)
* 10,000 Games: ~27 minutes (Serial), 234.95s (Parallel, 8 cores)

Back of napkin estimates place the number of simulations required to achieve a robust estimate at 10,000 - 100,000 depending on confidence level and score range