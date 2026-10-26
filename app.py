import csv
import io
import json
import os
import requests
from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from storage import add_journal_entry, clear_journal, clear_all_user_data, get_journal_entries, get_checkins, save_checkins, save_scan, get_scans, save_routine, get_routines, save_profile, get_profile
from products import recommend_products, PRODUCTS
from youcam_client import analyze_skin, YouCamError
from image_quality import inspect_image
from polish_features import photo_capture_tips, climate_season_guidance, build_report_pdf
from vto_client import list_look_templates, run_look_vto
from differentiators import compare_scans, adapt_routine_from_scans, check_ingredient_conflicts, product_fit, optimise_budget, explain_recommendation, cheaper_swap, llm_coach_reply
from skincare import (
    build_routine,
    demo_analysis,
    make_budget_guide,
    parse_analysis,
    routine_coach_reply,
)

load_dotenv()
st.set_page_config(page_title="SkinWise AI", page_icon="✦", layout="wide")

# Basic bilingual UI support. English remains the default; Hindi translations cover key navigation and onboarding.
LANGUAGE_OPTIONS = {"English": "en", "हिन्दी (Hindi)": "hi"}
lang_label = st.sidebar.selectbox("Language / भाषा", list(LANGUAGE_OPTIONS), key="ui_language")
LANG = LANGUAGE_OPTIONS[lang_label]
_TRANSLATIONS = {
    "Your skin, less guesswork.": "आपकी त्वचा की बेहतर देखभाल, कम अनुमान।",
    "A routine that fits your skin": "आपकी त्वचा के अनुसार रूटीन",
    "and your real life.": "और आपकी रोज़मर्रा की ज़िंदगी के अनुसार।",
    "Skin analysis": "त्वचा विश्लेषण",
    "My routine": "मेरा रूटीन",
    "Product match": "उत्पाद सुझाव",
    "Progress journal": "प्रगति डायरी",
    "Routine coach": "रूटीन सहायक",
    "Privacy & setup": "गोपनीयता और सेटअप",
    "Your skin profile": "आपकी त्वचा की जानकारी",
    "Monthly skincare budget": "मासिक स्किनकेयर बजट",
    "Skin type": "त्वचा का प्रकार",
    "What would you like help with?": "आप किस चीज़ में मदद चाहते हैं?",
    "Sensitivity": "संवेदनशीलता",
    "Main goal": "मुख्य लक्ष्य",
    "Onboarding questionnaire": "शुरुआती प्रश्नावली",
    "Known allergies / ingredients to avoid": "ज्ञात एलर्जी / जिन सामग्री से बचना है",
    "Your usual climate": "आपकी सामान्य जलवायु",
    "Current skincare products (optional)": "अभी इस्तेमाल होने वाले स्किनकेयर उत्पाद (वैकल्पिक)",
    "Save onboarding & reminder preferences": "प्रोफ़ाइल और रिमाइंडर प्राथमिकताएँ सेव करें",
    "Photo-quality coach": "फ़ोटो गुणवत्ता सहायक",
    "Capture a face photo": "चेहरे की फ़ोटो लें",
    "Or upload a JPG or PNG photo": "या JPG/PNG फ़ोटो अपलोड करें",
    "Analyze with YouCam": "YouCam से विश्लेषण करें",
    "Your routine builder": "आपका रूटीन",
    "Download shareable report card (PDF)": "शेयर करने योग्य रिपोर्ट डाउनलोड करें (PDF)",
    "Virtual look preview (optional YouCam API)": "वर्चुअल लुक प्रीव्यू (वैकल्पिक YouCam API)",
}
def tr(text: str) -> str:
    return _TRANSLATIONS.get(text, text) if LANG == "hi" else text

hero_html = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
.block-container {max-width: 1240px; padding-top: 1.4rem; padding-bottom: 3rem; padding-left: clamp(.8rem, 3vw, 2rem); padding-right: clamp(.8rem, 3vw, 2rem)}
/* Responsive layout, readable contrast, keyboard focus, and touch-friendly controls. */
@media (max-width: 760px) {
  .block-container {padding-top: .65rem; padding-bottom: 1.5rem}
  .hero {padding: 1.2rem 1rem !important; border-radius: 16px !important}
  .hero p {font-size: .95rem}
  div[data-testid="stHorizontalBlock"] {flex-wrap: wrap !important; gap: .7rem !important}
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {min-width: min(100%, 280px) !important; flex: 1 1 100% !important}
  div[data-testid="stMetric"] {padding: .7rem}
  button, [role="button"], input, textarea, select {min-height: 44px}
  .stTabs [data-baseweb="tab-list"] {gap: .25rem; overflow-x: auto; flex-wrap: nowrap}
  .stTabs [data-baseweb="tab"] {padding: .45rem .6rem; white-space: nowrap}
}
:focus-visible {outline: 3px solid #5b3a67 !important; outline-offset: 2px !important}
label, p, li, [data-testid="stCaptionContainer"] {line-height: 1.5}

html, body, [class*="css"] {font-family:'DM Sans',sans-serif}
.hero {padding:2.1rem 2.2rem; border:1px solid #eadfdc; border-radius:24px;
background:linear-gradient(120deg,#fbede6 0%,#f4edf7 54%,#e8f3ee 100%); margin-bottom:1.2rem}
.eyebrow {letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:#76576d;font-weight:700}
.hero h1 {font-family:'Playfair Display',serif;font-size:clamp(2rem,4vw,3.2rem);color:#302631;line-height:1.08;margin:.45rem 0}
.hero p {font-size:1.02rem;color:#625462;max-width:790px;margin-bottom:.4rem}
.pill {display:inline-block;border:1px solid #dac9d7;border-radius:999px;padding:.28rem .7rem;margin:.2rem .25rem .1rem 0;font-size:.78rem;color:#634c62}
.small-note {font-size:.82rem;color:#756d77}
div[data-testid="stMetric"] {background:#fffaf8;border:1px solid #eee2df;padding:1rem;border-radius:16px}
div.stButton > button {border-radius:12px}
section[data-testid="stSidebar"] {background:#fcf8f6}
</style>
<div class="hero">
  <div class="eyebrow">SKINWISE AI · YOUR SKIN, LESS GUESSWORK</div>
  <h1>__HERO_TITLE__<br>__HERO_SUBTITLE__</h1>
  <p>__HERO_COPY__</p>
  <span class="pill">Budget-aware</span><span class="pill">Sensitive-skin aware</span><span class="pill">Privacy-first by design</span>
</div>
"""
hero_html = hero_html.replace("__HERO_TITLE__", tr("A routine that fits your skin")).replace("__HERO_SUBTITLE__", tr("and your real life.")).replace("__HERO_COPY__", "त्वचा विश्लेषण को समझें, आसान रूटीन बनाएं और अपनी प्रगति ट्रैक करें।" if LANG == "hi" else "Understand supported skin-analysis results, turn them into a simple routine, and keep track of what you actually use — without the pressure to buy everything.")
st.markdown(hero_html, unsafe_allow_html=True)

# Personal journal/check-ins are persisted locally in SQLite; images and API keys are not stored.
for key, default in {
    "analysis": None, "source": None, "history": [], "completed_steps": [], "scans": [],
    "routine_notes": "", "coach_messages": [], "baseline_photo_name": None,
    "photo_consent": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default
if st.session_state.pop("_reset_photo_consent_next_run", False):
    st.session_state.pop("photo_consent", None)
if "journal_loaded" not in st.session_state:
    try:
        st.session_state.history = get_journal_entries()
        st.session_state.onboarding_profile = get_profile()
        st.session_state.scans = get_scans()
    except Exception:
        st.session_state.history = []
        st.session_state.scans = []
        st.session_state.onboarding_profile = {}
    st.session_state.journal_loaded = True

with st.sidebar:
    st.header(tr("Your skin profile"))
    st.caption("Your choices stay in this browser session unless you export them.")
    budget = st.select_slider(tr("Monthly skincare budget"), ["Under ₹500", "₹500–₹1,000", "₹1,000–₹2,000", "₹2,000+"], value="₹500–₹1,000")
    skin = st.selectbox(tr("Skin type"), ["Not sure", "Oily", "Dry", "Combination", "Normal", "Sensitive"])
    concerns = st.multiselect(tr("What would you like help with?"), ["Acne / breakouts", "Dark spots", "Uneven texture", "Dryness", "Oiliness", "Redness", "Fine lines"], default=["Acne / breakouts", "Dark spots"])
    sensitivity = st.selectbox(tr("Sensitivity"), ["Not sure", "Low", "Moderate", "High"])
    routine_style = st.radio("Routine style", ["Simple (essentials first)", "Balanced (one optional extra)"])
    avoid = st.multiselect("Ingredients / product types to avoid", ["Fragrance", "Essential oils", "Exfoliating acids", "Retinoids", "Known personal trigger (unspecified)"])
    goal = st.selectbox(tr("Main goal"), ["Build a consistent routine", "Reduce breakouts", "Prevent dark spots worsening", "Support a dry or tight-feeling barrier", "Keep routine affordable"])
    st.markdown("### " + tr("Onboarding questionnaire"))
    saved_profile = st.session_state.get("onboarding_profile", {})
    allergies = st.text_input(tr("Known allergies / ingredients to avoid"), value=saved_profile.get("allergies", ""), placeholder="e.g. fragrance, lanolin, known allergy")
    climate = st.selectbox(tr("Your usual climate"), ["Not specified", "Hot / humid", "Hot / dry", "Cold / dry", "Mixed / seasonal"], index=["Not specified", "Hot / humid", "Hot / dry", "Cold / dry", "Mixed / seasonal"].index(saved_profile.get("climate", "Not specified")) if saved_profile.get("climate", "Not specified") in ["Not specified", "Hot / humid", "Hot / dry", "Cold / dry", "Mixed / seasonal"] else 0)
    current_products = st.text_area(tr("Current skincare products (optional)"), value=saved_profile.get("current_products", ""), placeholder="e.g. cleanser, moisturizer, sunscreen; include product names if known", height=70)
    reminder_enabled = st.checkbox("Enable in-app routine reminders", value=bool(saved_profile.get("reminder_enabled", True)))
    reminder_morning = st.selectbox("Morning reminder time", ["07:00", "08:00", "09:00", "10:00", "11:00"], index=["07:00", "08:00", "09:00", "10:00", "11:00"].index(saved_profile.get("reminder_morning", "08:00")) if saved_profile.get("reminder_morning", "08:00") in ["07:00", "08:00", "09:00", "10:00", "11:00"] else 1)
    reminder_evening = st.selectbox("Evening reminder time", ["18:00", "19:00", "20:00", "21:00", "22:00"], index=["18:00", "19:00", "20:00", "21:00", "22:00"].index(saved_profile.get("reminder_evening", "20:00")) if saved_profile.get("reminder_evening", "20:00") in ["18:00", "19:00", "20:00", "21:00", "22:00"] else 2)
    if st.button(tr("Save onboarding & reminder preferences"), use_container_width=True):
        profile = {"skin_type": skin, "concerns": concerns, "sensitivity": sensitivity, "budget": budget, "routine_style": routine_style, "avoid": avoid, "goal": goal, "allergies": allergies, "climate": climate, "current_products": current_products, "reminder_enabled": reminder_enabled, "reminder_morning": reminder_morning, "reminder_evening": reminder_evening}
        save_profile(profile)
        st.session_state.onboarding_profile = profile
        st.success("Onboarding profile saved locally.")

tabs = st.tabs(["✨ " + tr("Skin analysis"), "🧴 " + tr("My routine"), "🛍️ " + tr("Product match"), "📈 " + tr("Progress journal"), "💬 " + tr("Routine coach"), "🔒 " + tr("Privacy & setup")])

with tabs[0]:
    st.subheader("01 · Get a skin snapshot")
    st.write("Use a clear, front-facing photo in even lighting. Avoid filters, heavy makeup, and photos you do not have permission to submit.")
    col_photo, col_result = st.columns([1, 1.15], gap="large")
    with col_photo:
        st.markdown("### " + tr("Photo-quality coach"))
        st.caption("Before you capture: use the guide below, then review the automatic checks after the photo is taken. Browser camera support varies.")
        for tip in photo_capture_tips():
            st.write(f"- {tip}")
        camera_photo = st.camera_input(tr("Capture a face photo"), key="analysis_camera")
        uploaded_photo = st.file_uploader(tr("Or upload a JPG or PNG photo"), type=["jpg", "jpeg", "png"], key="analysis_photo")
        photo = camera_photo if camera_photo is not None else uploaded_photo
        if photo:
            if photo.size > 8 * 1024 * 1024:
                st.error("Please use an image smaller than 8 MB.")
            else:
                st.image(photo, caption="Selected photo", width=310)
                photo_check = inspect_image(photo.getvalue())
                if photo_check.get("message"):
                    st.warning("Photo-quality coach: " + photo_check["message"])
                else:
                    st.success(f"Photo-quality coach: image preflight looks reasonable ({photo_check['width']} × {photo_check['height']} px). This does not guarantee a face is detectable.")
        st.caption("Live analysis uses the YouCam Skin Analysis v2.1 workflow: File API upload → task creation → result polling.")
        st.info("Privacy notice: the selected photo is sent to the YouCam endpoint configured by the app when you run live analysis. SkinWise does not save the uploaded photo to its local database, but the API provider may process it under its own terms and retention policy. Do not upload a photo unless you have permission to use it.")
        photo_consent = st.checkbox(
            "I understand that live analysis sends this photo to YouCam for processing, and I consent to that transfer.",
            key="photo_consent",
        )
        api_col, demo_col = st.columns(2)
        photo_check = inspect_image(photo.getvalue()) if photo and photo.size <= 8 * 1024 * 1024 else {"ok": False}
        with api_col:
            run_live = st.button(tr("Analyze with YouCam"), type="primary", disabled=(not bool(photo) or not photo_consent or (photo.size > 8 * 1024 * 1024 if photo else True)), use_container_width=True)
        with demo_col:
            run_demo = st.button("Preview labelled demo fallback", help="Fictional preview only; it does not analyze your photo or call YouCam.", use_container_width=True)
        if run_live and photo:
            key = os.getenv("YOUCAM_API_KEY", "").strip()
            base_url = os.getenv("YOUCAM_API_BASE_URL", "https://yce-api-01.makeupar.com").strip()
            if not key:
                st.error("Live API is not configured. Add YOUCAM_API_KEY to .env or deployment secrets.")
            elif not photo_check.get("ok"):
                st.error(photo_check.get("message", "Please upload a valid, clear photo."))
            else:
                try:
                    with st.spinner("Uploading, starting YouCam Skin Analysis, and waiting for the result…"):
                        result = analyze_skin(key, photo.getvalue(), photo.name, photo.type or "image/jpeg", base_url=base_url)
                    raw = result.get("result", {})
                    st.session_state.analysis = parse_analysis(raw)
                    st.session_state.analysis["task_id"] = result.get("task_id")
                    st.session_state.source = "Live YouCam Skin Analysis v2.1"
                    scan = {"date": str(date.today()), "source": st.session_state.source, "summary": st.session_state.analysis.get("summary", ""), "concerns": st.session_state.analysis.get("concerns", []), "metrics": st.session_state.analysis.get("metrics", []), "task_id": result.get("task_id"), "raw_response": result.get("raw_response")}
                    save_scan(scan)
                    st.session_state.scans = get_scans()
                    st.session_state.history.append({"date": str(date.today()), "source": st.session_state.source, "summary": scan["summary"], "concerns": scan["concerns"]})
                    st.success("YouCam analysis completed. Review the returned scores and their definitions below.")
                except requests.exceptions.Timeout:
                    st.error("The YouCam request timed out. Wait a moment and retry; avoid repeatedly submitting while a task may still be processing.")
                except requests.exceptions.RequestException:
                    st.error("Could not connect to YouCam. Check your network, API host, and account status, then retry.")
                except YouCamError as exc:
                    st.error(str(exc))
                    if exc.category in {"image_quality", "no_face", "invalid_request", "analysis_failed"}:
                        st.info("Photo tips: face a window, look straight at the camera, keep your whole face in frame, remove glasses if possible, avoid filters, and use a sharp photo with no strong shadows.")
                    elif exc.category == "quota":
                        st.info("Check your remaining units in the YouCam API Console before making another request.")
                except Exception as exc:
                    st.error(f"Unexpected integration error ({type(exc).__name__}). No result was saved. Check the app logs and retry.")
        if run_demo:
            st.session_state.analysis = demo_analysis(skin, concerns)
            st.session_state.source = "Illustrative demo data"
            # Demo data is session-only and deliberately not persisted as a real scan.
            st.session_state.completed_steps = []
            st.success("Demo loaded. No photo was analyzed and no API was called.")

    with col_result:
        st.subheader("Your snapshot")
        analysis = st.session_state.analysis
        if not analysis:
            st.info("Your result will appear here. Live scans require a configured YouCam API key. The optional demo is fictional and never counts as a real scan.")
        else:
            st.caption("Result source: " + str(st.session_state.source))
            if st.session_state.source == "Illustrative demo data":
                st.warning("Demo only — these are fictional labels, not measurements from your photo.")
            metrics = analysis.get("metrics", [])
            if metrics:
                metric_cols = st.columns(min(3, len(metrics)))
                for i, metric in enumerate(metrics):
                    with metric_cols[i % len(metric_cols)]:
                        st.metric(str(metric.get("label", "Result")), str(metric.get("value", "—")), help=str(metric.get("description", "")))
            st.write(analysis.get("summary", "No summary returned."))
            score_metrics = [m for m in metrics if isinstance(m.get("value"), (int, float))]
            if score_metrics:
                st.markdown("### Visual concern report")
                st.caption("Bars show numeric values returned by YouCam on their reported scale. They are not a diagnosis; interpret score direction using the API's metric definitions.")
                for metric in score_metrics:
                    value = float(metric["value"])
                    left, right = st.columns([3, 1])
                    with left:
                        st.write(metric["label"])
                        st.progress(max(0.0, min(1.0, value / 100.0)))
                    with right:
                        st.metric("Returned score", f"{value:g}")
            if analysis.get("concerns"):
                st.markdown("**Top 3 returned concern scores**")
                st.write(", ".join(map(str, analysis["concerns"])))
            if analysis.get("raw_response") is not None:
                with st.expander("Inspect raw API response"):
                    st.json(analysis["raw_response"])
            st.warning("SkinWise AI is not a medical device and this result is not medical advice or a diagnosis. Photo-based results can be affected by lighting, camera quality, and other factors.")
            st.info("Consider seeing a qualified dermatologist for persistent, painful, rapidly worsening, unusual, or otherwise concerning skin changes. Do not delay professional care because of an app result.")

with tabs[1]:
    st.subheader("02 · " + tr("Your routine builder"))
    st.write("Start with essentials. Add one new product at a time; you do not need a product for every concern.")
    if not st.session_state.analysis:
        st.info("Run the demo or configure YouCam analysis first to generate your personalized plan.")
    else:
        plan = build_routine(st.session_state.analysis, budget, skin, concerns, sensitivity, routine_style, avoid)
        climate_guidance = climate_season_guidance(climate, location="Mumbai")
        st.markdown("### Climate & seasonal routine adjustments")
        st.caption(f"Seasonal context: {climate_guidance['season']} · {climate_guidance['location']}")
        for climate_tip in climate_guidance["tips"]:
            st.write(f"- {climate_tip}")
        st.caption(climate_guidance["disclaimer"])
        morning, evening = st.columns(2, gap="large")
        for col, title, steps in [(morning, "☀️ Morning", plan["morning"]), (evening, "🌙 Evening", plan["evening"])]:
            with col:
                st.markdown(f"### {title}")
                for item in steps:
                    label = f"{item['step']}. {item['name']} — {item['why']}"
                    checked = st.checkbox(label, key=f"routine_{title}_{item['step']}_{item['name']}", value=item["name"] in st.session_state.completed_steps)
                    if checked and item["name"] not in st.session_state.completed_steps:
                        st.session_state.completed_steps.append(item["name"])
                    elif not checked and item["name"] in st.session_state.completed_steps:
                        st.session_state.completed_steps.remove(item["name"])
        total_steps = len(plan["morning"]) + len(plan["evening"])
        completed = sum(1 for step in plan["morning"] + plan["evening"] if step["name"] in st.session_state.completed_steps)
        st.progress(completed / total_steps if total_steps else 0)
        st.caption(f"{completed} of {total_steps} routine steps checked off in this session.")
        if st.button("Save this routine plan"):
            save_routine({"date": str(date.today()), "source": st.session_state.source or "Routine builder", "profile": {"skin_type": skin, "concerns": concerns, "sensitivity": sensitivity, "budget": budget, "allergies": allergies, "climate": climate, "current_products": current_products, "goal": goal}, "morning": plan["morning"], "evening": plan["evening"]})
            st.success("Routine plan saved to local SQLite storage.")
        if st.button("Save today’s routine check-in"):
            save_checkins(str(date.today()), st.session_state.completed_steps, [x["name"] for x in plan["morning"] + plan["evening"]])
            st.success("Today’s completion status saved locally.")
        st.markdown("### Routine reminders, streaks & weekly summary")
        reminder_profile = st.session_state.get("onboarding_profile", {})
        if reminder_profile.get("reminder_enabled", True):
            now_clock = datetime.now().strftime("%H:%M")
            morning_time = reminder_profile.get("reminder_morning", "08:00")
            evening_time = reminder_profile.get("reminder_evening", "20:00")
            if now_clock >= morning_time and now_clock < evening_time:
                st.info(f"☀️ Morning routine reminder · Your chosen reminder time is {morning_time}. Check off your AM steps above.")
            if now_clock >= evening_time:
                st.info(f"🌙 Evening routine reminder · Your chosen reminder time is {evening_time}. Check off your PM steps above.")
            st.caption("These are in-app reminders shown when you open the app; browser push notifications are not enabled.")
        checkins = get_checkins(limit=90)
        day_done = {}
        for item in checkins:
            day_done.setdefault(item["checkin_date"], False)
            if item["completed"]:
                day_done[item["checkin_date"]] = True
        today = date.today()
        streak = 0
        cursor_day = today if day_done.get(today.isoformat(), False) else today - timedelta(days=1)
        while day_done.get(cursor_day.isoformat(), False):
            streak += 1
            cursor_day -= timedelta(days=1)
        week_dates = {(today - timedelta(days=i)).isoformat() for i in range(7)}
        week_rows = [item for item in checkins if item["checkin_date"] in week_dates]
        week_completed = sum(1 for item in week_rows if item["completed"])
        week_total = len(week_rows)
        completed_days = sum(1 for day in week_dates if day_done.get(day, False))
        m1, m2, m3 = st.columns(3)
        m1.metric("Current streak", f"{streak} day{'s' if streak != 1 else ''}")
        m2.metric("Days checked in this week", f"{completed_days}/7")
        m3.metric("Steps completed this week", f"{week_completed}/{week_total}" if week_total else "0/0")
        if week_total:
            st.progress(week_completed / week_total)
        else:
            st.caption("Save a daily check-in to start your streak and weekly summary.")
        st.markdown("### Allergy and context reminders")
        if allergies.strip():
            st.warning(f"Your stated allergy / avoidance notes: {allergies}. Check the full ingredient list with a pharmacist or dermatologist; this app cannot verify every formula.")
        st.caption(f"Climate context: {climate}. Current products: {current_products or 'not listed'}. These are context notes for you and are not a diagnosis or automatic ingredient-safety verification.")
        st.markdown("### Budget guide")
        for item in make_budget_guide(budget, skin, sensitivity):
            st.write(f"**{item['category']}** — {item['guidance']}")
        st.markdown("### Ingredient conflict checker")
        ingredient_text = st.text_input("Paste ingredient names or product names", placeholder="e.g. retinol + salicylic acid", key="ingredient_conflict_text")
        if ingredient_text.strip():
            for warning in check_ingredient_conflicts(ingredient_text):
                st.warning(warning)
        st.markdown("### Adaptive routine review")
        recent_live = [x for x in get_scans() if "Live YouCam" in str(x.get("source", "")) and x.get("metrics")]
        if len(recent_live) >= 2:
            for suggestion in adapt_routine_from_scans(recent_live[1], recent_live[0], sensitivity, avoid):
                st.info(suggestion)
        else:
            st.caption("After two real scans with comparable metrics, this section can suggest cautious routine reviews. Demo scans are not used for adaptation.")
        st.markdown("### Your next steps")
        for item in plan["next_steps"]:
            st.write(f"- {item}")
        st.warning("Patch-test reminder: follow the product label, introduce only one new product at a time, and stop using it if you develop persistent irritation. Patch testing cannot guarantee that a product will never cause a reaction.")
        note = st.text_area("Personal note (optional)", value=st.session_state.routine_notes, placeholder="e.g., New moisturizer felt comfortable; remember to patch-test sunscreen.")
        st.session_state.routine_notes = note
        payload = {
            "generated_on": str(date.today()), "analysis": st.session_state.analysis,
            "source": st.session_state.source,
            "preferences": {"budget": budget, "skin_type": skin, "concerns": concerns, "sensitivity": sensitivity, "avoid": avoid, "goal": goal, "allergies": allergies, "climate": climate, "current_products": current_products},
            "routine": plan, "checked_off_steps": st.session_state.completed_steps, "note": note,
        }
        st.download_button("Download my routine (JSON)", json.dumps(payload, indent=2, ensure_ascii=False), "skinwise-routine.json", "application/json")
        report_pdf = build_report_pdf({
            "date": str(date.today()), "source": st.session_state.source,
            "profile": {"skin_type": skin, "concerns": concerns, "sensitivity": sensitivity, "budget": budget, "climate": climate, "goal": goal},
            "routine": plan, "climate_guidance": climate_guidance, "note": note,
            "progress": {"streak": streak, "days_this_week": completed_days, "steps_completed": week_completed, "steps_total": week_total},
        })
        st.download_button(tr("Download shareable report card (PDF)"), report_pdf, "skinwise-report-card.pdf", "application/pdf", type="primary")
        st.divider()
        st.markdown("### " + tr("Virtual look preview (optional YouCam API)"))
        st.caption("Try a curated makeup look on a separate selfie. This is a cosmetic style preview, not a prediction of skin improvement after 8 weeks. YouCam AI Look VTO can consume 2 API units per successful task; check your balance first.")
        st.info("For privacy, this preview requires a separate photo and explicit consent. The photo is sent to YouCam for rendering and is not saved to SkinWise's local database.")
        vto_photo = st.file_uploader("Choose a selfie for virtual makeup preview (JPG/PNG, under 10 MB)", type=["jpg", "jpeg", "png"], key="vto_photo_upload")
        vto_consent = st.checkbox("I consent to sending this selfie to YouCam AI Look Virtual Try-On.", key="vto_photo_consent")
        vto_api_key = os.getenv("YOUCAM_API_KEY", "").strip()
        vto_base_url = os.getenv("YOUCAM_API_BASE_URL", "https://yce-api-01.makeupar.com").strip()
        templates = []
        if vto_api_key and st.button("Load available YouCam looks", key="load_vto_templates"):
            try:
                templates = list_look_templates(vto_api_key, vto_base_url)
                st.session_state.vto_templates = templates
                if not templates:
                    st.warning("No look templates were returned for this API account.")
            except Exception as exc:
                st.error(f"Could not load YouCam looks ({type(exc).__name__}): {exc}")
        templates = st.session_state.get("vto_templates", [])
        if templates:
            labels = {f"{item['title']} · {item['id']}": item['id'] for item in templates}
            selected_look = st.selectbox("Choose a curated look", list(labels))
            if st.button("Generate virtual look preview", type="primary", disabled=not (vto_photo and vto_consent and vto_api_key), key="run_vto"):
                if vto_photo.size > 10 * 1024 * 1024:
                    st.error("Please choose a photo smaller than 10 MB.")
                else:
                    try:
                        from PIL import Image
                        from io import BytesIO
                        source_image = Image.open(vto_photo).convert("RGB")
                        if source_image.width < 100 or source_image.height < 100:
                            raise ValueError("The image must be at least 100 × 100 pixels.")
                        if max(source_image.size) >= 1920 or source_image.width >= 1920 or source_image.height >= 1080:
                            source_image.thumbnail((1919, 1079))
                        output_image = BytesIO()
                        source_image.save(output_image, format="JPEG", quality=90, optimize=True)
                        with st.spinner("Uploading your consented selfie and rendering the look…"):
                            vto_result = run_look_vto(vto_api_key, vto_base_url, output_image.getvalue(), "skinwise-vto-selfie.jpg", "image/jpg", labels[selected_look])
                        st.session_state.vto_result_url = vto_result["image_url"]
                        st.success("Virtual look preview generated. This does not predict future skin health or treatment results.")
                    except Exception as exc:
                        st.error(f"Virtual look preview failed ({type(exc).__name__}): {exc}")
        elif not vto_api_key:
            st.caption("Configure YOUCAM_API_KEY privately to enable the optional VTO preview.")
        if st.session_state.get("vto_result_url"):
            st.image(st.session_state.vto_result_url, caption="YouCam AI Look VTO result · cosmetic preview only", use_container_width=True)
            st.caption("The result image is hosted by YouCam. Its URL is held in the current app session; check provider retention terms.")

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["time_of_day", "step", "name", "why"])
        for period, items in [("Morning", plan["morning"]), ("Evening", plan["evening"])]:
            for item in items:
                writer.writerow([period, item["step"], item["name"], item["why"]])
        st.download_button("Export routine checklist (CSV)", csv_buffer.getvalue(), "skinwise-checklist.csv", "text/csv")

with tabs[3]:
    st.subheader("04 · Progress journal")
    st.caption("Journal entries are saved in a local SQLite database on the machine running SkinWise. Uploaded photos are not saved to that database.")
    st.info("For a fair comparison, take photos in similar lighting, distance, angle, and time of day. Skin changes are not always linear. Photos selected here are displayed for this session only and are not saved to the journal database.")
    baseline = st.file_uploader("Optional baseline photo for your own visual comparison", type=["jpg", "jpeg", "png"], key="baseline_photo")
    followup = st.file_uploader("Optional follow-up photo", type=["jpg", "jpeg", "png"], key="followup_photo")
    if baseline and followup:
        b, f = st.columns(2)
        with b:
            st.image(baseline, caption="Baseline photo", use_container_width=True)
        with f:
            st.image(followup, caption="Follow-up photo", use_container_width=True)
        st.warning("This is a visual side-by-side only. SkinWise does not measure change between these images.")
    journal_date = st.date_input("Journal date", value=date.today())
    adherence = st.slider("How consistently did you follow your routine?", 0, 7, 4, help="Number of days this week.")
    feel = st.selectbox("How did your skin feel?", ["Not recorded", "Comfortable", "Dry or tight", "Oily", "Stinging / irritated", "More breakouts", "Unsure"])
    journal_note = st.text_area("Journal note", placeholder="What changed? Any new product, irritation, or routine change?")
    if st.button("Save journal entry"):
        entry = {"date": str(journal_date), "source": "Journal entry", "adherence_days": adherence, "skin_feel": feel, "note": journal_note}
        add_journal_entry(entry)
        st.session_state.history = get_journal_entries()
        st.success("Journal entry saved locally.")
    if st.session_state.history:
        st.markdown("### Saved history")
        st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
        st.download_button("Export journal (JSON)", json.dumps(st.session_state.history, indent=2, ensure_ascii=False), "skinwise-journal.json", "application/json")
        if st.button("Clear saved journal history"):
            clear_journal()
            st.session_state.history = []
            st.success("Saved journal history cleared.")
    else:
        st.caption("No entries yet.")
    saved_scans = get_scans()
    if saved_scans:
        st.markdown("### Saved scan history")
        st.dataframe([{"date": x.get("date"), "source": x.get("source"), "top_concerns": ", ".join(x.get("concerns", [])), "task_id": x.get("task_id", "")} for x in saved_scans], use_container_width=True, hide_index=True)
        real_scans = [x for x in saved_scans if "Live YouCam" in str(x.get("source", "")) and x.get("metrics")]
        if len(real_scans) >= 2:
            st.markdown("### Scan-over-scan comparison")
            st.caption("Raw score changes only. Positive deltas are not automatically improvements; score direction depends on the documented metric definition.")
            baseline_label = st.selectbox("Baseline scan", [f"{x.get('date', 'unknown date')} · {str(x.get('task_id', ''))[:10]}" for x in real_scans], index=min(1, len(real_scans)-1))
            followup_label = st.selectbox("Follow-up scan", [f"{x.get('date', 'unknown date')} · {str(x.get('task_id', ''))[:10]}" for x in real_scans], index=0)
            bscan = real_scans[[f"{x.get('date', 'unknown date')} · {str(x.get('task_id', ''))[:10]}" for x in real_scans].index(baseline_label)]
            fscan = real_scans[[f"{x.get('date', 'unknown date')} · {str(x.get('task_id', ''))[:10]}" for x in real_scans].index(followup_label)]
            comparison = compare_scans(bscan, fscan)
            if comparison:
                st.dataframe(comparison, use_container_width=True, hide_index=True)
                import pandas as pd
                trend_rows = []
                for scan in reversed(real_scans):
                    row = {"Scan date": scan.get("date", "unknown")}
                    for metric in scan.get("metrics", []):
                        if isinstance(metric, dict) and isinstance(metric.get("value"), (int, float)):
                            row[str(metric.get("label", "Metric"))] = metric["value"]
                    trend_rows.append(row)
                trend = pd.DataFrame(trend_rows).set_index("Scan date")
                if not trend.empty and trend.shape[1]:
                    st.line_chart(trend)
            else:
                st.info("These scans do not share numeric metrics, so a direct comparison is not available.")
    saved_routines = get_routines()
    if saved_routines:
        st.markdown("### Saved routine plans")
        st.dataframe([{"date": x.get("date"), "source": x.get("source"), "skin_type": x.get("profile", {}).get("skin_type"), "budget": x.get("profile", {}).get("budget")} for x in saved_routines], use_container_width=True, hide_index=True)
    checkin_rows = get_checkins()
    if checkin_rows:
        st.markdown("### Saved routine check-ins")
        st.dataframe(checkin_rows, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("03 · Product match: a small, budget-aware shortlist")
    st.write("Choose a few products by role, price, and stated preferences—not by a claim that a product will cure a skin condition.")
    matched = recommend_products(skin, concerns, sensitivity, avoid, budget)
    st.caption(f"{matched['catalogue_count']} products in the curated catalogue. {matched['price_checked']}. Prices and stock can change; verify before buying.")
    if matched["products"]:
        st.metric("Starter shortlist total", f"₹{matched['total_inr']}", f"Budget cap ₹{matched['budget_cap_inr']}")
        for product in matched["products"]:
            with st.container(border=True):
                pcol1, pcol2 = st.columns([4, 1])
                with pcol1:
                    st.markdown(f"**{product['name']}**")
                    st.caption(f"{product['category'].title()} · {product['why']}")
                    st.caption("Key ingredients (verify current label): " + product.get("key_ingredients", "Check product label"))
                    st.caption("Match signals: " + (", ".join(product["concerns"]) if product["concerns"] else "routine essential"))
                    st.markdown(f"[Check price / buy link]({product['buy_link']})")
                with pcol2:
                    st.metric("Price snapshot", f"₹{product['price_inr']}")
        st.markdown(f"[Browse current product listings]({matched['source_url']})")
    else:
        st.warning("No products fit the current filters and budget. Raise the budget, review exclusions, or choose essentials separately.")
    st.info("This curated catalogue uses indicative INR price snapshots, not live retailer prices. Retailer links open searches so you can verify the exact SKU, price, seller, stock, and full ingredient list. Product matching is not medical advice.")
    with st.expander(f"Browse all {len(PRODUCTS)} catalogue products"):
        for item in PRODUCTS:
            with st.container(border=True):
                st.markdown(f"**{item['name']}** — ₹{item['price_inr']} · {item['category'].title()}")
                st.caption("Key ingredients (verify current label): " + item.get("key_ingredients", "Check product label"))
                st.caption("Concerns: " + (", ".join(item.get("concerns", [])) or "routine essential"))
                st.markdown(f"[Check price / buy link]({item['buy_link']})")
    st.markdown("### Product-fit check")
    product_names = [p["name"] for p in PRODUCTS]
    chosen_name = st.selectbox("Check a product before buying", product_names, key="product_fit_name")
    chosen_product = next(p for p in PRODUCTS if p["name"] == chosen_name)
    fit = product_fit(chosen_product, skin, concerns, sensitivity, avoid)
    st.metric("Profile-based fit", fit["verdict"])
    for reason in fit["reasons"]:
        st.write("- " + reason)
    st.caption(explain_recommendation(chosen_product, concerns, skin, sensitivity))

    st.markdown("### Budget optimiser")
    budget_cap = st.number_input("Your total routine budget (₹)", min_value=0, max_value=20000, value=1000, step=100, key="budget_optimizer_cap")
    eligible_products = [p for p in PRODUCTS if not (set(avoid or []) & set(p.get("avoid_tags", []))) and (skin in ("Not sure", "Sensitive") or skin in p.get("skin_types", []))]
    optimised = optimise_budget(eligible_products, int(budget_cap))
    st.metric("Optimised catalogue total", f"₹{optimised['total_inr']}", f"₹{optimised['remaining_inr']} remaining")
    st.caption(f"Rough monthly cost estimate: ₹{optimised['total_inr']} if you bought each selected item once this month. Actual use duration varies by product and package size.")
    if optimised["products"]:
        for p in optimised["products"]:
            st.write(f"**{p['category'].title()} — {p['name']}** · ₹{p['price_inr']} · {explain_recommendation(p, concerns, skin, sensitivity)}")
            swap = cheaper_swap(p, eligible_products)
            if swap:
                candidate = swap["product"]
                if swap["same_key_ingredient_claim_supported"]:
                    st.caption(f"Cheaper same-category alternative: {candidate['name']} (₹{candidate['price_inr']}) — saves ₹{swap['savings_inr']}; catalogue ingredient text overlaps on {', '.join(swap['shared_ingredients'])}. Verify exact current labels; this does not prove equivalent performance.")
                else:
                    st.caption(f"Lower-cost same-category alternative: {candidate['name']} (₹{candidate['price_inr']}) — saves ₹{swap['savings_inr']}; ingredient equivalence could not be confirmed from catalogue text.")
    else:
        st.info("No catalogue items fit that budget. Consider increasing it or prioritising one essential at a time.")

    if st.button("Export product shortlist (CSV)"):
        products_csv = io.StringIO()
        writer = csv.writer(products_csv)
        writer.writerow(["product", "brand", "category", "price_inr", "key_ingredients", "why", "buy_link", "price_checked"])
        for product in matched["products"]:
            writer.writerow([product["name"], product["brand"], product["category"], product["price_inr"], product.get("key_ingredients", ""), product["why"], product["buy_link"], matched["price_checked"]])
        st.download_button("Download CSV", products_csv.getvalue(), "skinwise-product-shortlist.csv", "text/csv")

with tabs[4]:
    st.subheader("05 · Routine coach")
    st.write("Ask about your routine. When OPENAI_API_KEY is configured, the coach uses an LLM with your current scan metrics and preferences as context; otherwise it clearly falls back to rule-based guidance.")
    if st.session_state.analysis:
        st.caption("Current focus: " + (", ".join(concerns) if concerns else "general routine"))
    question = st.text_input("Ask a routine question", placeholder="How do I introduce a new product slowly?")
    if st.button("Ask coach", disabled=not bool(question.strip())):
        current_routine = build_routine(st.session_state.analysis, budget, skin, concerns, sensitivity, routine_style, avoid) if st.session_state.analysis else None
        answer, coach_mode = llm_coach_reply(question, st.session_state.analysis, current_routine, skin, concerns, sensitivity, avoid, budget)
        st.session_state.coach_messages.append({"question": question, "answer": answer, "mode": coach_mode})
    for msg in reversed(st.session_state.coach_messages[-6:]):
        with st.chat_message("user"):
            st.write(msg["question"])
        with st.chat_message("assistant"):
            st.write(msg["answer"])
            st.caption(msg.get("mode", "Coach"))
    if st.button("Clear coach conversation"):
        st.session_state.coach_messages = []
        st.rerun()

with tabs[5]:
    st.subheader("06 · Privacy, consent, safety & API setup")
    st.markdown("### What is stored and where?")
    st.markdown("""
- **Local on this app host:** journal notes and routine check-ins are stored in a local SQLite database. If you run the app on your own computer, that database is on your computer; if you use a hosted deployment, it is on that host unless you configure storage differently.
- **Not saved by SkinWise:** uploaded analysis and comparison photos are not written to the SkinWise database. They may remain temporarily in the active app session or browser memory.
- **Third-party processing:** when you choose live analysis and consent, the selected photo is sent to the configured YouCam endpoint. SkinWise cannot promise the provider's retention or deletion behavior; check the terms for your account and region.
- **API key:** keep it in `.env` or deployment secrets. Never paste it into chat, source code, screenshots, or Git commits.
- **Optional LLM coach:** set `OPENAI_API_KEY`; optionally set `OPENAI_MODEL` and `OPENAI_BASE_URL`. The coach sends a text summary of selected preferences and returned metrics, not the photo or API key, to the configured LLM provider.
- **Exports:** files you download are under your control and are not removed by the delete button below.
    """)
    st.markdown("### Consent")
    st.write("Live analysis is disabled until you explicitly consent beside the photo upload. Consent applies to sending the selected photo to the configured YouCam endpoint for that analysis. You can leave the box unchecked and use the clearly labelled demo instead.")
    st.markdown("### Safety boundaries")
    st.warning("SkinWise AI provides general skincare education, not medical advice, diagnosis, or treatment. Seek a qualified dermatologist for persistent, painful, rapidly worsening, unusual, or concerning symptoms. Do not delay care based on an app result.")
    st.write("Patch-test new products according to their label and introduce one new product at a time. Stop using a product if it causes persistent irritation. A patch test cannot guarantee that a reaction will not occur.")

    st.markdown("### Delete my data")
    st.write("This permanently clears SkinWise journal entries and routine check-ins stored in the app's local SQLite database, and clears the current session's analysis, journal view, routine notes, coach conversation, and selected-photo consent. It does not delete downloaded exports, browser/device copies, server backups, or data retained by YouCam or another third party.")
    if st.button("Delete my SkinWise data", type="primary", use_container_width=False):
        try:
            clear_all_user_data()
        except Exception as exc:
            st.error(f"Could not clear locally stored data ({type(exc).__name__}). Check the app host's file permissions.")
        else:
            for key, value in {
                "analysis": None, "source": None, "history": [], "completed_steps": [], "scans": [],
                "routine_notes": "", "coach_messages": [], "baseline_photo_name": None,
                "journal_loaded": True, "onboarding_profile": {},
            }.items():
                st.session_state[key] = value
            st.session_state["_reset_photo_consent_next_run"] = True
            st.success("SkinWise local journal and check-ins were cleared, and current session data was reset.")
            st.rerun()

    st.markdown("### Live API setup")
    st.markdown("""
1. Create `.env` from `.env.example`.
2. Add `YOUCAM_API_KEY` and, if required, set `YOUCAM_API_BASE_URL` to the regional host shown in your API documentation.
3. SkinWise uses the published File API upload → Skin Analysis v2.1 task → status polling workflow.
4. Confirm supported actions and units for your account before live judging.
    """)
    st.code("YOUCAM_API_KEY=your_private_key\nYOUCAM_API_BASE_URL=https://yce-api-01.makeupar.com", language="bash")
    st.warning("This integration follows the published v2.1 workflow but must still be tested with your API key and region-specific account permissions before claiming a successful live scan.")
    st.markdown("**Project readiness checklist**")
    for item in [
        "Real API endpoint and authentication verified",
        "API response fields mapped to official definitions",
        "Tests pass locally",
        "App deployed and public demo link tested",
        "Screenshots captured from the working app",
        "1–3 minute public demo video uploaded",
    ]:
        st.checkbox(item, key="readiness_" + item)

st.divider()
st.caption("SkinWise AI · Hackathon prototype · Demo data is clearly labelled · Not medical advice")
