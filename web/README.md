# Web migration foundation

The desktop application remains at the repository root. The web application is
added alongside it in `web/` and reuses the Qt-independent Frog Rectus model at
`integrated_modules/frog_rectus/simulation/engine.py`.

## Start locally

From the repository root, run `docker compose up --build`, then open
`http://localhost:3000`. The API docs are at `http://localhost:8000/docs`.

The initial web practical supports agonist concentration entry in molar or mass
units, ACh chloride molecular-weight conversion, optional competitive
d-tubocurarine blockade, the engine's Hill response and contraction trace, and
persisted observations in PostgreSQL. This preserves the existing model's
calibration: ACh EC50 3 µM, Hill coefficient 1.6, drug-specific efficacy and
potency, 5 mm baseline, and 45 mm maximum contraction above baseline.

The older top-level `experiments/frog_rectus.py` is a separate introductory
demo using a Gaussian curve and fixed mL doses. It is not the integrated Frog
Rectus practical documented in `integrated_modules/frog_rectus/README.md` and
is not used as the web model.
