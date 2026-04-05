# TACHY SEO PRO v4.0 Architecture

## 1) Client-domain content architecture
- School profile is persisted in `client_schools`.
- Client pages are generated via per-type blueprint in `generate_client_page()`.
- Each page receives school specificity score, similarity checks, canonical/indexing decision, and publish safety validation.
- Persistence is captured in `client_pages`, `client_similarity_log`, `canonical_decisions`, and `client_safety_log`.

## 2) Safe backlink / brand-link rules
- Max TACHY links per client page: 2.
- Allowed anchors are branded only.
- Default rel on client pages is nofollow.
- Unsafe exact-match or over-count triggers manual_review + noindex.

## 3) Indexing and canonical flow (text flowchart)
1. Render page from blueprint
2. Compute school specificity score
3. Compare with tachy pages and existing client pages
4. Auto-select mode
   - specificity low -> noindex support mode
   - high similarity -> canonical_to_tachy mode
   - verified case study -> case-study mode
   - else index mode
5. Run publish safety validator
6. Persist decisions and issue codes

## 4) Anchor policy table
| Anchor | Allowed | Note |
|---|---|---|
| TACHY School ERP | Yes | Branded |
| powered by TACHY School ERP | Yes | Branded badge |
| school ERP platform by TACHY | Yes | Product mention |
| learn more about TACHY School ERP | Yes | Informational CTA |
| best school ERP software | No | Exact-match commercial |
| school ERP India | No | Exact-match commercial |
| school management software | No | Exact-match commercial |

## 5) Output mode selection logic
- `auto_select_output_mode(page_type, similarity_score, school_specificity_score, proof_status)`
- Client rules:
  - specificity < 50 -> `client_noindex_support`
  - similarity > 0.75 -> `client_canonicalized`
  - case_study + non-verified -> `client_noindex_support`
  - case_study + verified -> `client_case_study`
  - announcement -> `client_announcement`
  - default -> `client_indexed`
