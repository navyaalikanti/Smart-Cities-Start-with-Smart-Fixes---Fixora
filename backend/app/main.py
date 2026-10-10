import os
import re
import logging
import threading
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Literal, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from .nlp_engine import nlp

load_dotenv()
logger = logging.getLogger("fixora.uploads")

DEPARTMENTS = ["Road Management", "Transport Management", "Water Management", "Waste Management", "Electricity Management", "Public Safety", "Parks & Recreation", "Drainage & Sewerage", "Street Lighting", "Public Buildings"]
# Department routing and duplicate detection live in nlp_engine.py (TF-IDF + Logistic Regression).


mongo_url = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI")
if mongo_url:
    _client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = _client[os.getenv("MONGODB_DATABASE", "fixora")]
    users, issues = db.users, db.issues
    users.create_index("email", unique=True)
    issues.create_index([("latitude", 1), ("longitude", 1)])
    issues.create_index([("department", 1), ("area", 1), ("status", 1)])
else:
    db = None
    users = issues = None

app = FastAPI(title="Fixora Civic Response API", version="1.0.0", description="Civic issue reporting, intelligent routing, and city response workflows.")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class RegisterBody(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["citizen", "official", "worker"]
    department: Optional[str] = None
    area: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

class LoginBody(BaseModel):
    email: EmailStr
    password: str
    role: Literal["citizen", "official", "worker"]

class IssueBody(BaseModel):
    title: str = Field(min_length=4, max_length=120)
    description: str = Field(min_length=8, max_length=3000)
    address: Optional[str] = Field(default=None, max_length=300)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    photo_url: Optional[str] = None

class AssignBody(BaseModel):
    worker_id: str

class ResolveBody(BaseModel):
    photo_url: Optional[str] = None

def require_db():
    if db is None:
        raise HTTPException(503, "Set MONGODB_URL in backend/.env to enable the API database.")

def clean_user(doc):
    return {"id": str(doc["_id"]), "name": doc["name"], "email": doc["email"], "role": doc["role"], "department": doc.get("department"), "area": doc.get("area"), "latitude": doc.get("service_latitude"), "longitude": doc.get("service_longitude"), "service_radius_m": doc.get("service_radius_m", 5000)}

def token_for(user):
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(503, "Set JWT_SECRET_KEY in backend/.env before using authentication.")
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user["_id"]), "iat": now, "exp": now + timedelta(hours=int(os.getenv("JWT_EXPIRE_HOURS", "24")))}, secret, algorithm="HS256")

def current_user(token: str = Depends(oauth_scheme)):
    require_db()
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY", ""), algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session is invalid or expired.")
    user = users.find_one({"_id": __import__("bson").ObjectId(user_id)})
    if not user:
        raise HTTPException(401, "Account not found.")
    return user

def require_role(*roles):
    def check(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, "Your account does not have access to this action.")
        return user
    return check

def classify(title, description):
    department, confidence = nlp.classify(title, description)
    return department, round(confidence, 4)

def retrain_classifier():
    """Learn from real resolved issues (their department was handled successfully)."""
    if issues is None:
        return
    try:
        rows = issues.find({"status": {"$in": ["resolved", "closed"]}}, {"title": 1, "description": 1, "department": 1}).limit(5000)
        nlp.train([(r.get("title", ""), r.get("description", ""), r.get("department")) for r in rows])
    except Exception:
        logger.exception("Classifier retraining skipped")

@app.on_event("startup")
def _startup_train():
    retrain_classifier()

def distance_m(a_lat, a_lon, b_lat, b_lon):
    earth = 6371000
    dlat, dlon = radians(b_lat - a_lat), radians(b_lon - a_lon)
    x = sin(dlat/2)**2 + cos(radians(a_lat))*cos(radians(b_lat))*sin(dlon/2)**2
    return 2 * earth * asin(sqrt(x))

def issue_matches_service_area(issue, account):
    latitude, longitude = issue.get("latitude"), issue.get("longitude")
    service_latitude = account.get("service_latitude")
    service_longitude = account.get("service_longitude")
    radius = float(account.get("service_radius_m", 5000))
    if latitude is not None and longitude is not None and service_latitude is not None and service_longitude is not None:
        if distance_m(latitude, longitude, service_latitude, service_longitude) <= radius:
            return True
    area = (account.get("area") or "").strip()
    address = (issue.get("address") or "").strip()
    stored_area = (issue.get("area") or "").strip()
    return bool(area and (stored_area.casefold() == area.casefold() or (address and re.search(rf"(?<!\w){re.escape(area)}(?!\w)", address, re.IGNORECASE))))

def issue_dict(doc, viewer=None):
    created_at = doc.get("created_at")
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    upvotes = doc.get("upvotes")
    if not isinstance(upvotes, list):
        upvotes = []
    result = {
        "id": str(doc.get("_id", "")),
        "title": doc.get("title", ""),
        "description": doc.get("description", ""),
        "address": doc.get("address"),
        # Legacy reports may not have coordinates. Keep them unknown instead of
        # assigning a false location; the UI can still display the rest of the report.
        "latitude": doc.get("latitude"),
        "longitude": doc.get("longitude"),
        "photo_url": doc.get("photo_url"),
        "resolution_photo_url": doc.get("resolution_photo_url"),
        "department": doc.get("department"),
        "area": doc.get("area"),
        "status": doc.get("status", "submitted"),
        "upvotes": len(upvotes),
        "assigned_worker_id": doc.get("assigned_worker_id"),
        "assigned_worker_name": doc.get("assigned_worker_name"),
        "created_at": created_at,
        "updates": doc.get("updates") or [],
    }
    if viewer:
        result["upvoted"] = viewer in upvotes
    return result

def visible_filter(user):
    if user["role"] == "official":
        f = {"department": user.get("department")}
        service_latitude = user.get("service_latitude")
        service_longitude = user.get("service_longitude")
        clauses = []
        if service_latitude is not None and service_longitude is not None:
            radius = float(user.get("service_radius_m", 5000))
            lat_delta = radius / 111000
            lon_delta = radius / max(1000, 111000 * cos(radians(service_latitude)))
            clauses.append({"latitude": {"$gte": service_latitude - lat_delta, "$lte": service_latitude + lat_delta}, "longitude": {"$gte": service_longitude - lon_delta, "$lte": service_longitude + lon_delta}})
        if user.get("area"):
            clauses.append({"address": {"$regex": rf"(?<!\w){re.escape(user['area'].strip())}(?!\w)", "$options": "i"}})
            clauses.append({"area": user["area"]})
        if clauses:
            f["$or"] = clauses
        return f
    if user["role"] == "worker":
        return {"assigned_worker_id": str(user["_id"])}
    return {}

@app.get("/health")
def health():
    return {"status": "ok", "database_configured": db is not None, "departments": DEPARTMENTS}

@app.post("/auth/register")
def register(body: RegisterBody):
    require_db()
    if body.role != "citizen":
        if body.department not in DEPARTMENTS:
            raise HTTPException(422, "Select a valid department.")
        if not body.area or len(body.area.strip()) < 2:
            raise HTTPException(422, "Officials and workers must provide a service area.")
        if body.latitude is None or body.longitude is None:
            raise HTTPException(422, "Officials and workers must pin their service location on the map.")
    doc = {"name": body.name.strip(), "email": body.email.lower(), "password_hash": pwd_context.hash(body.password), "role": body.role, "department": body.department if body.role != "citizen" else None, "area": body.area.strip() if body.role != "citizen" and body.area else None, "service_latitude": body.latitude if body.role != "citizen" else None, "service_longitude": body.longitude if body.role != "citizen" else None, "service_radius_m": float(os.getenv("SERVICE_AREA_RADIUS_METERS", "5000")) if body.role != "citizen" else None, "created_at": datetime.now(timezone.utc)}
    try:
        doc["_id"] = users.insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise HTTPException(409, "An account with this email already exists.")
    return {"access_token": token_for(doc), "token_type": "bearer", "user": clean_user(doc)}

@app.post("/auth/login")
def login(body: LoginBody):
    require_db()
    user = users.find_one({"email": body.email.lower()})
    if not user or not pwd_context.verify(body.password, user["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    if user["role"] != body.role:
        raise HTTPException(403, f"This account is registered as {user['role']}.")
    return {"access_token": token_for(user), "token_type": "bearer", "user": clean_user(user)}

@app.get("/auth/me")
def me(user=Depends(current_user)):
    return clean_user(user)

@app.post("/issues/check-similar")
def check_similar(body: IssueBody, user=Depends(require_role("citizen"))):
    require_db()
    candidates = list(issues.find({"status": {"$nin": ["resolved", "closed"]}, "latitude": {"$gte": body.latitude - .02, "$lte": body.latitude + .02}, "longitude": {"$gte": body.longitude - .02, "$lte": body.longitude + .02}}).limit(200))
    if not candidates:
        return {"matches": []}
    similarities = nlp.similarities(body.title, body.description, [(d["title"], d["description"]) for d in candidates])
    matches = []
    for doc, similarity in zip(candidates, similarities):
        distance = distance_m(body.latitude, body.longitude, doc["latitude"], doc["longitude"])
        # Semantic overlap and proximity are both required. Scores are TF-IDF cosine similarity.
        if similarity >= float(os.getenv("DUPLICATE_TEXT_THRESHOLD", ".40")) and distance <= float(os.getenv("DUPLICATE_RADIUS_METERS", "500")):
            item = issue_dict(doc, str(user["_id"]))
            item["distance_m"] = distance
            item["similarity"] = round(float(similarity), 3)
            matches.append(item)
    matches.sort(key=lambda d: (d["distance_m"], -d["similarity"]))
    return {"matches": matches[:5]}

@app.post("/issues", status_code=201)
def create_issue(body: IssueBody, user=Depends(require_role("citizen"))):
    require_db()
    department, confidence = classify(body.title, body.description)
    now = datetime.now(timezone.utc)
    doc = {"title": body.title.strip(), "description": body.description.strip(), "address": body.address.strip() if body.address else None, "latitude": body.latitude, "longitude": body.longitude, "photo_url": body.photo_url, "department": department, "classification_confidence": confidence, "area": user.get("area"), "reporter_id": str(user["_id"]), "status": "submitted", "upvotes": [], "created_at": now, "updated_at": now, "updates": [{"status": "submitted", "message": f"Report submitted and routed to {department}.", "at": now.isoformat()}]}
    doc["_id"] = issues.insert_one(doc).inserted_id
    return issue_dict(doc, str(user["_id"]))

@app.get("/issues")
def list_issues(q: Optional[str] = None, status_filter: Optional[str] = None, user=Depends(current_user)):
    require_db()
    query = visible_filter(user)
    if status_filter:
        query["status"] = status_filter
    if user["role"] == "citizen":
        query["status"] = {"$ne": "closed"}
    if q and q.strip():
        pattern = re.escape(q.strip())
        search_clause = {"$or": [{k: {"$regex": pattern, "$options": "i"}} for k in ("title", "description", "address")]}
        query = {"$and": [query, search_clause]} if "$or" in query else {**query, **search_clause}
    docs = list(issues.find(query).sort("created_at", -1).limit(500))
    if user["role"] == "official":
        docs = [doc for doc in docs if issue_matches_service_area(doc, user)]
    return [issue_dict(d, str(user["_id"])) for d in docs]

@app.get("/issues/mine")
def my_issues(user=Depends(require_role("citizen"))):
    require_db()
    docs = issues.find({"reporter_id": str(user["_id"])}).sort("created_at", -1).limit(500)
    return [issue_dict(d, str(user["_id"])) for d in docs]

@app.get("/issues/upvoted")
def upvoted_issues(user=Depends(require_role("citizen"))):
    require_db()
    docs = issues.find({"upvotes": str(user["_id"]), "status": {"$ne": "closed"}}).sort("updated_at", -1).limit(500)
    return [issue_dict(d, str(user["_id"])) for d in docs]

@app.get("/issues/assigned")
def assigned_issues(user=Depends(require_role("worker"))):
    require_db()
    docs = issues.find({"assigned_worker_id": str(user["_id"])}).sort("updated_at", -1).limit(500)
    return [issue_dict(d, str(user["_id"])) for d in docs]

@app.get("/workers")
def list_workers(user=Depends(require_role("official"))):
    require_db()
    query = {"role": "worker", "department": user.get("department"), "area": user.get("area")}
    return [{"id": str(w["_id"]), "name": w["name"], "department": w["department"], "area": w["area"]} for w in users.find(query).sort("name", 1)]


@app.post("/issues/{issue_id}/upvote")
def upvote(issue_id: str, user=Depends(require_role("citizen"))):
    require_db()

    from bson import ObjectId

    try:
        oid = ObjectId(issue_id)
    except Exception:
        raise HTTPException(404, "Issue not found.")

    user_id = str(user["_id"])

    result = issues.find_one_and_update(
        {
            "_id": oid,
            "status": {"$nin": ["resolved", "closed"]}
        },
        [
            {
                "$set": {
                    "upvotes": {
                        "$cond": [
                            {
                                "$in": [
                                    user_id,
                                    {"$ifNull": ["$upvotes", []]}
                                ]
                            },
                            {
                                "$filter": {
                                    "input": {"$ifNull": ["$upvotes", []]},
                                    "as": "v",
                                    "cond": {"$ne": ["$$v", user_id]}
                                }
                            },
                            {
                                "$concatArrays": [
                                    {"$ifNull": ["$upvotes", []]},
                                    [user_id]
                                ]
                            }
                        ]
                    },
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        ],
        return_document=ReturnDocument.AFTER
    )

    if not result:
        raise HTTPException(404, "Open issue not found.")

    return issue_dict(result, user_id)


@app.post("/issues/{issue_id}/assign")
def assign_issue(issue_id: str, body: AssignBody, user=Depends(require_role("official"))):
    require_db()
    from bson import ObjectId
    try:
        oid = ObjectId(issue_id)
    except Exception:
        raise HTTPException(404, "Issue not found.")
    issue = issues.find_one({"_id": oid, "department": user.get("department")})
    worker = users.find_one({"_id": ObjectId(body.worker_id), "role": "worker", "department": user.get("department"), "area": user.get("area")})
    if not issue:
        raise HTTPException(404, "Issue not found in your department.")
    if not issue_matches_service_area(issue, user):
        raise HTTPException(403, "This issue is outside your pinned service location and area.")
    if not worker:
        raise HTTPException(400, "Choose a worker in your department and service area.")
    if not issue_matches_service_area(issue, worker):
        raise HTTPException(400, "Choose a worker whose pinned service location covers this issue.")
    now = datetime.now(timezone.utc)
    update = {"assigned_worker_id": str(worker["_id"]), "assigned_worker_name": worker["name"], "status": "assigned", "updated_at": now}
    issues.update_one({"_id": oid}, {"$set": update, "$push": {"updates": {"status": "assigned", "message": f"Assigned to {worker['name']}.", "at": now.isoformat()}}})
    return {"ok": True, **update}

@app.post("/issues/{issue_id}/resolve")
def resolve_issue(issue_id: str, body: ResolveBody, user=Depends(require_role("worker"))):
    require_db()
    from bson import ObjectId
    try:
        oid = ObjectId(issue_id)
    except Exception:
        raise HTTPException(404, "Issue not found.")
    issue = issues.find_one({"_id": oid, "assigned_worker_id": str(user["_id"]), "department": user.get("department")})
    if not issue or not issue_matches_service_area(issue, user):
        raise HTTPException(404, "Assignment not found for your account and area.")
    if not body.photo_url:
        raise HTTPException(422, "Upload a resolution photo before submitting the repair.")
    now = datetime.now(timezone.utc)
    issues.update_one({"_id": oid}, {"$set": {"status": "resolved", "resolution_photo_url": body.photo_url, "updated_at": now}, "$push": {"updates": {"status": "resolved", "message": "Worker uploaded the resolution photo.", "at": now.isoformat()}}})
    threading.Thread(target=retrain_classifier, daemon=True).start()
    return {"ok": True, "status": "resolved", "resolution_photo_url": body.photo_url}

@app.post("/uploads")
async def upload_photo(file: UploadFile = File(...), user=Depends(current_user)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Upload a JPG, PNG, or WebP image.")
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image exceeds the 10 MB upload limit.")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    bucket = os.getenv("SUPABASE_BUCKET", "fixora-photos")
    if not url or not key:
        raise HTTPException(503, "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env to enable photo uploads.")
    path = None
    try:
        from supabase import create_client
        client = create_client(url, key)
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
        path = f"{user['role']}/{uuid4().hex}{suffix}"
        client.storage.from_(bucket).upload(path, data, {"content-type": file.content_type, "upsert": "false"})
        return {"url": client.storage.from_(bucket).get_public_url(path), "path": path}
    except Exception as exc:
        detail = str(exc).strip() or "No error detail was provided by Supabase Storage."
        detail = detail.replace(key, "[redacted]")
        logger.exception("Supabase Storage upload failed for bucket '%s' (path=%s)", bucket, path or "not created")
        lower_detail = detail.lower()
        if "bucket not found" in lower_detail or "bucket does not exist" in lower_detail:
            detail = f"Storage bucket '{bucket}' was not found. Create that bucket in Supabase Storage or set SUPABASE_BUCKET to its exact name."
        elif "row-level security" in lower_detail or "permission denied" in lower_detail:
            detail = f"Supabase denied the upload to bucket '{bucket}'. Check that SUPABASE_SERVICE_ROLE_KEY is the project's service role/secret key and that the bucket allows uploads."
        elif "invalid jwt" in lower_detail or "invalid api key" in lower_detail or "unauthorized" in lower_detail:
            detail = "Supabase rejected the configured key. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env, then restart FastAPI."
        else:
            detail = f"Upload to Supabase bucket '{bucket}' failed ({type(exc).__name__}): {detail[:300]}"
        raise HTTPException(502, detail)
