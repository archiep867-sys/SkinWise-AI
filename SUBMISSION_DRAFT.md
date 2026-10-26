# SkinWise AI — Hackathon Submission Draft

## One-line pitch

**SkinWise AI turns skin-analysis results into a practical, explainable, budget-aware skincare plan—helping people understand their options without treating an AI score as a medical diagnosis.**

## Project description

Skincare advice can be confusing, expensive, and difficult to personalize. SkinWise AI is a skincare decision companion built around a YouCam Skin Analysis workflow. It is designed to turn returned analysis metrics into an understandable report, a conservative AM/PM routine, and a curated shortlist of skincare products with indicative Indian-market prices.

The prototype combines photo preflight checks and explicit consent before sending a photo for live analysis; result summaries; profile-aware routine and product matching; ingredient-caution prompts; budget-based alternatives; and a saved progress history. When users have multiple real scans, it can compare available numeric metrics over time and prompt them to review their routine cautiously. Explanations show why a product or routine step was suggested, while safety notes remind users that the app is educational and not a diagnosis or substitute for a dermatologist.

SkinWise AI is designed to make skincare guidance more understandable, transparent, and budget-conscious. It does not claim that a score proves a treatment works, that a product caused a change, or that catalogue products are guaranteed to be safe or effective. Product prices are indicative rather than live, and product details should be checked against current packaging and retailer listings.

## What makes it different

- **From scores to next steps:** presents analysis results alongside a readable report and routine suggestions.
- **Budget-aware choices:** helps users shortlist catalogue products within a spending limit and consider lower-cost alternatives.
- **Explainable recommendations:** shows the profile and catalogue signals behind product-fit decisions.
- **Progress with caution:** compares metrics from saved real scans without automatically calling a change good or bad when the metric scale or direction has not been verified.
- **Safety and privacy awareness:** requests consent before live photo transfer, avoids saving uploaded images in the local database, includes patch-test reminders, and provides a local-data deletion control.
- **Beyond the photo:** an onboarding questionnaire captures skin type, sensitivity, stated allergies/avoidances, climate, current products, goals, and budget as extra context for the routine.
- **Habit support:** an in-app AM/PM reminder prompt, daily routine checklist, saved completion streak, and rolling seven-day adherence summary help users build consistency without requiring push notifications.
- **Mobile-first and accessible basics:** responsive spacing/columns, touch-friendly controls, visible keyboard focus, and a basic English/Hindi selector for key navigation and onboarding fields.
- **Optional beauty VTO:** where the account has API access, users can consent to a separate selfie transfer, select an available YouCam AI Look template, and view a rendered cosmetic look. This is explicitly not a claim about what their skin will look like after eight weeks.

## Tier 3 polish features

The prototype includes a locally saved onboarding profile and in-app routine habit support. Reminder prompts appear when the app is open; they are not operating-system or browser push notifications. Allergy information is user-entered context and is not a guarantee that every product formula has been checked. Mobile styling and Hindi translation are basic prototype-level improvements, not a completed WCAG audit or full-app translation. The optional YouCam AI Look VTO integration must be verified with the live account; it is cosmetic preview only and consumes API units.

## Built with

Python, Streamlit, SQLite, and the YouCam Skin Analysis API workflow. An optional OpenAI-compatible text coach can be enabled with a private API key; the prototype includes a rule-based fallback.

## Important demo note

Before submission, verify the live YouCam scan end-to-end using the actual hackathon account and supported region, confirm the meaning and scale of displayed metrics, and record the demo using genuine app output. Do not present the fictional demo fallback as a real analysis. Do not claim live API success until it has been tested.

## Award-focused positioning

Use the official award categories and eligibility rules in the submission form. **Rising Star Award (Student Only):** if eligible, emphasize the student-led problem-solving, the working prototype, technical learning, iteration, and a clear live demo. **Women in Tech Special Award:** enter only if the entrant meets the organizer's eligibility criteria; if eligible, emphasize the technical ownership, problem-solving, and potential impact of the work without making unsupported claims. These awards are separate from the core project description, so keep the project story focused on its actual capabilities and evidence.

## Final submission checklist

- [ ] Confirm eligibility for each award category before selecting it.
- [ ] Run and verify a real YouCam analysis with the hackathon account.
- [ ] If enabling the optional AI Look VTO, verify template listing, unit balance, selfie consent, rendering, and the returned result URL.
- [ ] Confirm metric definitions and scales from the official API documentation.
- [ ] Test the deployed app from a clean browser and check that secrets are not exposed.
- [ ] Record a public 1–3 minute demo showing the real workflow and the strongest differentiators.
- [ ] Include repository, live app, demo video, setup instructions, and accurate limitations in the submission.

## Additional polish features

- **Photo-quality coach:** pre-capture prompts cover lighting, face angle, camera distance, and sharpness. After capture or upload, local image checks flag likely darkness, over-brightness, low contrast, or framing concerns before the user starts analysis. This is a guided preflight, not continuous live video tracking.
- **Climate and seasonal routine notes:** contextual guidance considers the selected climate and calendar season, including Mumbai's humid/monsoon and hotter periods. It emphasizes sensible basics such as moisturizer texture based on comfort and broad-spectrum sunscreen. It does not claim to know today's live weather or UV index.
- **Shareable report card:** creates a downloadable PDF containing the routine, profile context, seasonal notes, and available adherence summary. It excludes uploaded photos. PDF export makes sharing easier, but it does not itself invoke any external “share and earn” bonus API-unit mechanism.
