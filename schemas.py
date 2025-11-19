"""
Database Schemas for RUVA

Each Pydantic model maps to a MongoDB collection (lowercased class name).
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password or guest token")
    is_guest: bool = Field(False, description="Guest account flag")
    plan: Literal["free", "weekly", "monthly", "yearly"] = Field("free")


class UserInput(BaseModel):
    user_id: str
    face_photo_url: Optional[str] = Field(None, description="URL to uploaded face photo")
    height_cm: Optional[int] = Field(None, ge=100, le=250)
    weight_kg: Optional[float] = Field(None, ge=30, le=250)
    age: Optional[int] = Field(None, ge=13, le=100)
    goals: Optional[str] = None
    style_vibe: Optional[str] = Field(None, description="e.g., classic, street, minimal")


class AnalysisSummary(BaseModel):
    user_id: str
    face_summary: str
    physique_summary: str
    style_summary: str
    outfit_summary: str


class LookmaxxingDetail(BaseModel):
    user_id: str
    face_shape: str
    strong_features: List[str] = []
    weak_features: List[str] = []
    grooming: List[str] = []
    hairstyle: List[str] = []
    accessories: List[str] = []


class PhysiquePlan(BaseModel):
    user_id: str
    body_type: str
    workout_7_day: List[str] = []
    posture_cues: List[str] = []
    diet_notes: List[str] = []


class StylingPlan(BaseModel):
    user_id: str
    daily_outfits: List[str] = []
    colours: List[str] = []
    wardrobe_essentials: List[str] = []
    hairstyle_synergy: List[str] = []


class GlowUpPlan(BaseModel):
    user_id: str
    week_by_week: List[str] = []


# Simple pricing schema (reference only)
class Pricing(BaseModel):
    tier: Literal["weekly", "monthly", "yearly"]
    price: int
