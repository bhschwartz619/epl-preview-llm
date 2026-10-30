"""Join Guardian match previews (Beal et al.) to EPL results from football-data.co.uk
and compute the last-3-match baseline features.

Usage: python3 build_dataset.py <guardian_csv> <results_dir> <out_dir>

<results_dir> must hold the five Premier League files from football-data.co.uk, each
downloaded as E0.csv and renamed by season: E0_1314.csv, E0_1415.csv, E0_1516.csv,
E0_1617.csv, E0_1718.csv.
"""
import sys
from pathlib import Path
import pandas as pd

guardian_csv, results_dir, out_dir = map(Path, sys.argv[1:4])
out_dir.mkdir(parents=True, exist_ok=True)

# Seasons covered by the Guardian previews. The baseline uses only earlier matches in the
# same season, so no earlier season is needed.
SEASONS = ["1314", "1415", "1516", "1617", "1718"]
RESULT_COLS = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]


def parse_dates(s):
    """football-data dates are day-first: dd/mm/yy or dd/mm/yyyy (ISO also accepted)."""
    s = s.astype(str).str.strip()
    out = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    out = out.fillna(pd.to_datetime(s, format="%d/%m/%y", errors="coerce"))
    out = out.fillna(pd.to_datetime(s, format="%Y-%m-%d", errors="coerce"))
    return out


def load_season(code):
    path = results_dir / f"E0_{code}.csv"
    if not path.exists():
        sys.exit(f"Missing {path}: download E0.csv for season {code} from football-data.co.uk "
                 f"and save it as E0_{code}.csv")
    # Some football-data files carry extra columns or odd characters; read only what we need.
    df = pd.read_csv(path, usecols=RESULT_COLS, encoding="latin-1")
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTR"])  # drop blank trailing rows
    df["Date"] = parse_dates(df["Date"])
    if df["Date"].isna().any():
        sys.exit(f"Unparseable dates in {path}")
    # Check the file really is this season: every match must fall between July of the first
    # year and July of the second (catches a file saved under the wrong season's name).
    start = pd.Timestamp(f"20{code[:2]}-07-01")
    end = pd.Timestamp(f"20{code[2:]}-07-31")
    first, last = df["Date"].min().date(), df["Date"].max().date()
    print(f"Loaded {path.name}: {len(df)} matches, {first} to {last}")
    if df["Date"].lt(start).any() or df["Date"].gt(end).any():
        sys.exit(f"{path.name} does not contain season 20{code[:2]}-{code[2:]}: its matches run from "
                 f"{first} to {last}. It was probably saved under the wrong name; re-download "
                 f"season 20{code[:2]}/20{code[2:]} and save it as {path.name}.")
    if len(df) != 380:
        print(f"WARNING: {path} has {len(df)} matches (a full EPL season has 380)")
    return df.assign(Season=f"20{code[:2]}-{code[2:]}")

# Guardian spelling -> football-data spelling (EPL clubs only; anything unmapped is non-EPL)
NAME_MAP = {
    "AFC Bournemouth": "Bournemouth", "Bournemouth": "Bournemouth",
    "Arsenal": "Arsenal", "Aston Villa": "Aston Villa",
    "Brighton": "Brighton", "Brighton & Hove Albion": "Brighton",
    "Burnley": "Burnley", "Cardiff": "Cardiff", "Cardiff City": "Cardiff",
    "Chelsea": "Chelsea", "Crystal Palace": "Crystal Palace", "Everton": "Everton",
    "Fulham": "Fulham", "Huddersfield": "Huddersfield", "Huddersfield Town": "Huddersfield",
    "Hull": "Hull", "Hull City": "Hull", "Leicester": "Leicester", "Leicester City": "Leicester",
    "Liverpool": "Liverpool", "Man City": "Man City", "Manchester City": "Man City",
    "Manchester city": "Man City", "Man Utd": "Man United", "Manchester United": "Man United",
    "Middlesbrough": "Middlesbrough", "Newcastle": "Newcastle", "Newcastle United": "Newcastle",
    "Newcastle Utd": "Newcastle", "Norwich City": "Norwich", "QPR": "QPR",
    "Queens Park Rangers": "QPR", "Southampton": "Southampton", "Stoke": "Stoke",
    "Stoke City": "Stoke", "Sunderland": "Sunderland", "Swansea": "Swansea",
    "Swansea City": "Swansea", "Spurs": "Tottenham", "Tottenham": "Tottenham",
    "Tottenham Hostpur": "Tottenham", "Tottenham Hotspur": "Tottenham", "Watford": "Watford",
    "West Brom": "West Brom", "West Bromwich": "West Brom", "West Bromwich Albion": "West Brom",
    "West Ham": "West Ham", "West Ham United": "West Ham",
}

# ---------- results + last-3 baseline ----------
res = pd.concat([load_season(s) for s in SEASONS], ignore_index=True)
res = res.sort_values("Date", kind="stable").reset_index(drop=True)
res["FixtureID"] = res.index

# team-match long table to compute points from each team's previous 3 league games (same season)
long = pd.concat([
    pd.DataFrame({"FixtureID": res.FixtureID, "Date": res.Date, "Season": res.Season, "Team": res.HomeTeam,
                  "Pts": res.FTR.map({"H": 3, "D": 1, "A": 0}), "GD": res.FTHG - res.FTAG}),
    pd.DataFrame({"FixtureID": res.FixtureID, "Date": res.Date, "Season": res.Season, "Team": res.AwayTeam,
                  "Pts": res.FTR.map({"A": 3, "D": 1, "H": 0}), "GD": res.FTAG - res.FTHG}),
]).sort_values(["Team", "Date", "FixtureID"])
g = long.groupby(["Team", "Season"])
long["Last3Pts"] = g["Pts"].transform(lambda s: s.shift(1).rolling(3, min_periods=3).sum())
long["Last3GD"] = g["GD"].transform(lambda s: s.shift(1).rolling(3, min_periods=3).sum())
home_f = long.rename(columns={"Team": "HomeTeam", "Last3Pts": "HomeLast3Pts", "Last3GD": "HomeLast3GD"})[
    ["FixtureID", "HomeTeam", "HomeLast3Pts", "HomeLast3GD"]]
away_f = long.rename(columns={"Team": "AwayTeam", "Last3Pts": "AwayLast3Pts", "Last3GD": "AwayLast3GD"})[
    ["FixtureID", "AwayTeam", "AwayLast3Pts", "AwayLast3GD"]]
res = res.merge(home_f, on=["FixtureID", "HomeTeam"]).merge(away_f, on=["FixtureID", "AwayTeam"])

# ---------- previews ----------
gd = pd.read_csv(guardian_csv)
n_raw = len(gd)
gd["PubDate"] = pd.to_datetime(gd["Date"].str.replace(r"\s+\d{1,2}\.\d{2}\s+\w+$", "", regex=True),
                               format="%a %d %b %Y", errors="coerce")
bad_date = gd.PubDate.isna()
gd["HomeStd"] = gd["Home"].map(NAME_MAP)
gd["AwayStd"] = gd["Away"].map(NAME_MAP)

# Match each preview to the first league fixture between the same teams 0-7 days after publication
cand = gd.merge(res, left_on=["HomeStd", "AwayStd"], right_on=["HomeTeam", "AwayTeam"], how="left",
                suffixes=("", "_res"))
cand["Lag"] = (cand["Date_res"] - cand["PubDate"]).dt.days
cand = cand[(cand.Lag >= 0) & (cand.Lag <= 7)].sort_values(["MatchID", "Lag"]).drop_duplicates("MatchID")

merged = gd.merge(cand[["MatchID", "FixtureID", "Date_res", "Lag", "FTHG", "FTAG", "FTR",
                        "HomeLast3Pts", "HomeLast3GD", "AwayLast3Pts", "AwayLast3GD"]],
                  on="MatchID", how="left")

# ---------- diagnostics ----------
non_epl = merged.HomeStd.isna() | merged.AwayStd.isna()
unmatched_epl = merged.FixtureID.isna() & ~non_epl
no_text = merged.Text.isna()
dup_fixture = merged.FixtureID.notna() & merged.duplicated("FixtureID", keep=False)

final = merged[merged.FixtureID.notna() & ~no_text].copy()
final = final.sort_values("Lag").drop_duplicates("FixtureID").sort_values("Date_res")
has_base = final[["HomeLast3Pts", "AwayLast3Pts"]].notna().all(axis=1)

stats = {
    "raw_previews": n_raw,
    "non_epl_previews": int(non_epl.sum()),
    "epl_previews_unmatched": int(unmatched_epl.sum()),
    "missing_text": int(no_text.sum()),
    "unparseable_date": int(bad_date.sum()),
    "previews_sharing_a_fixture": int(dup_fixture.sum()),
    "final_matches": len(final),
    "final_with_last3_baseline": int(has_base.sum()),
    "lag_days_distribution": final.Lag.value_counts().sort_index().to_dict(),
    "outcome_share": final.FTR.value_counts(normalize=True).round(3).to_dict(),
    "by_season": final.Season.value_counts().sort_index().to_dict(),
    "date_range": (str(final.Date_res.min().date()), str(final.Date_res.max().date())),
}
for k, v in stats.items():
    print(f"{k}: {v}")

final_out = final.rename(columns={"Date_res": "MatchDate"})[
    ["MatchID", "FixtureID", "Season", "PubDate", "MatchDate", "Lag", "Home", "Away", "HomeStd", "AwayStd",
     "HomeLast3Pts", "HomeLast3GD", "AwayLast3Pts", "AwayLast3GD", "FTHG", "FTAG", "FTR", "Text"]]
final_out.to_csv(out_dir / "previews_with_results.csv", index=False)
merged[unmatched_epl].drop(columns=["Text"]).to_csv(out_dir / "unmatched_epl_previews.csv", index=False)
merged[non_epl][["MatchID", "Home", "Away", "Date", "Season"]].to_csv(out_dir / "non_epl_previews.csv", index=False)
res.to_csv(out_dir / "epl_results_2013_2018.csv", index=False)

# One row per excluded preview with the reason, so every exclusion can be inspected.
reason = pd.Series(pd.NA, index=merged.index, dtype="object")
reason[no_text & merged.FixtureID.notna()] = "missing text"
reason[unmatched_epl & bad_date.reindex(merged.index, fill_value=False)] = "unparseable publication date"
reason[unmatched_epl & reason.isna()] = "no league fixture 0-7 days after publication (e.g. cup tie)"
reason[non_epl] = "non-EPL team (cup or European match)"
excl = merged.loc[reason.notna(), ["MatchID", "Home", "Away", "Date", "Season"]].assign(Reason=reason[reason.notna()])
excl.to_csv(out_dir / "excluded_previews.csv", index=False)

# The team-name mapping actually used, with how many previews use each spelling.
used = pd.concat([gd["Home"], gd["Away"]]).value_counts()
pd.DataFrame([{"GuardianSpelling": k, "StandardName": v, "TimesUsed": int(used.get(k, 0))}
              for k, v in sorted(NAME_MAP.items())]).to_csv(out_dir / "team_name_map.csv", index=False)
