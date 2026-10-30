"""Descriptive statistics quoted in the Milestone 1 document (Sections 3 and 4).

Reads the raw Guardian file and the outputs of build_dataset.py, and prints every
computed figure with the document section it supports.

Usage: python3 data_summary.py <GuardianReportsAll.csv> <build_output_dir> <report_dir>
Writes: <report_dir>/data_summary.txt
"""
import sys
from pathlib import Path
import pandas as pd

raw_csv, build_dir, report_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
report_dir.mkdir(parents=True, exist_ok=True)

raw = pd.read_csv(raw_csv)
final = pd.read_csv(build_dir / "previews_with_results.csv")
results = pd.read_csv(build_dir / "epl_results_2013_2018.csv")
excl = pd.read_csv(build_dir / "excluded_previews.csv")
names = pd.read_csv(build_dir / "team_name_map.csv")

lines = []
def say(section, label, value):
    lines.append(f"[{section}] {label}: {value}")

def words(s):
    return s.dropna().str.split().str.len()

# ---- 3.1 Guardian previews (raw download) ----
say("3.1", "Previews in downloaded CSV", f"{len(raw):,}")
say("3.1", "Seasons in downloaded CSV", ", ".join(sorted(raw["Season"].unique())))
say("3.1", "Previews per season (raw)", raw["Season"].value_counts().sort_index().to_dict())
rw = words(raw["Text"])
say("3.1", "Words per preview, raw (median / min / max / mean)",
    f"{rw.median():.0f} / {rw.min()} / {rw.max()} / {rw.mean():.1f}")
fw = words(final["Text"])
say("3.1, 4.6", "Words per preview, matched set (median / min / max / mean)",
    f"{fw.median():.0f} / {fw.min()} / {fw.max()} / {fw.mean():.1f}")
signed = final["Text"].str.strip().str.contains(r"[A-Z][a-z]+ [A-Z][a-z]+$", regex=True).mean()
say("3.1", "Matched previews ending in a two-word name (journalist sign-off)", f"{signed:.1%}")

# ---- 3.2 Results ----
say("3.2", "EPL matches in results data", f"{len(results):,}")
say("3.2", "Results seasons", ", ".join(sorted(results["Season"].unique())))
shares = final["FTR"].value_counts(normalize=True)
say("3.2, 4.1", "Outcome shares in matched set (H / A / D)",
    f"{shares['H']:.1%} / {shares['A']:.1%} / {shares['D']:.1%}")

# ---- 3.3 Join and validation ----
used = names[names["TimesUsed"] > 0]
say("3.3 step 1", "Guardian spellings mapped -> standard club names",
    f"{len(used)} -> {used['StandardName'].nunique()}")
lag = final["Lag"]
say("3.3 step 2", "Days from publication to match", lag.value_counts().sort_index().to_dict())
say("3.3 step 2", "Share played the day after publication", f"{(lag == 1).mean():.1%}")
say("3.3 step 2", "Maximum lag (days)", int(lag.max()))
say("3.3 step 2", "Fixtures matched by more than one preview", int(final["FixtureID"].duplicated().sum()))
base = final[["HomeLast3Pts", "AwayLast3Pts"]].notna().all(axis=1)
say("3.3 step 3", "Matched matches lacking full 3-match baseline", int((~base).sum()))

# Exclusion funnel (table in 3.3)
counts = excl["Reason"].value_counts().to_dict()
non_epl = counts.get("team not in the EPL during 2013-18", 0)
no_fix = (counts.get("no league fixture between the same teams 0-7 days after publication", 0)
          + counts.get("unparseable publication date", 0))
no_text = counts.get("missing text", 0)
say("3.3 table", "Downloaded previews", f"{len(raw):,}")
say("3.3 table", f"After removing non-EPL ({non_epl})", f"{len(raw) - non_epl:,}")
say("3.3 table", f"After removing no league fixture within 7 days ({no_fix}, incl. "
                 f"{counts.get('unparseable publication date', 0)} malformed date)", f"{len(raw) - non_epl - no_fix:,}")
say("3.3 table", f"After removing missing text ({no_text})", f"{len(raw) - non_epl - no_fix - no_text:,}")
say("3.3 table", "Rows in analysis file (check)", f"{len(final):,}")
say("3.3 table", "Matches with full 3-match baseline", f"{int(base.sum()):,}")

# ---- 4.4 Modeling split ----
model = final[base]
train = model[model["Season"] != "2017-18"]
test = model[model["Season"] == "2017-18"]
say("4.4", "Train matches (2013-14 to 2016-17, with baseline)", f"{len(train):,}")
say("4.4", "Test matches (2017-18, with baseline)", f"{len(test):,}")
say("4.4", "Test matches (2017-18, all matched)", f"{(final['Season'] == '2017-18').sum():,}")
say("4.1", "Always-predict-home accuracy, test set", f"{(test['FTR'] == 'H').mean():.1%}")
say("4.1", "Always-predict-home accuracy, all matched", f"{(final['FTR'] == 'H').mean():.1%}")
say("4.3", "Match date range", f"{final['MatchDate'].min()} to {final['MatchDate'].max()}")

report = "\n".join(lines)
(report_dir / "data_summary.txt").write_text(report + "\n")
print(report)
