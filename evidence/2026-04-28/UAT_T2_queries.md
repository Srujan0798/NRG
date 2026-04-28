# UAT Query Set - Tier 2 Ministry

**Persona:** Ministry official / policy analyst
**Access assertion:** Tier 2 responses must use institutional aggregates, anonymized summaries, and policy-level trends. Researcher PII must not be returned.

| # | Query | Expected tier filtering |
|---|---|---|
| 1 | Which institutions produced the most AI research each year from 2020 to 2025? | Institution aggregate only. |
| 2 | Show a five-year rollup of AI, biotech, renewable energy, and semiconductor publication trends by state. | State and domain aggregates only. |
| 3 | Compare government innovation grant allocation by research domain and institution type. | Funding aggregates by domain and institution type. |
| 4 | Which ministries or agencies appear together most often in funded research collaborations? | Agency collaboration counts without individual profiles. |
| 5 | Which states have high publication output but low patent commercialization in clean energy? | State-level gap analysis only. |
| 6 | Rank institutions by publications per crore of government innovation grant funding. | Institution-level ratio; no individual researcher fields. |
| 7 | Show aggregate TRL distribution for market-ready technologies by institution type. | TRL histogram by institution type. |
| 8 | Which research domains have rising output but declining funding over the last five years? | Domain-level trend and funding comparison. |
| 9 | Identify national collaboration clusters between IITs, NITs, and state universities in healthcare AI. | Institution-cluster summary only. |
| 10 | Generate a policy summary of underfunded high-output research areas without showing individual researcher details. | Policy narrative with anonymized aggregates. |

**Verification note:** Responses must not include email, phone, Aadhaar, PAN, or individual researcher contact fields.
