from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import jwt
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="Orienta API", description="South African Educational Guidance System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# AI Models Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# Data Models
class UserRole(str):
    LEARNER = "learner"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(default=UserRole.LEARNER)
    email: str
    phone: Optional[str] = None
    password_hash: Optional[str] = None
    school_id: Optional[str] = None
    consent_flags: Dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    role: str = Field(default=UserRole.LEARNER)

class UserLogin(BaseModel):
    email: str
    password: str

class LearnerProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    grade_level: Optional[int] = None
    province: Optional[str] = None
    subjects: List[Dict[str, Any]] = Field(default_factory=list)  # [{"subject": "Math", "mark_band": "70-80"}]
    aps_band: Optional[str] = None
    interest_tags: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)  # fees_band, distance_km, etc.
    target_fields: List[str] = Field(default_factory=list)
    language_pref: Optional[str] = None
    readiness_score: Optional[float] = None
    intake_completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Institution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # university, university_of_technology, tvet
    province: str
    city: str
    application_portal_url: Optional[str] = None
    fee_reference_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Programme(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    institution_id: str
    title: str
    faculty: str
    qualification_type: str
    province: str
    city: str
    duration_months: int
    total_estimated_cost: float
    entry_requirements: Dict[str, Any] = Field(default_factory=dict)  # aps_min, subject_minima
    source_url: Optional[str] = None
    last_verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    visible: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FundingOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # nsfas, bursary, scholarship, learnership
    provider_name: str
    income_thresholds: Dict[str, Any] = Field(default_factory=dict)
    eligibility: Dict[str, Any] = Field(default_factory=dict)
    deadline_date: Optional[str] = None
    application_url: Optional[str] = None
    documents_required: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    last_verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    visible: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Pathway(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    programme_id: str
    fit_score: float
    rationale: str
    projected_cost: float
    funding_shortlist: List[str] = Field(default_factory=list)  # funding_option ids
    status: str = Field(default="suggested")  # suggested, saved, applied
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class IntakeResponse(BaseModel):
    question_id: str
    question: str
    answer: Any
    progress: float

class IntakeSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    responses: List[IntakeResponse] = Field(default_factory=list)
    current_step: int = 0
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventsLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: str  # stripe or paystack
    amount_cents: int
    currency: str
    status: str  # initiated, pending, succeeded, failed
    external_ref: Optional[str] = None  # session_id from payment provider
    plan_type: str  # learner or premium
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Auth helpers
def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, os.environ['JWT_SECRET'], algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, os.environ['JWT_SECRET'], algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(user_id: str = Depends(verify_token)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# AI Chat helpers
async def get_ai_response(system_message: str, user_message: str, user_id: str):
    """Get AI response using emergentintegrations"""
    try:
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"orienta_{user_id}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_msg = UserMessage(text=user_message)
        response = await chat.send_message(user_msg)
        return response
    except Exception as e:
        logging.error(f"AI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service unavailable")

# Logging helper
async def log_event(event_type: str, payload: Dict[str, Any], user_id: Optional[str] = None):
    """Log events to events_log collection"""
    event = EventsLog(
        user_id=user_id,
        event_type=event_type,
        payload=payload
    )
    await db.events_log.insert_one(event.dict())

# Routes
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password_hash"] = pwd_context.hash(user_data.password)
    del user_dict["password"]
    user = User(**user_dict)
    
    await db.users.insert_one(user.dict())
    
    # Create learner profile if learner
    if user.role == UserRole.LEARNER:
        profile = LearnerProfile(user_id=user.id)
        await db.learner_profiles.insert_one(profile.dict())
    
    await log_event("user_registered", {"user_id": user.id, "role": user.role})
    
    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user}

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    """Login user"""
    user = await db.users.find_one({"email": user_data.email})
    if not user or not pwd_context.verify(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user["id"]})
    return {"access_token": token, "token_type": "bearer", "user": User(**user)}

@api_router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    if current_user.role == UserRole.LEARNER:
        profile = await db.learner_profiles.find_one({"user_id": current_user.id})
        if profile:
            return {"user": current_user, "profile": LearnerProfile(**profile)}
    return {"user": current_user}

@api_router.post("/intake/start")
async def start_intake(current_user: User = Depends(get_current_user)):
    """Start or resume intake process"""
    if current_user.role != UserRole.LEARNER:
        raise HTTPException(status_code=403, detail="Only learners can take intake")
    
    # Check for existing session
    session = await db.intake_sessions.find_one({"user_id": current_user.id, "completed": False})
    if not session:
        session_obj = IntakeSession(user_id=current_user.id)
        await db.intake_sessions.insert_one(session_obj.dict())
        await log_event("intake_started", {"user_id": current_user.id})
        return session_obj
    
    return IntakeSession(**session)

@api_router.post("/intake/answer")
async def submit_intake_answer(
    question_id: str,
    answer: Any,
    current_user: User = Depends(get_current_user)
):
    """Submit answer for intake question"""
    session = await db.intake_sessions.find_one({"user_id": current_user.id, "completed": False})
    if not session:
        raise HTTPException(status_code=404, detail="No active intake session")
    
    session_obj = IntakeSession(**session)
    
    # Define intake questions
    questions = [
        {"id": "grade", "text": "What grade are you currently in?", "type": "select"},
        {"id": "province", "text": "Which province are you in?", "type": "select"},
        {"id": "subjects", "text": "What are your subject marks?", "type": "subjects"},
        {"id": "interests", "text": "What are your career interests?", "type": "multiselect"},
        {"id": "budget", "text": "What is your estimated budget for studies?", "type": "range"},
        {"id": "location", "text": "How far are you willing to travel?", "type": "range"},
        {"id": "fields", "text": "Which fields of study interest you most?", "type": "multiselect"}
    ]
    
    # Find question
    question = next((q for q in questions if q["id"] == question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Add response
    response = IntakeResponse(
        question_id=question_id,
        question=question["text"],
        answer=answer,
        progress=(session_obj.current_step + 1) / len(questions) * 100
    )
    
    # Update session
    session_obj.responses.append(response)
    session_obj.current_step += 1
    session_obj.updated_at = datetime.now(timezone.utc)
    
    if session_obj.current_step >= len(questions):
        session_obj.completed = True
        await log_event("intake_completed", {"user_id": current_user.id})
        
        # Update learner profile
        await update_profile_from_intake(current_user.id, session_obj.responses)
    
    await db.intake_sessions.replace_one(
        {"id": session_obj.id}, 
        session_obj.dict()
    )
    
    return {
        "session": session_obj,
        "next_question": questions[session_obj.current_step] if session_obj.current_step < len(questions) else None
    }

async def update_profile_from_intake(user_id: str, responses: List[IntakeResponse]):
    """Update learner profile based on intake responses"""
    profile_updates = {
        "intake_completed": True,
        "updated_at": datetime.now(timezone.utc)
    }
    
    for response in responses:
        if response.question_id == "grade":
            profile_updates["grade_level"] = response.answer
        elif response.question_id == "province":
            profile_updates["province"] = response.answer
        elif response.question_id == "subjects":
            profile_updates["subjects"] = response.answer
        elif response.question_id == "interests":
            profile_updates["interest_tags"] = response.answer
        elif response.question_id == "budget":
            if "constraints" not in profile_updates:
                profile_updates["constraints"] = {}
            profile_updates["constraints"]["fees_band"] = response.answer
        elif response.question_id == "location":
            if "constraints" not in profile_updates:
                profile_updates["constraints"] = {}
            profile_updates["constraints"]["distance_km"] = response.answer
        elif response.question_id == "fields":
            profile_updates["target_fields"] = response.answer
    
    await db.learner_profiles.update_one(
        {"user_id": user_id},
        {"$set": profile_updates}
    )

@api_router.get("/intake/questions")
async def get_intake_questions():
    """Get all intake questions"""
    questions = [
        {
            "id": "grade",
            "text": "What grade are you currently in?",
            "type": "select",
            "options": ["Grade 11", "Grade 12", "Post-Matric"]
        },
        {
            "id": "province",
            "text": "Which province are you in?",
            "type": "select",
            "options": ["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State", "Limpopo", "Mpumalanga", "Northern Cape", "North West"]
        },
        {
            "id": "subjects",
            "text": "What are your subject marks (estimated for Grade 11)?",
            "type": "subjects",
            "subjects": ["Mathematics", "English", "Afrikaans", "Physical Sciences", "Life Sciences", "Accounting", "Business Studies", "Geography", "History", "Life Orientation"]
        },
        {
            "id": "interests",
            "text": "What are your career interests?",
            "type": "multiselect",
            "options": ["Medicine & Health", "Engineering", "Business & Finance", "Law", "Education", "Arts & Design", "Technology", "Social Work", "Agriculture", "Sports & Recreation"]
        },
        {
            "id": "budget",
            "text": "What is your estimated budget for studies per year?",
            "type": "select",
            "options": ["R0 - R20,000", "R20,000 - R50,000", "R50,000 - R100,000", "R100,000+"]
        },
        {
            "id": "location",
            "text": "How far are you willing to travel for studies?",
            "type": "select",
            "options": ["Same city", "Same province", "Anywhere in South Africa", "International"]
        },
        {
            "id": "fields",
            "text": "Which fields of study interest you most?",
            "type": "multiselect",
            "options": ["Science & Technology", "Commerce & Management", "Health Sciences", "Engineering", "Humanities", "Arts & Design", "Education", "Law", "Agriculture"]
        }
    ]
    return {"questions": questions}

@api_router.get("/pathways/preview")
async def get_pathway_preview(current_user: User = Depends(get_current_user)):
    """Get a single pathway preview (before payment)"""
    if current_user.role != UserRole.LEARNER:
        raise HTTPException(status_code=403, detail="Only learners can view pathways")
    
    profile = await db.learner_profiles.find_one({"user_id": current_user.id})
    if not profile or not profile.get("intake_completed"):
        raise HTTPException(status_code=400, detail="Complete intake first")
    
    # Get one sample programme
    sample_programme = await db.programmes.find_one({"visible": True})
    if not sample_programme:
        raise HTTPException(status_code=404, detail="No programmes available")
    
    institution = await db.institutions.find_one({"id": sample_programme["institution_id"]})
    
    return {
        "programme": Programme(**sample_programme),
        "institution": Institution(**institution) if institution else None,
        "preview_only": True,
        "message": "This is a preview. Unlock full pathway matching for R79."
    }

# Payment routes will be added here
@api_router.post("/payments/create-checkout")
async def create_checkout_session(
    request: Request,
    plan_type: str,  # "learner" or "premium"
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session"""
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    # Check if user already has paid access
    existing_payment = await db.payment_transactions.find_one({
        "user_id": current_user.id,
        "status": "succeeded"
    })
    if existing_payment:
        raise HTTPException(status_code=400, detail="Access already unlocked")
    
    # Define plans
    plans = {
        "learner": {"amount": 79.0, "currency": "ZAR"},
        "premium": {"amount": 129.0, "currency": "ZAR"}
    }
    
    if plan_type not in plans:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    plan = plans[plan_type]
    
    # Get origin from request
    origin = str(request.base_url).rstrip('/')
    
    try:
        # Initialize Stripe checkout
        webhook_url = f"{origin}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=plan["amount"],
            currency=plan["currency"],
            success_url=f"{origin}/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin}/",
            metadata={
                "user_id": current_user.id,
                "plan_type": plan_type
            }
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            user_id=current_user.id,
            provider="stripe",
            amount_cents=int(plan["amount"] * 100),
            currency=plan["currency"],
            status="initiated",
            external_ref=session.session_id,
            plan_type=plan_type
        )
        
        await db.payment_transactions.insert_one(transaction.dict())
        
        return {"checkout_url": session.url, "session_id": session.session_id}
        
    except Exception as e:
        logging.error(f"Payment creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment session")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_seed():
    """Seed database with initial data"""
    # Check if institutions exist
    if await db.institutions.count_documents({}) == 0:
        await seed_institutions()
    
    if await db.programmes.count_documents({}) == 0:
        await seed_programmes()
    
    if await db.funding_options.count_documents({}) == 0:
        await seed_funding_options()

async def seed_institutions():
    """Seed institutions data"""
    institutions = [
        {
            "id": str(uuid.uuid4()),
            "name": "University of the Witwatersrand",
            "type": "university",
            "province": "Gauteng",
            "city": "Johannesburg",
            "application_portal_url": "https://www.wits.ac.za/applications",
            "fee_reference_url": "https://www.wits.ac.za/fees",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "University of Johannesburg",
            "type": "university",
            "province": "Gauteng",
            "city": "Johannesburg",
            "application_portal_url": "https://www.uj.ac.za/apply",
            "fee_reference_url": "https://www.uj.ac.za/fees",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "University of Pretoria",
            "type": "university",
            "province": "Gauteng",
            "city": "Pretoria",
            "application_portal_url": "https://www.up.ac.za/applications",
            "fee_reference_url": "https://www.up.ac.za/fees",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "University of South Africa",
            "type": "university",
            "province": "Gauteng",
            "city": "Pretoria",
            "application_portal_url": "https://www.unisa.ac.za/apply",
            "fee_reference_url": "https://www.unisa.ac.za/fees",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Tshwane University of Technology",
            "type": "university_of_technology",
            "province": "Gauteng",
            "city": "Pretoria",
            "application_portal_url": "https://www.tut.ac.za/apply",
            "fee_reference_url": "https://www.tut.ac.za/fees",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    await db.institutions.insert_many(institutions)

async def seed_programmes():
    """Seed programmes data"""
    institutions = await db.institutions.find().to_list(length=None)
    
    programmes = []
    for institution in institutions:
        if "Wits" in institution["name"]:
            programmes.extend([
                {
                    "id": str(uuid.uuid4()),
                    "institution_id": institution["id"],
                    "title": "Bachelor of Engineering in Electrical Engineering",
                    "faculty": "Engineering",
                    "qualification_type": "Bachelor's Degree",
                    "province": institution["province"],
                    "city": institution["city"],
                    "duration_months": 48,
                    "total_estimated_cost": 280000.0,
                    "entry_requirements": {
                        "aps_min": 38,
                        "subject_minima": {
                            "Mathematics": 6,
                            "Physical Sciences": 5,
                            "English": 4
                        }
                    },
                    "source_url": "https://www.wits.ac.za/engineering",
                    "last_verified_at": datetime.now(timezone.utc),
                    "visible": True,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": str(uuid.uuid4()),
                    "institution_id": institution["id"],
                    "title": "Bachelor of Commerce in Accounting",
                    "faculty": "Commerce",
                    "qualification_type": "Bachelor's Degree",
                    "province": institution["province"],
                    "city": institution["city"],
                    "duration_months": 36,
                    "total_estimated_cost": 210000.0,
                    "entry_requirements": {
                        "aps_min": 32,
                        "subject_minima": {
                            "Mathematics": 5,
                            "English": 4,
                            "Accounting": 5
                        }
                    },
                    "source_url": "https://www.wits.ac.za/commerce",
                    "last_verified_at": datetime.now(timezone.utc),
                    "visible": True,
                    "created_at": datetime.now(timezone.utc)
                }
            ])
        elif "UJ" in institution["name"]:
            programmes.extend([
                {
                    "id": str(uuid.uuid4()),
                    "institution_id": institution["id"],
                    "title": "Bachelor of Education in Foundation Phase",
                    "faculty": "Education",
                    "qualification_type": "Bachelor's Degree",
                    "province": institution["province"],
                    "city": institution["city"],
                    "duration_months": 48,
                    "total_estimated_cost": 160000.0,
                    "entry_requirements": {
                        "aps_min": 26,
                        "subject_minima": {
                            "English": 4,
                            "Mathematics": 3
                        }
                    },
                    "source_url": "https://www.uj.ac.za/education",
                    "last_verified_at": datetime.now(timezone.utc),
                    "visible": True,
                    "created_at": datetime.now(timezone.utc)
                }
            ])
    
    if programmes:
        await db.programmes.insert_many(programmes)

async def seed_funding_options():
    """Seed funding options data"""
    funding_options = [
        {
            "id": str(uuid.uuid4()),
            "name": "NSFAS",
            "type": "nsfas",
            "provider_name": "National Student Financial Aid Scheme",
            "income_thresholds": {"household_income": 350000},
            "eligibility": {
                "citizenship": "South African",
                "academic_merit": "APS 23+",
                "fields": "All"
            },
            "deadline_date": "2024-12-31",
            "application_url": "https://www.nsfas.org.za/apply",
            "documents_required": ["ID Document", "Proof of Income", "Academic Records"],
            "source_url": "https://www.nsfas.org.za",
            "last_verified_at": datetime.now(timezone.utc),
            "visible": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Funza Lushaka Bursary",
            "type": "bursary",
            "provider_name": "Department of Basic Education",
            "income_thresholds": {"household_income": 500000},
            "eligibility": {
                "field": "Education",
                "aps_min": 25,
                "commitment": "Teaching for same period as study"
            },
            "deadline_date": "2024-11-30",
            "application_url": "https://www.funzalushaka.doe.gov.za",
            "documents_required": ["ID Document", "Academic Records", "Proof of Income"],
            "source_url": "https://www.funzalushaka.doe.gov.za",
            "last_verified_at": datetime.now(timezone.utc),
            "visible": True,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    await db.funding_options.insert_many(funding_options)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()