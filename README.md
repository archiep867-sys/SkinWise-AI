# SkinWise AI

**A budget-aware skincare decision companion built for the YouCam API Skin AI & eCommerce VTO Hackathon.** SkinWise turns a real YouCam Skin Analysis result into a readable report, a conservative routine, a curated product shortlist, and a locally persisted progress history.

## Tier 1 features

- **Mobile-first responsive layout and accessibility basics:** narrow-screen CSS adapts spacing and columns, controls have larger touch targets, keyboard focus is visible, and labels retain readable line spacing and contrast. Test with actual iOS/Android browsers before judging; Streamlit's layout behavior can vary by browser.
- **Basic English/Hindi interface:** a language selector translates key navigation, profile/onboarding fields, and selected action labels into Hindi. Some detailed explanatory content remains English in this prototype.

- **YouCam Skin Analysis v2.1 integration:** File API upload URL + `file_id`, signed upload, asynchronous task creation, polling, result parsing, timeouts, and friendly provider/quota errors. The API host can be configured for account/region routing.
- **Photo preflight and edge cases:** JPG/PNG and 8 MB upload checks, image dimensions, brightness/contrast heuristics, face-detection failure guidance from provider errors, task timeouts, invalid requests, auth failures, rate limits, provider failures, and unit/quota messages.
- **Visual skin report:** metric cards, visual bars for returned numeric fields, a top-three returned-score summary, raw-response inspection, and disclaimers that values are not a diagnosis. Score interpretation should be confirmed against the current API schema.
- **32-product curated starter catalogue:** Indian-market product options, indicative INR price snapshots, category, ingredient highlights, skin-type/concern matching, avoidance tags, and retailer search links. Prices and ingredients must be verified against the current listing and packaging before purchase; no live inventory feed is connected.
- **Onboarding profile:** captures skin type, concerns, sensitivities, stated allergies/avoidances, climate, current products, goals, budget, and routine preferences; saves the profile locally so recommendations are not based on a photo alone. Allergy notes are user-provided context, not automated allergy validation.
- **Routine reminders and adherence:** in-app AM/PM reminder prompts, daily routine checklist, saved check-ins, current streak, and a rolling seven-day completion summary. These are in-app reminders, not browser push notifications.
- **Persistence:** local SQLite tables save the onboarding profile, scans, routine plans, journal entries, and routine check-ins across app reruns on the same persistent filesystem. Images and API keys are not saved in SQLite.
- **Trust and safety:** explicit photo-transfer consent, clear medical disclaimer, dermatologist prompt for concerning symptoms, patch-test reminders, and a delete-my-data action.
- **Deployment readiness:** Streamlit configuration, dependency file, environment template, and instructions for deploying from GitHub.

## Optional YouCam AI Look Virtual Try-On

- **Curated makeup look preview:** when the account has access and the user explicitly consents to a separate selfie transfer, SkinWise can list available AI Look VTO templates, upload the selfie through the File API, create a `look-vto` task, poll for completion, and display the returned render URL.
- The official AI Look VTO documentation lists **2 API units per successful task**. Check the current account balance and permissions before use. The feature is optional and is not required for the skincare workflow.
- **Important limitation:** a cosmetic makeup preview is not a simulation of skin improvement after eight weeks and must not be presented as one. No routine efficacy, medical outcome, or future appearance is predicted. Live VTO remains unverified against the project's actual API key/account until tested.

## Important status note

The integration follows the published YouCam API workflow, but **a successful live scan has not been verified in this repository session** because the developer's private API key/account is not available to test here. Confirm the API host and supported actions in your account/region, add the key privately, and run a live test before claiming the integration works in your demo. Do not commit your key.

The demo fallback is intentionally fictional, clearly labelled, and never saved as a real scan. It does not analyze the uploaded photo or call YouCam.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Put your private key in .env; do not share it or commit .env.
streamlit run app.py
```

Set these environment variables in `.env`:

```env
YOUCAM_API_KEY=your_private_key
YOUCAM_API_BASE_URL=https://yce-api-01.makeupar.com
```

If the API Console for your account specifies another regional API host, use that exact host. The default action list in `youcam_client.py` uses SD actions only; verify feature availability and unit consumption for your plan before repeated scans.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub with `.env` excluded.
2. Sign in to Streamlit Community Cloud and choose **Create app**.
3. Select this repository, branch `main`, and main file path `app.py`.
4. In the app's **Settings → Secrets**, add:

   ```toml
   YOUCAM_API_KEY = "your_private_key"
   YOUCAM_API_BASE_URL = "https://yce-api-01.makeupar.com"
   ```

5. Deploy, open the generated public URL in a private/incognito browser, and test the full upload → task → polling → result path.
6. Check the Streamlit logs for errors and confirm no secret appears in the UI or logs.

**Persistence caveat:** the app uses SQLite on the host filesystem. Local runs persist on your machine; hosted filesystem persistence depends on the host's storage lifecycle. For reliable long-term multi-user data, migrate to a managed database and add user authentication before collecting real users' data. Do not treat a public shared SQLite app as private per-user storage.

## Tests

```bash
python -m pytest -q
```

Current automated tests cover routine logic, result parsing, image preflight, catalogue shape, SQLite storage, VTO template parsing, and API client response helpers. They do not call YouCam live; test that separately with your account and a permitted image.

## Privacy and safety

- Photos are sent to YouCam only after the user checks the consent box and starts live analysis.
- Uploaded photos are not written to the SkinWise SQLite database. The provider may process uploaded images under its own terms and retention policy; review those terms for your account/region.
- Scan summaries and raw result JSON, routine plans, journal entries, and check-ins are stored locally in SQLite. Raw result payloads can contain task metadata; use the delete button or clear the database when appropriate.
- The delete action clears the app's local onboarding profile, journal, check-ins, scan history, routine plans, and current-session state. It cannot delete downloaded exports, external backups, or data retained by third parties.
- SkinWise provides general skincare education, not medical advice, diagnosis, or treatment. Seek qualified care for persistent, painful, severe, unusual, or worsening symptoms.
- Patch-test new products according to their label and introduce one new product at a time. Patch testing does not guarantee that a reaction will not occur.

## Product catalogue caveat

Product entries link to retailer search results, not guaranteed product detail pages. Prices are indicative snapshots rather than live retailer prices, and ingredient highlights are not a substitute for the current full INCI list on the package. Verify the exact product size, seller, price, availability, and ingredients before buying.

## Submission checklist

- [ ] Test live YouCam analysis with the API key and account region.
- [ ] Confirm every returned score's official meaning and scale.
- [ ] Deploy and test the public URL from a clean browser.
- [ ] Capture genuine screenshots from the functioning app.
- [ ] Record a public 1–3 minute demo explaining and showing the YouCam API workflow.
- [ ] Submit the repository, live URL, and video URL on Devpost.

## Tier 2 differentiators

- **Scan-over-scan comparison:** compares metrics present in both saved live scans, displays raw deltas, and charts available numeric metrics over time. The app deliberately does not label positive/negative deltas as better/worse because metric direction and scales must be verified against the official YouCam schema. Comparisons are only available after at least two real scans.
- **Adaptive routine review:** after two saved live scans, conservative rules flag possible routine-review prompts (for example, a changed redness score). They do not automatically claim a product caused a change or diagnose a condition. The user should consider photo consistency and how their skin feels.
- **Ingredient conflict checker:** checks a small built-in caution list for selected active combinations and suggests caution/separation; it is not a complete chemistry database or universal incompatibility claim.
- **Product-fit check:** classifies a catalogue item as GOOD FIT, CAUTION, or SKIP based on the user's profile, exclusions, and catalogue tags. It is not a guarantee of efficacy or safety.
- **Budget optimiser:** selects catalogue items under a user-set total and shows indicative total/rough monthly cost plus lower-cost same-category alternatives when available. Shared catalogue ingredient text is not proof of equivalent performance.
- **LLM routine coach (optional):** configure `OPENAI_API_KEY` to use the OpenAI-compatible chat completions endpoint. `OPENAI_MODEL` and `OPENAI_BASE_URL` are configurable. Without a key or if the request fails, the app falls back to its transparent rule-based coach. It sends a text summary of scan metrics and profile preferences, not the image or YouCam API key. Review your LLM provider's data terms before enabling it.
- **Explainability:** product and routine recommendations display the rule or catalogue signals behind each suggestion.

These differentiators are implemented as prototype features. Validate them with real API responses and current product labels before presenting the system as clinically meaningful or production-ready.

## Photo-quality coach, seasonal guidance, and report card

- **Photo-quality coach:** shows lighting, angle, distance, and sharpness tips before camera capture, supports browser camera capture or JPG/PNG upload, then runs local image preflight checks and displays feedback. This is guided capture, not continuous real-time computer-vision tracking or a guarantee that YouCam will detect a face.
- **Climate and seasonal guidance:** adds conservative routine notes based on the saved climate choice and seasonal calendar. Mumbai guidance includes humid/monsoon, hot pre-monsoon, post-monsoon transition, and milder/drier-season notes. The app does **not** fetch live weather or UV-index data; check a trusted local forecast for current conditions.
- **Shareable report card:** exports a PDF with profile context, AM/PM routine, seasonal guidance, and available adherence summary. It does not embed uploaded photos. The PDF is a shareable artifact; any hackathon “share and earn” bonus-unit mechanism must be handled through the organizer/provider's own process and is not triggered by PDF export itself.
