# Milestone 1 — data and reproducible calculations

Every computed number in the Milestone 1 document comes from the scripts in this folder.
`FIGURES.md` maps each figure in the document to the report line that produces it.

## 1. Get the data (manual download)
1. **Guardian previews:** download `GuardianReportsAll.csv` from
   https://github.com/RyanBeal7/GuardianPreviewData and save it as `data/GuardianReportsAll.csv`.
2. **Match results:** on https://www.football-data.co.uk/englandm.php, download the
   **Premier League** results file (`E0.csv`) for each of these five seasons, and save each one
   in `data/raw_results/` renamed by season:

   | Season | Save as |
   | --- | --- |
   | 2013/2014 | `data/raw_results/E0_1314.csv` |
   | 2014/2015 | `data/raw_results/E0_1415.csv` |
   | 2015/2016 | `data/raw_results/E0_1516.csv` |
   | 2016/2017 | `data/raw_results/E0_1617.csv` |
   | 2017/2018 | `data/raw_results/E0_1718.csv` |

   Every season downloads with the same name, `E0.csv`, so rename each file right after downloading it.

After both downloads, `data/` should contain `GuardianReportsAll.csv` and `raw_results/` with the five files.

## 2. Reproduce everything
Requires Python 3 with pandas (`pip install pandas`). From this folder, run these three
commands in order. `build_dataset.py` must run first, because it creates the analysis file
the other two read. On Windows, type `python` instead of `python3`.

```
python3 scripts/build_dataset.py data/GuardianReportsAll.csv data/raw_results data
python3 scripts/data_summary.py data/GuardianReportsAll.csv data reports
python3 scripts/keyword_coverage.py data/previews_with_results.csv reports
```

The first command prints the join diagnostics to the screen; the figures used in the document
are saved in `reports/data_summary.txt` and `reports/keyword_coverage.csv`.

## Scripts (in the order they run)
| Script | What it does | Writes |
| --- | --- | --- |
| `scripts/build_dataset.py` | Standardizes team names, matches each preview to its fixture, computes last-3-match baseline | `data/previews_with_results.csv` and the files below |
| `scripts/data_summary.py` | All descriptive statistics in Sections 3 and 4 | `reports/data_summary.txt` |
| `scripts/keyword_coverage.py` | Preliminary keyword coverage table (Section 3.4) | `reports/keyword_coverage.csv`, `reports/keyword_coverage_per_preview.csv` |

## Data files
- `data/previews_with_results.csv` — **the analysis file.** 1,409 EPL matches (Feb 2014 – May 2018): preview text, standardized teams, match date, baseline features, result.
  - `HomeLast3Pts`, `AwayLast3Pts`: league points from each team's previous 3 matches in the same season (blank for a team's first 3 games; 1,293 rows have both).
  - `HomeLast3GD`, `AwayLast3GD`: goal difference over the same 3 matches.
  - `FTHG`, `FTAG`, `FTR`: full-time home goals, away goals, result (H/D/A) — the target.
  - `Lag`: days between article publication and the match.
- `data/GuardianReportsAll.csv` — original previews (1,506 rows; text owned by The Guardian).
- `data/raw_results/` — EPL results 2013–14 to 2017–18 from Football-Data.co.uk (1,900 matches).
- `data/epl_results_2013_2018.csv` — combined results with baseline features for every fixture.
- `data/excluded_previews.csv` — the 97 excluded previews, each with its reason.
- `data/team_name_map.csv` — every Guardian team spelling, its standard name, and how often it appears.
- `data/non_epl_previews.csv`, `data/unmatched_epl_previews.csv` — exclusion detail by category.

## Join logic
Team names are mapped to Football-Data spellings; each preview is matched to the first league
fixture between the same home and away teams 0–7 days after publication. The baseline uses only
matches earlier in the same season, so no future information enters a match's features.
