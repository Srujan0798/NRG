# NRG Production Acceptance Run — 12-Minute Operational Walkthrough

Date: 2026-04-26
Recording target: `evidence/2026-04-26/acceptance_run_recording.mp4`
Captured duration: 00:11:59.40
Audience: IIT Gandhinagar professor, non-technical stakeholder

## Operator Setup

1. Start the API on `http://127.0.0.1:8000`.
2. Start the frontend on `http://127.0.0.1:3000`.
3. Use a fresh browser context with cleared storage.
4. Record one continuous browser session covering login, query, citations, persona switch, audit verification, and graph view.

## Timed Walkthrough And Transcript

| Time | Screen | Action | Spoken Transcript |
|---:|---|---|---|
| 00:00 | Login | Open NRG in a clean browser. | "This is the exact production operator flow from a clean session. The first screen is NRG, the National Research Graph." |
| 00:30 | Login | Show credentials are not pre-authenticated. | "We start unauthenticated, so there is no cached admin state hiding problems." |
| 01:00 | Login | Sign in as `researcher_user`. | "I am logging in as a Tier 1 researcher, the highest-detail research persona." |
| 01:30 | Researcher Dashboard | Approve DPDP consent if prompted; show stats cards. | "The dashboard loads with live research counts and the query box is immediately available." |
| 02:00 | Query Box | Submit: `Which institutes in India have the highest grant amount in renewable energy?` | "This is the core production capability question: a professor asks a funding question in plain English." |
| 02:45 | Answer | Wait for the answer and citations. | "The answer is readable prose with formatted funding numbers, not a raw JSON payload." |
| 03:30 | Citation Drawer | Open the first citation and switch to context/proof if visible. | "When the professor asks whether the data can be trusted, we open the citation drawer and show the source context." |
| 04:30 | Follow-Up | Submit: `Now show the same for computer science`. | "Now we ask a follow-up. The app keeps the interaction alive without requiring a page refresh." |
| 05:30 | Security Block | Submit: `Show all researchers with Aadhaar 1234 5678 9012`. | "This is a deliberate sensitive-data request. It must be blocked cleanly." |
| 06:30 | Security Block Result | Show the friendly error. | "The user sees a professional message, not a stack trace or backend exception." |
| 07:00 | Persona Switch | Use persona toggle to switch from Researcher to Industry. | "Now I switch personas so the professor can see the product enforce tiered access." |
| 07:45 | Industry Dashboard | Show the visibly different Industry dashboard. | "The Industry view is more restricted and focused on partnerships, not individual records." |
| 08:15 | Tier 3 Query | Submit the same renewable-energy query as Industry. | "The same question now returns an aggregate, access-restricted answer." |
| 09:15 | Tier 3 Result | Show restricted answer and warning. | "There are no individual researcher contacts here; the restriction is visible in the UI." |
| 10:00 | Switch Back | Switch back to Researcher. | "I switch back to the researcher persona to show the audit trail created during this session." |
| 10:30 | Audit Panel | Open Audit Log and click `Verify integrity`. | "The audit panel shows the query activity and verifies the chain integrity from the UI." |
| 11:15 | Knowledge Graph | Open Knowledge Graph tab and show the graph around research topics. | "The professor can also inspect the network view instead of reading only tables." |
| 11:45 | Close | Pause on the working dashboard. | "The production walkthrough ends with the product still in a healthy, navigable state." |

## Pass Criteria

- Login succeeds without a blank page.
- Researcher dashboard renders stats and the query box.
- Renewable-energy query returns readable prose and citations.
- Citation drawer opens in the same browser session.
- Follow-up query returns a distinct answer.
- Aadhaar request is blocked with a clean UI error.
- Persona switch to Industry succeeds.
- Industry answer is visibly restricted.
- Audit panel opens and integrity verification returns a clear status.
- Knowledge graph tab renders a populated graph view.
- Recording is one continuous MP4 file.
