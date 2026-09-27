# FAQ Bot Fixture

A minimal FAQ-based retrieval fixture for testing the adapter-scaffolder skill.

This fixture is **intentionally different** from `toy_rag_fixture`:
- Uses a different data shape (FAQ entries with `q`/`a`/`category` fields)
- Uses TF-IDF–style scoring instead of keyword intersection
- Returns contexts as objects that need transformation (not plain strings)
- Has a non-standard API shape (`{"response": ..., "sources": [...]}`)

This forces the adapter scaffolder to do real work — it cannot reuse the
`toy_rag_fixture` adapter verbatim.
