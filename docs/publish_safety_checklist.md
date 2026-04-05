# Publish Safety Checklist — TACHY v4.0

## A) TACHY main-domain pages
- [ ] Quality gate passed
- [ ] Schema semantic validation passed
- [ ] No risky unsupported claims
- [ ] AggregateRating only when verified proof exists
- [ ] VideoObject only with normalized valid YouTube ID
- [ ] Canonical + robots tags correct
- [ ] If failed checks: noindex + manual_review + issue codes logged

## B) Client-domain pages
- [ ] School specificity score >= 60
- [ ] TACHY links <= 2
- [ ] Anchor text validation passed (branded only)
- [ ] Similarity with tachy page < 0.65 for index mode
- [ ] If similarity 0.65-0.84 -> canonical_to_tachy or noindex
- [ ] LocalBusiness for TACHY not present on client domain
- [ ] Publish safety validator passed
- [ ] Canonical decision logged
- [ ] If failed checks: noindex + manual_review + client_safety_log entry
