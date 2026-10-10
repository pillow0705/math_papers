# CCSGD experiment source

Current sources copied from `split_papers/complex_correction/experiments`, without code changes. Archived variants, generated results, training data, and caches are excluded.

| Experiment | Entry point | Supporting source |
|---|---|---|
| Nonlinear-feature regression | [run_mse.py](run_mse.py) | [simulate.cpp](simulate.cpp), C++17 |
| Single-hidden-layer sine network | [neural_network/run_nn.py](neural_network/run_nn.py) | Seven methods with fresh measurement noise |
| Five-seed network run | [neural_network/run_long.py](neural_network/run_long.py) | Launches `run_nn.py` and combines trajectories |

From the CCSGD repository root:

```sh
python3 -m pip install -r experiments/requirements.txt
python3 experiments/run_mse.py
python3 experiments/neural_network/run_nn.py
# Alternative to the preceding network command: five concurrent one-seed runs
python3 experiments/neural_network/run_long.py
```

Regression requires a C++17 compiler (`c++`, or set `CXX`). Python dependency versions are not pinned because the supplied source has no archived environment lock.

Defaults are 256 regression streams with 10,000,000 updates, and five network seeds with 200,000 updates. Each command writes figures, trajectories, and summaries to its local `results/`; `run_long.py` also uses `neural_network/long_runs/`. These outputs are not included in this source-only copy. No experiment was run during copying.
