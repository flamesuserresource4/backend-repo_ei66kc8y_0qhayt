import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from database import db, create_document, get_documents
from schemas import (
    User, UserInput, AnalysisSummary, LookmaxxingDetail,
    PhysiquePlan, StylingPlan, GlowUpPlan
)

app = FastAPI(title="RUVA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "RUVA", "status": "ok"}


# Auth models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GuestLoginRequest(BaseModel):
    email: EmailStr


# -------- Authentication (minimal, not production-grade) --------
@app.post("/auth/signup")
def signup(payload: SignupRequest):
    try:
        existing = get_documents("user", {"email": payload.email}, limit=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(email=payload.email, password_hash=f"hash:{payload.password}", is_guest=False)
    user_id = create_document("user", user)
    return {"user_id": user_id, "email": payload.email}


@app.post("/auth/login")
def login(payload: LoginRequest):
    try:
        users = get_documents("user", {"email": payload.email}, limit=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not users:
        raise HTTPException(status_code=404, detail="User not found")
    user = users[0]
    if user.get("password_hash") != f"hash:{payload.password}":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": str(user.get("_id")), "email": user.get("email")}


@app.post("/auth/guest")
def guest_login(payload: GuestLoginRequest):
    user = User(email=payload.email, password_hash="guest", is_guest=True)
    user_id = create_document("user", user)
    return {"user_id": user_id, "email": payload.email, "guest": True}


# -------- User Input --------
@app.post("/input")
def save_user_input(data: UserInput):
    doc_id = create_document("userinput", data)
    return {"input_id": doc_id}


# -------- AI Workflow stubs (rule-based placeholders) --------
def make_face_analysis(data: Dict[str, Any]) -> LookmaxxingDetail:
    return LookmaxxingDetail(
        user_id=data["user_id"],
        face_shape="oval",
        strong_features=["defined jawline"],
        weak_features=["under-eye puffiness"],
        grooming=["weekly exfoliation", "SPF 50 daily"],
        hairstyle=["medium length textured crop"],
        accessories=["thin metal frames", "minimalist studs"],
    )


def make_physique_plan(data: Dict[str, Any]) -> PhysiquePlan:
    return PhysiquePlan(
        user_id=data["user_id"],
        body_type="athletic",
        workout_7_day=[
            "Push strength",
            "Pull strength",
            "Legs + core",
            "Active recovery (walk + mobility)",
            "Upper hypertrophy",
            "Lower hypertrophy",
            "Rest + stretch",
        ],
        posture_cues=["neck long", "ribs down", "glutes on"],
        diet_notes=["high protein", "2L water", "500 kcal deficit (if fat loss)"]
    )


def make_styling_plan(data: Dict[str, Any]) -> StylingPlan:
    return StylingPlan(
        user_id=data["user_id"],
        daily_outfits=["monochrome black smart-casual", "cream knit + tapered chinos"],
        colours=["cream", "black", "light gold"],
        wardrobe_essentials=["white sneakers", "dark denim", "oxford shirt"],
        hairstyle_synergy=["texture complements jawline"]
    )


def make_glow_up(data: Dict[str, Any]) -> GlowUpPlan:
    return GlowUpPlan(
        user_id=data["user_id"],
        week_by_week=[
            "Week 1: skin baseline + haircut",
            "Week 2: posture daily 10m + wardrobe audit",
            "Week 3: gym routine locked",
            "Week 4: social refresh (bio/photos)",
            "Weeks 5-12: progressions + photos",
        ],
    )


def make_summary(face: LookmaxxingDetail, phys: PhysiquePlan, style: StylingPlan) -> AnalysisSummary:
    return AnalysisSummary(
        user_id=face.user_id,
        face_summary=f"Face shape {face.face_shape}; groom: {', '.join(face.grooming)}",
        physique_summary=f"Body {phys.body_type}; posture: {', '.join(phys.posture_cues)}",
        style_summary=f"Colours: {', '.join(style.colours)}",
        outfit_summary=f"Outfits: {', '.join(style.daily_outfits)}",
    )


class WorkflowRequest(BaseModel):
    user_id: str


@app.post("/workflow/run")
def run_workflow(req: WorkflowRequest):
    try:
        inputs = get_documents("userinput", {"user_id": req.user_id}, limit=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    base = inputs[0] if inputs else {"user_id": req.user_id}

    face = make_face_analysis(base)
    phys = make_physique_plan(base)
    style = make_styling_plan(base)
    glow = make_glow_up(base)
    summary = make_summary(face, phys, style)

    # Persist summaries
    create_document("lookmaxxingdetail", face)
    create_document("physiqueplan", phys)
    create_document("stylingplan", style)
    create_document("glowupplan", glow)
    create_document("analysissummary", summary)

    return {
        "summary": summary.model_dump(),
        "face": face.model_dump(),
        "physique": phys.model_dump(),
        "styling": style.model_dump(),
        "glow": glow.model_dump(),
    }


@app.get("/summary/{user_id}")
def get_latest_summary(user_id: str):
    try:
        docs = get_documents("analysissummary", {"user_id": user_id}, limit=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not docs:
        raise HTTPException(status_code=404, detail="No summary yet")
    doc = docs[0]
    # Convert ObjectId to str safely
    doc["_id"] = str(doc.get("_id"))
    return doc


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Env
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
