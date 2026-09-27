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

## Deploy on Render

Deploy three Render resources: a PostgreSQL database, a FastAPI web service,
and a Next.js web service. Use the same Render region for the API and database.

1. Connect `DenxVil/Computer-Assisted-Learning-` to Render. Use
   `web-migration` for a preview deployment; after the pull request is merged,
   switch both web services to `main` for production.
2. Create a Render PostgreSQL database. Copy its **internal** connection URL.
3. Create the API as a Python web service. Leave Root Directory blank so the
   service can import the shared `integrated_modules` package from the repo
   root. Set:

   - Build command: `pip install -r web/backend/requirements.txt`
   - Start command: `uvicorn web.backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/health`
   - `PYTHON_VERSION`: `3.12.10`
   - `DATABASE_URL`: the database's internal URL
   - `CORS_ORIGINS`: `http://localhost:3000` temporarily

   The backend normalizes Render's `postgresql://` URL to the installed
   Psycopg 3 SQLAlchemy driver automatically.
4. Create the frontend as a Node web service. Set Root Directory to
   `web/frontend`, then configure:

   - Build command: `pnpm install --frozen-lockfile && pnpm build`
   - Start command: `pnpm start`
   - `NODE_VERSION`: `24.21.0`
   - `NEXT_PUBLIC_API_URL`: `https://<your-api-service>.onrender.com`

5. After Render assigns the frontend URL, update the API's `CORS_ORIGINS` to
   that exact HTTPS origin, without a trailing slash. Add your custom domain
   there too if you use one, then redeploy the API.
6. Open the frontend URL, administer a dose, and check the API at
   `https://<your-api-service>.onrender.com/docs`.

Keep database credentials in Render environment variables. Use the database's
internal URL for the API when both resources are in the same region.
