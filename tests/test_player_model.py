from models.player_model import predict_player_points
from models.monte_carlo import MonteCarlo

player_id = 430 #Haaland
gw = 14

mean, std = predict_player_points(player_id, gw)
mc = MonteCarlo(n_sims=10000)

dist = mc.simulate(mean, std)
print("Mean:", mean)
print(dist.summary())
