# 2.19.5 deferred fallback acquisition

Frozen 2.19.3 experiment remains unchanged. Candidate 2.19.4 changes retained; preparation now only requires original assets to be downloaded. Unused render_fallback metadata stays in the inventory without a path or implementation eligibility. Unknown/missing originals still block; downloaded assets still receive hash/dimension verification. Actual use still requires existing contract asset pins and authorization.

Local replay of identical source: 8 originals, 37 deferred fallbacks, zero preparation issues. Avoided fallback bytes: 444712. Preparation ~0.34 seconds. This proves the dependency was removed, NOT minutes saved in a fresh network/model run. Most previous delay cannot be attributed to byte volume alone: tool exchanges, truncated bundle recovery and model processing amplified it.

215 regression tests passed. No independent model rerun this turn; no new fidelity claim. Next end-to-end test should freeze this candidate, count all startup through final outputs, and compare actual tool counts and uncached token usage along with visual quality.
