# Known Channel Manager risks

Verified against FM `b41857a01400859d5c20940ced23f7d7aded6a99` on 2026-07-12. Reverify against HEAD.

| Severity | Finding | Evidence |
|---|---|---|
| P0 | Backend writes lack effective JWT/RBAC; frontend local-storage protection is cosmetic. | `AuthContext.tsx:27-61`; `apiClient.ts:20-40`; write routes in `promotions.py`, `booking.py`, `marketing_articles.py` |
| P0 | Location-only flags are overwritten to Shop=true by a second session/write. | `sheet_service.py:786-819`; `booking.py:61-79` |
| P0 | Campaign, promotion, allocation, and publication have no shared release/version/approval/rollback. | `models/marketing.py:47-87,140-160`; `IndexStorage.tsx:165-172` |
| P0 | Channel update and promotion assignment are separate live writes, allowing partial publication. | `ChannelManager.tsx:112-133`; `booking.py:142-190` |
| P0 | Public promotion index reads `public/data`; sync writes `src/data` and may export drafts if no published rows exist. | website `data-fetcher.ts:8-12`; `sync_promotions.ts:49-52,96-132` |
| P1 | Empty channels default to Shop, so true unpublish fails. | `sheet_service.py:649-654,786-787` |
| P1 | Rentable-status vocabularies differ between read and oversold validation. | `sheet_service.py:530-544,617-619,732-765` |
| P1 | Promotion clear sends null/empty string while backend requires string. | `ChannelManager.tsx:123-130`; `PricingDashboard.tsx:246-251`; `promotions.py:10-15` |
| P1 | Group display uses one unit and hides mixed promotion assignments. | `sheet_service.py:655-663` |
| P1 | Store selection is not location-driven; ALL becomes TEST_STORE. | `ChannelManager.tsx:112-121,188-196` |
| P1 | Channel price is not persisted; website reads inventory rent. | `ChannelManager.tsx:112-121,334-342`; `sheet_service.py:699-821`; `website_pricing.py:572-583` |
| P1 | `published-pricing` filters active, not channel flags. | `website_pricing.py:346-377` |
| P1 | Selected IDs are count-checked but not proven eligible or store-owned. | `sheet_service.py:768-805`; `booking.py:62-78` |
| P1 | Static cards can synthesize title IDs, breaking FM attribution. | website `PromotionCard.tsx:46-72` |

Add failing tests for auth, channel flags, promotion removal, store ownership, status vocabulary, idempotency, propagation, and rollback before new workflow UI.
