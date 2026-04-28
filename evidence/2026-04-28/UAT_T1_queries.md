# UAT Query Set - Tier 1 Researcher

**Persona:** Professor's assistant / IIT-GN research support
**Access assertion:** Tier 1 may view researcher-level details, citations, audit trail references, and approved contact fields.

| # | Query | Expected tier filtering |
|---|---|---|
| 1 | How many IIT Gandhinagar publications were published in 2023, grouped by research area? | Full publication aggregates with citations. |
| 2 | Which researchers at IIT Gandhinagar published on hydrogen catalysis between 2020 and 2024, and what are their email contacts? | Researcher names and approved contact fields allowed for Tier 1. |
| 3 | Show the top 10 Computer Science researchers by publication count since 2021, including institution, h-index, and recent paper titles. | Researcher-level ranking allowed with cited publication evidence. |
| 4 | Find researchers in Gujarat working on robotics who also have patents or funded projects. | Joined researcher, patent, and project details allowed. |
| 5 | Which labs collaborate most often with researchers publishing in machine learning? | Lab and researcher collaboration details allowed. |
| 6 | Compare publication growth for IIT Gandhinagar, IIT Bombay, and IIT Madras from 2019 to 2024. | Institution and publication time-series allowed. |
| 7 | List researchers whose funding increased after they started publishing in renewable energy topics. | Researcher-level funding and publication trend allowed. |
| 8 | Show co-author networks for quantum computing researchers and identify the most connected collaborator. | Co-author graph and named collaborators allowed. |
| 9 | Which institutions have researchers working at TRL 6 or above in semiconductor or chip design? | TRL-stage joins and researcher context allowed. |
| 10 | For hydrogen research, show publications, active researchers, grants, patents, and likely collaboration opportunities. | Multi-hop researcher, publication, grant, patent, and institution synthesis allowed. |

**Coverage:** Basic count, multi-table joins, filter plus aggregate, collaboration graph, TRL alias path, funding, patents, and complex synthesis.
