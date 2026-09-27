# CAL Lab web application

The web app adds four browser-based pharmacology practicals beside the original desktop application. Desktop source files and launchers remain in place.

## Experiments

- **Dog Blood Pressure** — the existing dose-response model, drug presets and ranges, continuous systolic/diastolic pressure and heart-rate traces, blocker-before-agonist studies, Dale reversal, ephedrine tachyphylaxis, interpretation and an observation log.
- **Rabbit Eye** — drug administration to either eye with a saline control in the other; ruler, torch, cotton-swab, conjunctiva and ocular-tone examinations; student comparison notebook, session restore, CSV/PNG exports, and theory/practical guidance.
- **Frog Rectus Abdominis** — the integrated desktop engine's concentration conversion, agonist response, d-tubocurarine competitive antagonism, live organ-bath and wash traces, observation log, dose-response curves and EC50/Emax guides.
- **Acetylcholine Bioassay** — server-held teacher unknown, standard/unknown dosing, wash traces, student estimate, interpolation, three-point and four-point methods, calculation diagnostics, and PNG results.

The Frog Rectus and bioassay calculations preserve their source Hill models and dose selection. The Dog BP and Rabbit Eye pages use their existing desktop model constants and drug effects. The unknown bioassay stock concentration is stored and used only by the backend.

## Local start

From the repository root, run:

```sh
docker compose up --build
```

Open `http://localhost:3000`. FastAPI docs are at `http://localhost:8000/docs`. PostgreSQL stores Frog Rectus observations and the hidden bioassay sample. Rabbit Eye notebook drafts use browser local storage.

## Render deployment

This is a monorepo deployment with a PostgreSQL database, a FastAPI web service and a Next.js web service. Deploy all three from the `web-migration` branch for preview. The current `CalFront` and `CalAPI` Render services are configured to deploy `main`; switch their branch to `web-migration` in each service's **Settings → Build & Deploy → Branch** before deploying the new version. This keeps the GitHub `main` branch unchanged. Use the same Render region for the API and database.

### 1. PostgreSQL

Create a PostgreSQL database in Render, choose a plan that fits your data-retention needs, and copy its **Internal Database URL**. Keep it private.

### 2. FastAPI service

Use the repository `DenxVil/Computer-Assisted-Learning-`, branch `web-migration`, and leave **Root Directory** blank so the app can import the shared model packages. Configure:

- Build: `pip install -r web/backend/requirements.txt`
- Start: `uvicorn web.backend.app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- `PYTHON_VERSION`: `3.12.10`
- `DATABASE_URL`: the database's internal URL
- `CORS_ORIGINS`: the frontend's HTTPS origin (set after step 3)

The API normalizes Render's PostgreSQL URL for Psycopg 3.

### 3. Next.js service

Use the same repository and branch. Set **Root Directory** to `web/frontend` and configure:

- Build: `pnpm install --frozen-lockfile && pnpm build`
- Start: `pnpm start`
- `NODE_VERSION`: `24.21.0`
- `NEXT_PUBLIC_API_URL`: the FastAPI service URL, such as `https://calapi-pwv2.onrender.com`

Do not run `corepack enable` in the build command; Render's system pnpm path can be read-only.

### 4. Connect and verify

Set the API's `CORS_ORIGINS` to the exact frontend origin, without a trailing slash, then redeploy the API. Open the frontend and visit all four cards. Check the API health at `/health` and docs at `/docs`.

The web services currently on `main` serve the earlier Frog Rectus foundation. They need the `web-migration` branch selection and a successful deploy before the four-module site is live. After review and merge, both services may be switched back to `main`.

