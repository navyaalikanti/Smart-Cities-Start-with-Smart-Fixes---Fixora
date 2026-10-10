# Fixora — Smart city fixes, made visible

Fixora is a civic issue reporting and response platform. Residents report problems in their city; the right department reviews and assigns the work; field workers document the resolution. Citizens and city teams can follow progress in one place.

## What Fixora includes

- Separate registration and sign-in flows for citizens, city officials, and field workers.
- Department and service-area selection for officials and workers, including a mapped service location.
- Citizen reports with a title, description, optional photo and address, and a map pin that can use the device's current location.
- Department queues scoped to service areas, worker assignment, issue status updates, and resolution photos.
- Citizen report history, citywide report search, issue upvotes, and visibility into report progress.
- A Leaflet map for city teams, with issue markers that grow darker as reports receive more upvotes.
- React frontend, FastAPI backend, MongoDB Atlas persistence, and Supabase photo storage.

## NLP-powered department routing

Citizens never choose a department. `backend/app/nlp_engine.py` runs a trained statistical model:

- **Features:** TF-IDF over words and two-word phrases, plus character 3-5 grams (so typos and unseen wording still match).
- **Model:** multinomial Logistic Regression trained on `backend/app/nlp_seed.py` (about 250 labelled example reports across the ten departments).
- **Self-improving:** at server start, and after every repair a worker marks resolved, the model is retrained with the real resolved issues stored in MongoDB.
- **Confidence:** the predicted probability is stored on each issue as `classification_confidence`.

There are no keyword lists or if/else rules. To improve accuracy for your city, add more example sentences per department to `nlp_seed.py`.

## Similar report suggestions

Before submitting, the new report is compared with open issues nearby (same TF-IDF feature space as the classifier, so word weights are stable) using cosine similarity. A report is suggested as a duplicate only when text similarity reaches `DUPLICATE_TEXT_THRESHOLD` (default 0.40) and it is within `DUPLICATE_RADIUS_METERS` (default 500). The citizen can then upvote the existing issue or submit anyway.

## Technology

- **Frontend:** React, Vite, Leaflet, React Leaflet, Lucide icons
- **API:** FastAPI, Uvicorn
- **Database:** MongoDB Atlas via PyMongo
- **NLP:** scikit-learn TF-IDF + Logistic Regression, cosine similarity
- **Photo storage:** Supabase Storage

## Run locally

### Requirements

- Python 3.10 or newer
- Node.js and npm
- MongoDB Atlas connection string
- Supabase project and Storage bucket

### 1. Configure the backend

From the project root:

```powershell
Copy-Item backend/.env.example backend/.env
```

Set the values in `backend/.env`:

| Variable | Purpose |
| --- | --- |
| `MONGODB_URL` | MongoDB Atlas connection string |
| `MONGODB_DATABASE` | Database name (defaults to `fixora`) |
| `JWT_SECRET_KEY` | Long, private signing secret |
| `CORS_ORIGINS` | Frontend origin, typically `http://localhost:5173` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Private backend-only Supabase service role key |
| `SUPABASE_BUCKET` | Storage bucket name (defaults to `fixora-photos`) |
| `DUPLICATE_TEXT_THRESHOLD` | Minimum TF-IDF cosine similarity for a duplicate suggestion |
| `DUPLICATE_RADIUS_METERS` | Maximum distance for a duplicate suggestion |
| `SERVICE_AREA_RADIUS_METERS` | Default official/worker service radius |

Create the configured Supabase Storage bucket and set its access policy to match the app's photo URL behavior. Keep `backend/.env` and the service role key private. Never put the Supabase service role key in frontend environment variables.

Install and start the API:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

FastAPI's interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Configure the frontend

In a second terminal, from the project root:

```powershell
Copy-Item frontend/.env.example frontend/.env
cd frontend
npm install
npm run dev
```

Open the local Vite URL printed in the terminal. `VITE_API_URL` should point to the FastAPI origin, such as `http://127.0.0.1:8000`, with no extra path prefix.

Create a production frontend build with:

```powershell
npm run build
```

## Departments

Fixora ships with ten department profiles covering core city services, including roads, transport, water, sanitation, drainage, electricity, parks, public safety, street lighting, and public facilities. The department list is defined in `backend/app/main.py`; training examples are in `backend/app/nlp_seed.py`.

## Service-area matching

Officials see reports assigned to their department and service area. Location coordinates are used with the configured service radius; area/address text is retained as a compatibility match where needed. Officials can assign reports to workers whose department and service area match. Worker accounts only receive reports assigned to them.

## Project structure

```text
backend/
  app/main.py       FastAPI routes, persistence, NLP routing, and matching
  requirements.txt
  .env.example
frontend/
  src/              React application and shared styling
  index.html
  package.json
  .env.example
```

## Data and deployment notes

- The app does not seed example users, issues, or dashboard statistics; views are populated from the database.
- Official and worker registration is open in this development scaffold. Add an approval process before using it for a public city deployment.
- Set the default map center in the frontend to the target city before launch.
- Review authentication, account onboarding, storage policies, CORS origins, and operational monitoring before production deployment.
