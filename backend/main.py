"""
CareGuide — Surgical Patient Video Platform
FastAPI backend: EHR → Pipeline → Dashboard → SMS
"""

import os
import json
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from pipeline.ingest   import IngestLayer
from pipeline.extract  import ExtractionLayer
from pipeline.classify import ClassificationLayer
from pipeline.generate import GenerationLayer
from integrations.elevenlabs   import ElevenLabsClient
from integrations.tavus        import TavusClient
from integrations.twilio_client import TwilioClient

# ─── App Setup ────────────────────────────────────────────────
app = FastAPI(
    title="CareGuide Surgical Patient Platform",
    description="Personalized surgical education videos generated from EHR data.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_patient_store: dict = {}

# ─── Demo Seed ────────────────────────────────────────────────
@app.on_event("startup")
async def _seed_demo_patient() -> None:
    """Pre-populate demo patient so the dashboard works without running the full pipeline."""
    _patient_store["maria_001"] = {
        "name": "Maria L.",
        "phone": "",
        "email": "",
        "pipeline_type": "post_op",
        "voice_audio_url": None,
        "battlecard_html": "",
        "avatar_url": None,
        "voice_script": (
            "Hi Maria, I'm your personal care guide from the surgical team. "
            "I'm here to make sure you feel confident and supported as you recover at home. "
            "You just had a lumpectomy and sentinel node biopsy, and you're starting an important "
            "medication called olaparib to protect against the cancer returning. "
            "The most important thing right now: take olaparib 300 milligrams every morning and "
            "300 milligrams every evening — about 12 hours apart — every single day. "
            "I recommend setting phone alarms right now so you never miss a dose. "
            "If you do miss one, just skip it and take the next one on schedule. Never double up. "
            "You may feel some fatigue over the coming days — that's completely normal because "
            "your blood count is slightly low, and your body is healing. "
            "There are a few things that need a call to us right away: "
            "a fever of 100.4 degrees or higher means call us immediately. "
            "Shortness of breath or chest pain means call 911 — don't wait. "
            "Vomiting that won't stop, diarrhea that doesn't improve, or new bruising — call us. "
            "Your follow-up appointment is in about 4 weeks at the oncology clinic "
            "for a blood count recheck. We'll see how your body is tolerating the olaparib. "
            "Before that appointment — or any time — call us if something worries you. "
            "You are never bothering us. Calling early is always the right choice. "
            "You are strong, you have a great team behind you, and you've got this, Maria."
        ),
        "structured_data": {
            "patient_name": "Maria L.",
            "procedure_name": "Lumpectomy + Sentinel Node Biopsy",
            "allergies": ["NKDA"],
            "key_diagnoses": [
                "Triple-negative breast cancer",
                "BRCA1 mutation (germline)",
            ],
            "medications": [
                {"name": "Olaparib", "dose": "300mg", "frequency": "twice daily (12 hrs apart)", "route": "oral", "status": "CONTINUE", "notes": "Take for 12 months at the same times every day."},
                {"name": "Ondansetron", "dose": "8mg", "frequency": "every 8 hrs as needed", "route": "oral", "status": "CONTINUE", "notes": "For nausea — take as soon as you feel off."},
                {"name": "Loperamide", "dose": "2mg after first loose stool, then 2mg each (max 8mg/day)", "frequency": "as needed", "route": "oral", "status": "CONTINUE", "notes": "For diarrhea."},
            ],
            "red_flags": [
                "Fever 100.4°F or higher → call doctor immediately",
                "Shortness of breath or chest pain → call 911 / ER",
                "Vomiting that won't stop → call doctor",
                "Diarrhea that won't improve → call doctor",
                "New or worsening bleeding or bruising → call doctor",
                "Severe dizziness, can't keep fluids down → ER",
                "Worsening fatigue, lightheadedness, racing heart → call doctor",
            ],
            "normal_symptoms": [
                "Mild fatigue (blood count slightly low — Hgb 10.6, mild anemia expected)",
                "Mild soreness at incision site",
                "Light bruising",
            ],
            "post_op_instructions": (
                "Take olaparib exactly as prescribed — do NOT double up missed doses. "
                "No new supplements or herbal products without oncology approval. "
                "Use effective contraception during olaparib therapy. "
                "BRCA1 mutation is genetic — not caused by lifestyle."
            ),
            "primary_concern": "Understanding olaparib schedule and when to call the care team",
            "follow_up": {
                "date": "4 weeks from discharge",
                "provider": "Oncology clinic",
                "notes": "Blood count recheck",
            },
        },
        "resources": None,
    }

# ─── Request / Response Models ────────────────────────────────
class EHRBundle(BaseModel):
    patient_id:         str
    patient_name:       str
    phone_number:       str
    pmh:                str
    procedure_context:  str
    after_visit_summary: str
    clinical_notes:     str
    medication_list:    str
    allergies:          str
    problem_list:       str

class DischargeInput(BaseModel):
    patient_name:       str
    discharge_notes:    str
    patient_id:         Optional[str] = None
    phone_number:       Optional[str] = None
    email:              Optional[str] = None

class ResourceSet(BaseModel):
    voice_script:       str
    battlecard_html:    str
    voice_audio_url:    Optional[str] = None

class DischargeResponse(BaseModel):
    patient_id:         str
    dashboard_url:      str
    diagnosis:          ResourceSet
    treatment:          ResourceSet
    structured_data:    dict

class ProcessResponse(BaseModel):
    patient_id:       str
    pipeline_type:    str
    dashboard_url:    str
    voice_audio_url:  Optional[str]
    battlecard_html:  str
    avatar_url:       Optional[str]

class ChatRequest(BaseModel):
    patient_id:           str
    message:              str
    conversation_history: List[dict] = []

class ChatResponse(BaseModel):
    response:   str
    patient_id: str
    audio_url:  Optional[str] = None


# ─── Doctor Portal ────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def doctor_portal():
    """Serves the doctor dashboard — patient roster + add patient."""
    html_path = os.path.join(os.path.dirname(__file__), "../frontend/doctor.html")
    with open(html_path) as f:
        return HTMLResponse(content=f.read())


@app.get("/api/patients")
async def list_patients():
    """Return all patients in the store for the doctor roster."""
    patients = []
    for pid, d in _patient_store.items():
        sd = d.get("structured_data") or {}
        patients.append({
            "id": pid,
            "name": d.get("name", "Unknown"),
            "procedure": sd.get("procedure_name", ""),
            "date": sd.get("procedure_date", ""),
            "hasResources": d.get("resources") is not None,
            "pipelineType": d.get("pipeline_type", "post_op"),
            "phone": d.get("phone", ""),
            "email": d.get("email", ""),
        })
    return {"patients": patients}


@app.get("/doctor/patient/{patient_id}", response_class=HTMLResponse)
async def doctor_patient_view(patient_id: str):
    """Doctor's view of a patient dashboard (same as patient view but with back-to-roster nav)."""
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")

    d = _patient_store[patient_id]

    def clean_html(html):
        h = (html or "").strip()
        if h.startswith("```"):
            h = h.split("\n", 1)[1] if "\n" in h else h[3:]
            if h.endswith("```"):
                h = h[:-3].strip()
        return h

    resources = d.get("resources")
    resources_json = None
    if resources:
        resources_json = {
            "diagnosis": {
                "voice_audio_url": resources["diagnosis"].get("voice_audio_url"),
                "battlecard_html": clean_html(resources["diagnosis"].get("battlecard_html", "")),
            },
            "treatment": {
                "voice_audio_url": resources["treatment"].get("voice_audio_url"),
                "battlecard_html": clean_html(resources["treatment"].get("battlecard_html", "")),
            },
        }

    patient_json = json.dumps({
        "id":           patient_id,
        "name":         d["name"],
        "firstName":    d["name"].split()[0],
        "pipelineType": d["pipeline_type"],
        "procedure":    d["structured_data"].get("procedure_name", ""),
        "visitDate":    d["structured_data"].get("procedure_date", ""),
        "audioUrl":     d.get("voice_audio_url") or None,
        "tavusUrl":     d.get("avatar_url") or None,
        "phoneTeam":    os.getenv("CARE_TEAM_PHONE", ""),
        "hasResources": resources_json is not None,
        "resources":    resources_json,
        "doctorView":   True,
    })

    html_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    with open(html_path) as f:
        html = f.read()

    inject = f"<script>window.__PATIENT__ = {patient_json};</script>"
    html = html.replace("</head>", f"{inject}\n</head>")
    voice_url = f"/patient/{patient_id}/voice"
    html = html.replace('id="voiceAvatarBtn" href="#"', f'id="voiceAvatarBtn" href="{voice_url}"')

    return HTMLResponse(content=html)


# ─── PDF Upload ───────────────────────────────────────────────
from fastapi import File, UploadFile, Form

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Extract text from an uploaded PDF discharge document."""
    try:
        from PyPDF2 import PdfReader
        import io

        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        if not text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from PDF. The file may be scanned/image-based.")

        return {"text": text.strip(), "pages": len(reader.pages)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


# ─── Send to Patient ──────────────────────────────────────────
@app.post("/api/send-to-patient/{patient_id}")
async def send_to_patient(patient_id: str):
    """Send the patient dashboard link via SMS (Twilio) and email."""
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")

    d = _patient_store[patient_id]
    name = d.get("name", "Patient")
    first_name = name.split()[0]
    phone = d.get("phone", "")
    email = d.get("email", "")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    dashboard_url = f"{base_url}/patient/{patient_id}"

    results = {"sms": None, "email": None}

    # SMS via Twilio
    if phone:
        try:
            sms_body = (
                f"Hi {first_name}, your post-surgery recovery resources from your care team are ready. "
                f"View your personalized recovery plan here: {dashboard_url} "
                f"(Best viewed on a computer)"
            )
            sid = TwilioClient().send(to=phone, body=sms_body)
            results["sms"] = "sent" if sid else "twilio_not_configured"
        except Exception as e:
            print(f"[send] SMS error: {e}")
            results["sms"] = f"error: {str(e)}"

    # Email via Twilio SendGrid (or simple SMTP fallback)
    if email:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_host = os.getenv("SMTP_HOST")
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")

            if smtp_host and smtp_user and smtp_pass:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"Your Recovery Resources Are Ready - CareGuide"
                msg["From"] = smtp_user
                msg["To"] = email

                html_body = f"""
                <div style="font-family:-apple-system,sans-serif;max-width:500px;margin:0 auto;padding:24px;">
                    <div style="background:linear-gradient(135deg,#1A3C8F,#2563EB);color:#fff;padding:24px;border-radius:12px;text-align:center;margin-bottom:20px;">
                        <h1 style="font-size:20px;margin-bottom:6px;">CareGuide</h1>
                        <p style="font-size:14px;opacity:.85;">Your Recovery Resources Are Ready</p>
                    </div>
                    <p style="font-size:15px;color:#374151;line-height:1.6;margin-bottom:16px;">
                        Hi {first_name}, your care team has prepared personalized recovery resources for you, including voice explanations and quick reference guides.
                    </p>
                    <a href="{dashboard_url}" style="display:block;text-align:center;background:#2563EB;color:#fff;padding:14px 24px;border-radius:10px;text-decoration:none;font-weight:600;font-size:15px;margin-bottom:16px;">
                        View Your Recovery Plan
                    </a>
                    <p style="font-size:13px;color:#6B7280;text-align:center;">Best viewed on a computer or tablet.</p>
                </div>
                """
                msg.attach(MIMEText(html_body, "html"))

                with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587"))) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                results["email"] = "sent"
            else:
                results["email"] = "smtp_not_configured"
                print(f"[send] Email skipped — SMTP not configured. Would send to: {email}")

        except Exception as e:
            print(f"[send] Email error: {e}")
            results["email"] = f"error: {str(e)}"

    if not phone and not email:
        raise HTTPException(status_code=422, detail="No phone number or email on file for this patient")

    return {"patient_id": patient_id, "dashboard_url": dashboard_url, **results}


# ─── New Two-Resource Pipeline ────────────────────────────────
@app.post("/api/process-discharge")
async def process_discharge(input_data: DischargeInput):
    """
    Full two-resource pipeline:
      Raw discharge notes → Extract → Generate (Diagnosis + Treatment)
                         → ElevenLabs audio for each → Store

    Returns both resource sets for immediate display.
    """
    import uuid

    patient_id = input_data.patient_id or f"pt_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Extract structured data from raw discharge notes
        print(f"[pipeline] Starting extraction for {patient_id}...")
        raw_package = {
            "metadata": {
                "patient_id": patient_id,
                "patient_name": input_data.patient_name,
                "phone_number": input_data.phone_number or "",
            },
            "clinical_data": {
                "clinical_notes": input_data.discharge_notes,
                "after_visit_summary": input_data.discharge_notes,
                "pmh": "",
                "procedure_context": "",
                "medication_list": "",
                "allergies": "",
                "problem_list": "",
            },
        }

        structured_data = await ExtractionLayer().extract(raw_package)
        print(f"[pipeline] Extraction complete. Generating resources...")

        # 2. Generate two resource sets (diagnosis + treatment)
        generator = GenerationLayer()
        resources = await generator.generate_two_resources(structured_data)
        print(f"[pipeline] Generation complete. Synthesizing audio...")

        # 3. Synthesize audio for both via ElevenLabs
        el_client = ElevenLabsClient()
        diag_audio = await el_client.synthesize(
            resources["diagnosis"]["voice_script"], f"{patient_id}_diagnosis"
        )
        treat_audio = await el_client.synthesize(
            resources["treatment"]["voice_script"], f"{patient_id}_treatment"
        )
        print(f"[pipeline] Audio synthesis complete. Storing results...")

        # 4. Build dashboard URL
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        dashboard_url = f"{base_url}/patient/{patient_id}"

        # 5. Store everything
        _patient_store[patient_id] = {
            "name": input_data.patient_name,
            "phone": input_data.phone_number or "",
            "email": input_data.email or "",
            "pipeline_type": "post_op",
            "voice_audio_url": diag_audio,
            "battlecard_html": resources["diagnosis"]["battlecard_html"],
            "avatar_url": None,
            "voice_script": resources["diagnosis"]["voice_script"],
            "structured_data": structured_data,
            "resources": {
                "diagnosis": {
                    "voice_script": resources["diagnosis"]["voice_script"],
                    "battlecard_html": resources["diagnosis"]["battlecard_html"],
                    "voice_audio_url": diag_audio,
                },
                "treatment": {
                    "voice_script": resources["treatment"]["voice_script"],
                    "battlecard_html": resources["treatment"]["battlecard_html"],
                    "voice_audio_url": treat_audio,
                },
            },
        }

        print(f"[pipeline] Done! Dashboard: {dashboard_url}")

        return {
            "patient_id": patient_id,
            "dashboard_url": dashboard_url,
            "diagnosis": {
                "voice_script": resources["diagnosis"]["voice_script"],
                "battlecard_html": resources["diagnosis"]["battlecard_html"],
                "voice_audio_url": diag_audio,
            },
            "treatment": {
                "voice_script": resources["treatment"]["voice_script"],
                "battlecard_html": resources["treatment"]["battlecard_html"],
                "voice_audio_url": treat_audio,
            },
            "structured_data": structured_data,
        }

    except Exception as exc:
        print(f"[pipeline] ERROR: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(exc)}")


# ─── Legacy Process Patient ───────────────────────────────────
@app.post("/api/process-patient", response_model=ProcessResponse)
async def process_patient(bundle: EHRBundle, background_tasks: BackgroundTasks):
    """Legacy full pipeline (single resource set)."""
    raw_package = IngestLayer().process(bundle.model_dump())
    structured_data = await ExtractionLayer().extract(raw_package)
    pipeline_type = ClassificationLayer().classify(structured_data)
    generator = GenerationLayer()
    voice_script, battlecard_html = await generator.generate(structured_data, pipeline_type)
    audio_url = await ElevenLabsClient().synthesize(voice_script, bundle.patient_id)
    avatar = await TavusClient().create_conversation(
        patient_id=bundle.patient_id,
        knowledge_base={
            "voice_script":  voice_script,
            "battlecard":    battlecard_html,
            "ehr_summary":   structured_data,
        },
    )
    base_url      = os.getenv("BASE_URL", "http://localhost:8000")
    dashboard_url = f"{base_url}/patient/{bundle.patient_id}"
    _patient_store[bundle.patient_id] = {
        "name":                bundle.patient_name,
        "phone":               bundle.phone_number,
        "pipeline_type":       pipeline_type,
        "voice_audio_url":     audio_url,
        "battlecard_html":     battlecard_html,
        "avatar_url":          avatar.get("conversation_url"),
        "structured_data":     structured_data,
        "voice_script":        voice_script,
        "resources":           None,
    }
    background_tasks.add_task(
        _send_sms, phone=bundle.phone_number, name=bundle.patient_name, dashboard_url=dashboard_url,
    )
    return ProcessResponse(
        patient_id=bundle.patient_id, pipeline_type=pipeline_type,
        dashboard_url=dashboard_url, voice_audio_url=audio_url,
        battlecard_html=battlecard_html, avatar_url=avatar.get("conversation_url"),
    )


# ─── Resource Endpoints ───────────────────────────────────────
@app.get("/api/patient/{patient_id}/resources")
async def get_patient_resources(patient_id: str):
    """Return the two-resource sets (diagnosis + treatment) if available."""
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")
    resources = _patient_store[patient_id].get("resources")
    if not resources:
        raise HTTPException(status_code=404, detail="No split resources generated for this patient")

    def clean_html(html):
        """Strip markdown code fences if Claude wrapped the HTML."""
        h = (html or "").strip()
        if h.startswith("```"):
            h = h.split("\n", 1)[1] if "\n" in h else h[3:]
            if h.endswith("```"):
                h = h[:-3].strip()
        return h

    for key in ("diagnosis", "treatment"):
        if key in resources and "battlecard_html" in resources[key]:
            resources[key]["battlecard_html"] = clean_html(resources[key]["battlecard_html"])

    return resources


@app.get("/api/patient/{patient_id}/audio")
async def get_patient_audio(patient_id: str):
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")
    store = _patient_store[patient_id]
    cached_url = store.get("voice_audio_url")
    if cached_url:
        filename = cached_url.split("/audio/")[-1]
        from pathlib import Path
        if Path(f"/tmp/{filename}").exists():
            return {"audio_url": f"/audio/{filename}"}
    voice_script = store.get("voice_script")
    if not voice_script:
        raise HTTPException(status_code=422, detail="No voice script available for this patient")
    audio_url = await ElevenLabsClient().synthesize(voice_script, patient_id)
    if not audio_url:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured — set ELEVENLABS_API_KEY")
    store["voice_audio_url"] = audio_url
    return {"audio_url": audio_url}


@app.get("/api/patient/{patient_id}/battlecard")
async def get_battlecard(patient_id: str):
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"html": _patient_store[patient_id]["battlecard_html"]}


@app.get("/api/patient/{patient_id}/config")
async def get_dashboard_config(patient_id: str):
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")
    d = _patient_store[patient_id]
    return {
        "id":            patient_id,
        "name":          d["name"],
        "pipelineType":  d["pipeline_type"],
        "procedure":     d["structured_data"].get("procedure_name", ""),
        "visitDate":     d["structured_data"].get("procedure_date", ""),
        "audioUrl":      d["voice_audio_url"],
        "tavusUrl":      d["avatar_url"],
        "phoneTeam":     os.getenv("CARE_TEAM_PHONE", ""),
        "hasResources":  d.get("resources") is not None,
    }


@app.get("/api/patient/{patient_id}/discharge")
async def get_discharge_instructions(patient_id: str):
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")
    d = _patient_store[patient_id]
    return {
        "structured_data": d["structured_data"],
        "voice_script": d.get("voice_script", ""),
    }


@app.get("/patient/{patient_id}/voice", response_class=HTMLResponse)
async def voice_avatar_page(patient_id: str):
    """Serves the voice avatar conversation interface."""
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")

    d = _patient_store[patient_id]
    patient_json = json.dumps({
        "id":        patient_id,
        "name":      d["name"],
        "firstName": d["name"].split()[0],
        "procedure": d["structured_data"].get("procedure_name", ""),
    })

    html_path = os.path.join(os.path.dirname(__file__), "../frontend/voice-avatar.html")
    with open(html_path) as f:
        html = f.read()

    inject = f"<script>window.__PATIENT__ = {patient_json};</script>"
    html = html.replace("</head>", f"{inject}\n</head>")
    return HTMLResponse(content=html)


@app.get("/patient/{patient_id}", response_class=HTMLResponse)
async def patient_dashboard(patient_id: str):
    if patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")

    d = _patient_store[patient_id]

    def clean_html(html):
        h = (html or "").strip()
        if h.startswith("```"):
            h = h.split("\n", 1)[1] if "\n" in h else h[3:]
            if h.endswith("```"):
                h = h[:-3].strip()
        return h

    resources = d.get("resources")
    resources_json = None
    if resources:
        resources_json = {
            "diagnosis": {
                "voice_audio_url": resources["diagnosis"].get("voice_audio_url"),
                "battlecard_html": clean_html(resources["diagnosis"].get("battlecard_html", "")),
            },
            "treatment": {
                "voice_audio_url": resources["treatment"].get("voice_audio_url"),
                "battlecard_html": clean_html(resources["treatment"].get("battlecard_html", "")),
            },
        }

    patient_json = {
        "id":           patient_id,
        "name":         d["name"],
        "firstName":    d["name"].split()[0],
        "pipelineType": d["pipeline_type"],
        "procedure":    d["structured_data"].get("procedure_name", ""),
        "visitDate":    d["structured_data"].get("procedure_date", ""),
        "audioUrl":     d.get("voice_audio_url") or None,
        "tavusUrl":     d.get("avatar_url") or None,
        "phoneTeam":    os.getenv("CARE_TEAM_PHONE", ""),
        "hasResources": resources_json is not None,
        "resources":    resources_json,
    }

    patient_json_str = json.dumps(patient_json)

    html_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    with open(html_path) as f:
        html = f.read()

    inject = f"<script>window.__PATIENT__ = {patient_json_str};</script>"
    html = html.replace("</head>", f"{inject}\n</head>")

    voice_url = f"/patient/{patient_id}/voice"
    html = html.replace('id="voiceAvatarBtn" href="#"', f'id="voiceAvatarBtn" href="{voice_url}"')

    return HTMLResponse(content=html)


@app.post("/api/avatar/chat", response_model=ChatResponse)
async def avatar_chat(req: ChatRequest):
    if req.patient_id not in _patient_store:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_data = _patient_store[req.patient_id]

    try:
        from prompts.avatar import build_avatar_system_prompt
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        clean_data = {k: v for k, v in patient_data["structured_data"].items()
                      if k != "_raw_clinical"}
        system_prompt = build_avatar_system_prompt(clean_data)

        messages = [{"role": m["role"], "content": m["content"]}
                    for m in req.conversation_history]
        messages.append({"role": "user", "content": req.message})

        print(f"[avatar_chat] Sending to Claude for patient {req.patient_id}...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=350,
            system=system_prompt,
            messages=messages,
        )

        reply_text = response.content[0].text
        print(f"[avatar_chat] Got response ({len(reply_text)} chars), synthesizing audio...")
        audio_url = await ElevenLabsClient().synthesize(reply_text, f"{req.patient_id}_chat")

        return ChatResponse(response=reply_text, patient_id=req.patient_id, audio_url=audio_url)

    except Exception as exc:
        import traceback
        print(f"[avatar_chat] ERROR: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return ChatResponse(
            response="I'm having a brief technical issue. For urgent questions, please call your care team directly.",
            patient_id=req.patient_id, audio_url=None,
        )


# ─── Background Tasks ─────────────────────────────────────────
async def _send_sms(phone: str, name: str, dashboard_url: str) -> None:
    first = name.split()[0]
    body  = (
        f"Hi {first}, your post-surgery recovery resources from your care team are ready. "
        f"View your personalized recovery plan here: {dashboard_url} "
        f"(Best viewed on a computer)"
    )
    TwilioClient().send(to=phone, body=body)


# ─── Static Files ─────────────────────────────────────────────
try:
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../frontend")),
        name="static",
    )
except Exception:
    pass

try:
    app.mount("/audio", StaticFiles(directory="/tmp"), name="audio")
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
