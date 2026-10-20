# siyoung-personal-reader

A personal, non-commercial, **read-only** Reddit digest script for one person (u/siyoung_reader2741).

- Reddit "script" OAuth app, scope `read` only. It never posts, comments, votes, messages, or moderates.
- Fixed subreddits: r/iPhoneDuo, r/iphone, r/apple, r/TeslaMotors.
- Endpoints: `/r/{sub}/new`, `/r/{sub}/search` (restrict_sr), and `/api/info` for deletion checks.
- Limits: at most 2 runs/day, 150 requests/run, at most 10 requests/minute. It honors `X-Ratelimit-*` headers.
- User-Agent: `macos:siyoung-personal-reader:v0.1.0 (by /u/siyoung_reader2741)`
- Data: stores only id, title, text, score, and time on the local disk. It purges after 7 days and drops deleted or removed items.
- No redistribution, no resale, no AI/ML training, no user profiling, no de-anonymization.

Complies with Reddit's Responsible Builder Policy, Developer Terms, and Data API Terms.
