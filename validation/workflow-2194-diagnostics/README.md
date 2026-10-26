# 2.19.4 workflow diagnosis

Baseline preserved: validation/retest-2193-sol56/frozen-skill and its run.

Verified root causes:
1. pending-assets.json used version/pending_assets instead of policy/nodes. The loader silently denied it. New schema validation rejects malformed policy with an actionable template reference.
2. pending_allowed rejected every node with asset_ids. Actual Wifi and Cellular references are render_fallback, not original assets. Hashed reinspection evidence can now establish fallback-only IDs; unknown/original types, changed evidence, and existing paths still reject placeholder authorization.
3. Graphic audit explicitly allowed system_chrome with a reason, contrary to no invented icons. Application-drawn chrome now requires source geometry just like other graphics.
4. stop freezes session time but cannot prevent direct shell writes. Entry instructions now require final preview/report before stop and full external timestamp accounting if artifacts change afterward. No claim of filesystem enforcement.

Verification: replay.json demonstrates the two actual blocked source nodes now reach authorized placeholder disposition without geometry gaps. This is a source-path replay, NOT a full page acceptance. Original assets, unknown types and stale hashes are negative tests. Existing experiment remains failed and unmodified.

Efficiency limitation: current preparation still reconciles all manifest entries, including fallback evidence. Large MCP bundle/variant retrieval and cumulative context remain unresolved performance costs; no ten-minute claim. Avoid attributing the entire failure to model capability or claiming schema repair alone improves visual fidelity.
