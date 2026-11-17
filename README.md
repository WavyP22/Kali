# Kalshi Guard v8 — Game Lines First

## What changed
- Today is the default, with Tomorrow and Choose a date separate. Time zone defaults to Eastern and can be selected manually.
- Market type defaults to **Game Lines (Spreads)**, with options for all game markets, winners and totals.
- Known long-term futures, coaching changes, expansion teams and unrecognized market formats are excluded from daily and unverified-start lists.
- Game starts must be confirmed from a timestamp or an exact two-team ESPN schedule match. Unknown starts do not appear as same-day plays.
- Advanced scan sliders are collapsed in the sidebar.
- Suggested 2–6 pick combinations are **hypothetical research groups**, not verified executable Kalshi combos. There is no independent predictive model, validated value ranking or trading.

## Deploy
Upload all files in this folder to the root of your existing GitHub repo, replacing matching names. Streamlit entrypoint: `app.py`.

## Limitations
Game-line recognition uses conservative text patterns. Some legitimate game lines may be omitted, and some non-game propositions may require further filtering. ESPN scoreboard is unofficial and exact matchup matching may fail. A market's close time is not a reliable game start. Kalshi may rate-limit requests. Tests do not validate live Kalshi/ESPN behavior.
