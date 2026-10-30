"""Preliminary keyword coverage of the topics behind the proposed LLM features.

For each topic, reports the share of matched previews whose text contains at least one
keyword (case-insensitive). These are rough proxies used only in the Milestone 1 table
"Preliminary keyword coverage" (Section 3.4); they are NOT the LLM features themselves.

Two versions are reported:
  * "strict" - whole-word matching (so "form" does not match "performance" or "formation").
               THESE are the figures used in the document (30%, 26%, 41%, 26%).
  * "loose"  - plain substring matching, kept as a sensitivity check; it overcounts
               "Recent form" because "form" appears inside other words.

Usage: python3 keyword_coverage.py <previews_with_results.csv> <report_dir>
Writes: <report_dir>/keyword_coverage.csv and <report_dir>/keyword_coverage_per_preview.csv
"""
import sys
from pathlib import Path
import pandas as pd

in_csv, report_dir = Path(sys.argv[1]), Path(sys.argv[2])
report_dir.mkdir(parents=True, exist_ok=True)

# Substring patterns (sensitivity check). "injur" matches injury/injured/injuries, etc.
LOOSE = {
    "Recent form": r"form|unbeaten|winless|run of|losing streak|winning streak|consecutive|in a row",
    "Injury or availability": r"injur|fitness|doubt|suspen|absen|ruled out|hamstring|knee|ankle|sidelined"
                              r"|without (?:the )?(?:injured|suspended)",
    "Motivation or stakes": r"relegat|title|top four|top-four|europe|champions league|survival|must-win"
                            r"|desperate|dead rubber|safety",
    "Managerial uncertainty": r"manager|sack|pressure|under-fire|interim|caretaker",
}
# Whole-word versions (used in the document): keyword stems may still extend (injur -> injury),
# but cannot start mid-word, and "form" must be the whole word.
STRICT = {
    "Recent form": r"\bform\b|\bunbeaten\b|\bwinless\b|\brun of\b|\blosing streak\b|\bwinning streak\b"
                   r"|\bconsecutive\b|\bin a row\b",
    "Injury or availability": r"\binjur\w*|\bfitness\b|\bdoubt\w*|\bsuspen\w*|\babsen\w*|\bruled out\b"
                              r"|\bhamstring\w*|\bknee\w*|\bankle\w*|\bsidelined\b",
    "Motivation or stakes": r"\brelegat\w*|\btitle\b|\btop[- ]four\b|\beurope\w*|\bchampions league\b"
                            r"|\bsurvival\b|\bmust-win\b|\bdesperate\b|\bdead rubber\b|\bsafety\b",
    "Managerial uncertainty": r"\bmanager\w*|\bsack\w*|\bpressure\b|\bunder-fire\b|\binterim\b|\bcaretaker\b",
}

df = pd.read_csv(in_csv)
text = df["Text"].fillna("").str.lower()
n = len(df)

rows, per_preview = [], df[["MatchID"]].copy()
for topic in LOOSE:
    loose_hit = text.str.contains(LOOSE[topic], regex=True)
    strict_hit = text.str.contains(STRICT[topic], regex=True)
    per_preview[f"{topic} (loose)"] = loose_hit
    per_preview[f"{topic} (strict)"] = strict_hit
    rows.append({
        "Topic": topic,
        "Previews": n,
        "LooseMatches": int(loose_hit.sum()),
        "LooseShare": round(loose_hit.mean(), 3),
        "StrictMatches": int(strict_hit.sum()),
        "StrictShare": round(strict_hit.mean(), 3),
        "LoosePattern": LOOSE[topic],
    })

out = pd.DataFrame(rows)
out.to_csv(report_dir / "keyword_coverage.csv", index=False)
per_preview.to_csv(report_dir / "keyword_coverage_per_preview.csv", index=False)

print(f"Keyword coverage over {n} matched previews")
for r in rows:
    print(f"  {r['Topic']:<24} loose {r['LooseShare']:.1%} ({r['LooseMatches']})"
          f"   strict {r['StrictShare']:.1%} ({r['StrictMatches']})")
