# GAIL Procurement Analytics — Complete Power BI Build Guide

Everything you need to build the 3-page dashboard from a blank Power BI Desktop
file to a finished, polished report: data import, data model, every DAX measure,
GAIL's brand palette, and page-by-page visual instructions.

---

## Part 1 — Design System

### 1.1 Color Palette (sampled directly from GAIL's IEW 2027 poster)

An earlier version of this guide used colors from a third-party logo-color
database, which only captured the isolated logo mark (red/gold/black). That
undersells GAIL's actual current brand system — real marketing material
(the India Energy Week 2027 poster) shows **forest green as the dominant
brand color**, fitting their "clean energy" positioning, with gold and navy
as supporting colors and the logo's red reserved as a small accent. These
hex values were sampled directly from the poster image, not guessed:

| Role | Color | Hex | Use |
|---|---|---|---|
| Brand Primary | GAIL Forest Green | `#3F6B4A` | Top nav bar, primary chart series, **compliant/good indicators** |
| Brand Text | GAIL Navy | `#243450` | Headlines, body text, axis labels (matches the poster's headline text) |
| Brand Accent | GAIL Gold | `#E8C13C` | Warnings, medium-risk, secondary series (from the logo oval + IEW sunburst) |
| Brand Alert | GAIL Red | `#C0392B` | **High-risk/non-compliant indicators** (from the logo mark itself) |
| Tint | Sage Green | `#B9C8A2` | Icon backgrounds, light card tints (from the poster's icon circles) |
| Background | Cream | `#F2F3E9` | Report canvas background (matches the poster exactly, not a generic gray) |
| Panel/Card | White | `#FFFFFF` | Visual containers |
| Muted Text | Warm Gray | `#66705F` | Labels, captions, secondary text (greenish undertone to match the palette, not a cold gray) |
| Hairline | Border | `#E1E4D6` | Card borders, gridlines |

**Design rationale to note in your own writeup:** this is a genuine improvement
over guessing colors from a logo file — the palette is pulled from GAIL's
actual current visual identity, not an isolated brand mark. It also produces
a more natural semantic mapping than the red-primary version: green is both
GAIL's dominant brand color *and* the conventional "good/compliant" signal,
so they reinforce each other instead of competing. Red is still reserved for
risk/alert, which now reads as a deliberate accent (matching how sparingly
GAIL itself uses red — only in the logo mark) rather than the dominant color
fighting against standard dashboard conventions.

### 1.2 Typography


Power BI Desktop only reliably renders fonts already installed on your system.
Don't risk a custom font failing to render — use Power BI's built-in Segoe UI family:

| Role | Font | Weight |
|---|---|---|
| Page titles / headers | Segoe UI Semibold | Bold |
| KPI card numbers | Segoe UI Semibold | Bold, 28-32pt |
| Body / axis labels | Segoe UI | Regular, 9-10pt |
| Table data | Segoe UI | Regular, 9pt |

### 1.3 Logo

Do not use an AI-generated or reconstructed version of GAIL's logo — it's
trademarked IP. Instead:

1. Download the official logo yourself from GAIL's investor relations or media
   page (gailonline.com) — use the PNG/SVG they publish, not a screenshot.
2. In Power BI: **Insert → Image**, place it top-left of the report canvas,
   sized to ~120×40px, aligned with the report title.
3. **Add a small disclaimer** near the logo or in the report footer:
   *"Independent analytics project using anonymized data — not an official
   GAIL (India) Ltd. publication."* This protects you from any implication
   that this is an official company document, which matters since you're
   using their brand identity in a personal/portfolio context.

### 1.4 Layout Improvements Over the HTML Prototype

- Add a **report-level navigation bar** using bookmarks + buttons (not just
  Power BI's default page tabs) so it feels like a designed product, not a
  default report — instructions in Part 4.
- Add a **tooltip page** for the vendor risk scorecard so hovering a vendor
  shows a mini trend, not just the static table (Part 3, Page 2).
- Consistent **8px spacing grid** — align every visual to the same margins;
  Power BI's default snapping is coarse, use **View → Gridlines & Snap to Grid**.

---

## Part 2 — Data Import & Model

### Step 1: Import the cleaned data

1. Open Power BI Desktop → **Get Data → Text/CSV**.
2. Import all three cleaned files: `po_master_cleaned.csv`, `cpbg_info_cleaned.csv`,
   `cpbg_intimation_diff_cleaned.csv`.
3. In Power Query Editor, verify data types for each (Power BI sometimes
   mis-detects types on import):
   - Date columns (`PO DATE`, `PR Date`, `Term End`, etc.) → **Date**
   - `cpbg_value_compliant`, `cpbg_duration_compliant`, `intimation_compliant` → **True/False**
   - Monetary columns (`PO Basic Value (INR)`, `Credit Amount`) → **Decimal Number**
4. Rename the queries (right-click in the Queries pane) to clean names:
   `po_master`, `cpbg_info`, `cpbg_intimation_diff`.
5. **Close & Apply**.

### Step 2: Build relationships

Go to **Model view** and create these relationships:

| From | To | Cardinality |
|---|---|---|
| `cpbg_info[PO NO]` | `po_master[PO NO]` | Many-to-one |
| `cpbg_intimation_diff[Purchasing Document]` | `po_master[PO NO]` | Many-to-one |

(Both join keys were already aligned by the anonymization script, so this
should connect cleanly — if it doesn't, check for stray whitespace in the
`PO NO`/`Purchasing Document` columns.)

### Step 3: Add a Date table (recommended, optional)

Your FY grouping already works fine from the text column `FY` in `po_master`,
but a proper date table gives you cleaner axis formatting and unlocks
Power BI's built-in time-intelligence functions if you extend this later.

New Table (Modeling → New Table):
```dax
DateTable =
CALENDAR(DATE(2023,1,1), DATE(2027,12,31))
```
Add calculated columns to it:
```dax
Year = YEAR(DateTable[Date])
MonthName = FORMAT(DateTable[Date], "MMM")
MonthNum = MONTH(DateTable[Date])
FiscalYear =
"FY " & IF(MONTH(DateTable[Date]) >= 4, YEAR(DateTable[Date]), YEAR(DateTable[Date]) - 1)
    & "-" & RIGHT(IF(MONTH(DateTable[Date]) >= 4, YEAR(DateTable[Date]) + 1, YEAR(DateTable[Date])), 2)
FiscalMonthNum =
IF(MONTH(DateTable[Date]) >= 4, MONTH(DateTable[Date]) - 3, MONTH(DateTable[Date]) + 9)
```
Then relate `DateTable[Date]` (1) to `po_master[PO DATE]` (many) — mark
`DateTable` as a **Date Table** (Modeling → Mark as Date Table).

### Step 4: Apply the GAIL theme

Save this as `gail_theme.json` and import via **View → Themes → Browse for themes**:

```json
{
  "name": "GAIL Procurement Analytics",
  "dataColors": [
    "#3F6B4A", "#E8C13C", "#243450", "#C0392B",
    "#B9C8A2", "#66705F", "#8AA37A", "#D9C36A"
  ],
  "background": "#FFFFFF",
  "foreground": "#243450",
  "tableAccent": "#3F6B4A",
  "good": "#3F6B4A",
  "neutral": "#E8C13C",
  "bad": "#C0392B",
  "maximum": "#3F6B4A",
  "center": "#E8C13C",
  "minimum": "#F2F3E9",
  "visualStyles": {
    "*": {
      "*": {
        "background": [{ "color": { "solid": { "color": "#FFFFFF" } } }],
        "border": [{ "show": true, "color": { "solid": { "color": "#E1E4D6" } } }]
      }
    }
  }
}
```

---

## Part 3 — Every DAX Measure

Create a dedicated home for these: **Modeling → New Table**, name it
`_Measures`, and delete its placeholder column. Add every measure below to
this table (select it, then **New Measure**) so your model stays organized.

### 3.1 Page 1 — PO Lifecycle & Bottlenecks

```dax
Avg PR-to-PO Cycle Time =
AVERAGEX(
    FILTER(po_master, po_master[cycle_time_data_flag] = "OK"),
    po_master[cycle_days_pr_to_po]
)
```

```dax
Avg Approval Lag =
AVERAGE(po_master[approval_lag_days])
```

```dax
Lead Time Deviation Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(po_master), po_master[lead_time_deviation_days] > 0),
    CALCULATE(COUNTROWS(po_master), NOT(ISBLANK(po_master[lead_time_deviation_days]))),
    0
)
```

```dax
PR to Approval Days =
AVERAGEX(
    FILTER(po_master, po_master[cycle_time_data_flag] = "OK" && NOT(ISBLANK(po_master[C&P Release Date]))),
    DATEDIFF(po_master[PR Date], po_master[C&P Release Date], DAY)
)
```

```dax
Approval to PO Days =
AVERAGEX(
    FILTER(po_master, NOT(ISBLANK(po_master[C&P Release Date]))),
    DATEDIFF(po_master[C&P Release Date], po_master[PO DATE], DAY)
)
```

```dax
PO to Delivery Days =
AVERAGEX(
    FILTER(po_master, po_master[delivery_data_flag] = "OK"),
    po_master[po_to_delivery_days]
)
```

```dax
Valid Cycle PO Count =
CALCULATE(COUNTROWS(po_master), po_master[cycle_time_data_flag] = "OK")
```

```dax
Negative Cycle Flag Count =
CALCULATE(COUNTROWS(po_master), po_master[cycle_time_data_flag] <> "OK")
```

### 3.2 Page 2 — Vendor Concentration & Risk

```dax
Total PO Spend =
SUM(po_master[PO Basic Value (INR)])
```

```dax
Top 5 Vendor Share % =
VAR VendorTable =
    ADDCOLUMNS(
        VALUES(po_master[VENDOR CODE]),
        "VSpend", CALCULATE(SUM(po_master[PO Basic Value (INR)]))
    )
VAR RankedTable =
    ADDCOLUMNS(VendorTable, "Rank", RANKX(VendorTable, [VSpend], , DESC))
VAR Top5Spend = SUMX(FILTER(RankedTable, [Rank] <= 5), [VSpend])
VAR TotalSpend = SUMX(VendorTable, [VSpend])
RETURN
    DIVIDE(Top5Spend, TotalSpend)
```

```dax
HHI Index =
VAR TotalSpendSelected =
    CALCULATE(SUM(po_master[PO Basic Value (INR)]), ALLSELECTED(po_master[VENDOR CODE]))
VAR VendorShares =
    ADDCOLUMNS(
        VALUES(po_master[VENDOR CODE]),
        "VShare", DIVIDE(CALCULATE(SUM(po_master[PO Basic Value (INR)])), TotalSpendSelected)
    )
RETURN
    SUMX(VendorShares, [VShare] ^ 2) * 10000
```

```dax
Vendor Delay Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(po_master), po_master[lead_time_deviation_days] > 0),
    CALCULATE(COUNTROWS(po_master), NOT(ISBLANK(po_master[lead_time_deviation_days]))),
    0
)
```

```dax
Vendor Avg Deviation (Delayed Only) =
AVERAGEX(
    FILTER(po_master, po_master[lead_time_deviation_days] > 0),
    po_master[lead_time_deviation_days]
)
```

```dax
Vendor Risk Score =
VAR AvgDev = COALESCE([Vendor Avg Deviation (Delayed Only)], 0)
VAR DelayPct = COALESCE([Vendor Delay Rate %], 0) * 100
RETURN
    AvgDev * 0.6 + DelayPct * 0.4
```

```dax
Vendor PO Count =
COUNTROWS(po_master)
```

```dax
MSME Combined Spend % =
DIVIDE(
    CALCULATE(
        SUM(po_master[PO Basic Value (INR)]),
        po_master[msme_category] IN { "Micro", "Small", "Medium" }
    ),
    SUM(po_master[PO Basic Value (INR)])
)
```

### 3.3 Page 3 — CPBG Compliance & Exposure

```dax
CPBG Value Compliance % =
DIVIDE(
    CALCULATE(COUNTROWS(cpbg_info), cpbg_info[cpbg_value_compliant] = TRUE()),
    COUNTROWS(cpbg_info)
)
```

```dax
CPBG Duration Compliance % =
DIVIDE(
    CALCULATE(COUNTROWS(cpbg_info), cpbg_info[cpbg_duration_compliant] = TRUE()),
    COUNTROWS(cpbg_info)
)
```

```dax
Intimation Compliance % =
DIVIDE(
    CALCULATE(COUNTROWS(cpbg_intimation_diff), cpbg_intimation_diff[intimation_compliant] = TRUE()),
    COUNTROWS(cpbg_intimation_diff)
)
```

```dax
Live BG Exposure =
CALCULATE(
    SUM(cpbg_info[Credit Amount]),
    cpbg_info[Start of Term] <= TODAY(),
    cpbg_info[Term End] >= TODAY()
)
```

```dax
Live BG Count =
CALCULATE(
    COUNTROWS(cpbg_info),
    cpbg_info[Start of Term] <= TODAY(),
    cpbg_info[Term End] >= TODAY()
)
```

```dax
Expiring in 90 Days Count =
CALCULATE(
    COUNTROWS(cpbg_info),
    cpbg_info[Term End] >= TODAY(),
    cpbg_info[Term End] <= TODAY() + 90
)
```

```dax
Expiring in 90 Days Value =
CALCULATE(
    SUM(cpbg_info[Credit Amount]),
    cpbg_info[Term End] >= TODAY(),
    cpbg_info[Term End] <= TODAY() + 90
)
```

> **Note on True/False columns:** if Power Query imports `cpbg_value_compliant`
> etc. as text ("True"/"False") instead of the Boolean type, change `= TRUE()`
> to `= "True"` in the measures above. Check the column's data type icon in
> the Fields pane (should show a Boolean toggle icon) before troubleshooting
> further if a measure returns blank.

---

## Part 4 — Page-by-Page Build

### Report-level navigation (do this first)

1. Create 3 pages, named `1_Lifecycle`, `2_VendorRisk`, `3_CPBG` (Page name
   in the Format pane — clean names help you reference them later).
2. On each page, add 3 rectangle shapes at the top as nav buttons (Insert →
   Shapes → Rectangle), labeled "Lifecycle", "Vendor Risk", "CPBG Compliance".
3. Style: fill Navy `#243450` for the inactive state, Forest Green `#3F6B4A`
   for whichever page you're currently on (set this manually per page) — keep
   Red reserved for risk/alert indicators only, not navigation state.
4. Select each shape → **Format → Action → Type: Page navigation** → pick
   the target page. This gives you branded navigation instead of Power BI's
   plain page tabs.
5. Copy these 3 shapes to all pages (Ctrl+C, paste on each page) so the nav
   bar is identical everywhere.

### Page 1: PO Lifecycle & Bottlenecks

**KPI Cards (top row, 4 cards):**
- Visual: **Card** (New Card visual, not the old KPI visual)
- Card 1: `Avg PR-to-PO Cycle Time` → format as `0"d"` (custom format)
- Card 2: `Avg Approval Lag` → format as `0"d"`
- Card 3: `Lead Time Deviation Rate %` → format as percentage, 1 decimal
- Card 4: a static text box: "No fixed SLA exists" (per C&P Procedure) — use
  a Text Box, not a card, since it's not a computed value

**Chart 1 — Monthly Cycle Time Trend (left, ~60% width):**
- Visual: **Line Chart**
- X-axis: `DateTable[FiscalMonthNum]` (or `po_master[PO DATE]` by month if
  you skipped the date table)
- Legend: `po_master[FY]`
- Y-axis (Values): `Avg PR-to-PO Cycle Time`
- Format → Line styles: 2.5pt width; Colors: manually assign 2023-24 = Warm Gray
  `#66705F`, 2024-25 = Gold `#E8C13C`, 2025-26 = Forest Green `#3F6B4A` (most
  recent year gets the brand-primary color, drawing the eye to it)

**Chart 2 — Lifecycle Funnel (right, ~40% width):**
- Visual: **Clustered Bar Chart** (horizontal)
- Axis: a manual 3-row table (PR→Approval / Approval→PO / PO→Delivery) — easiest
  way: create a small disconnected table via **Enter Data** with a `Stage`
  column, then use 3 separate measures as a **switch measure**:
```dax
Funnel Stage Value =
SWITCH(
    SELECTEDVALUE('Stage Table'[Stage]),
    "PR to Approval", [PR to Approval Days],
    "Approval to PO", [Approval to PO Days],
    "PO to Delivery", [PO to Delivery Days]
)
```
- Colors: Navy `#243450`, Gold `#E8C13C`, Forest Green `#3F6B4A`

**Chart 3 — Cycle Time by Order Type (full width, bottom):**
- Visual: **Clustered Column Chart**
- Axis: `po_master[Doc. Type]`
- Values: `Avg PR-to-PO Cycle Time`
- Add a filter: `Vendor PO Count >= 3` (via visual-level filter on count, to
  exclude noisy tiny groups)
- Data color: GAIL Red `#C0392B` (this is your standout finding — ZF/foreign
  orders taking ~377 days — so give it the brand-alert color)

**Footer text box:** "6 records with logically-impossible negative cycle
times excluded from these averages." — Insert → Text Box, small, muted gray.

### Page 2: Vendor Concentration & Risk

**Chart 1 — Top Vendors by Spend (left):**
- Visual: **Clustered Bar Chart** (horizontal, sorted descending)
- Axis: `po_master[VENDOR CODE]`
- Values: `Total PO Spend`
- Filter: **Top N** filter on `VENDOR CODE` by `Total PO Spend`, N = 12
- Color: Navy `#243450` (neutral — this chart is informational, not a risk signal)

**Chart 2 — HHI Trend (right):**
- Visual: **Line Chart** with markers
- Axis: `po_master[FY]`
- Values: `HHI Index`
- Add a **constant line** at y=2500 (Format → Analytics → Constant Line) labeled
  "High Concentration Threshold" — dashed gray
- Line color: GAIL Red `#C0392B`

**Table — Vendor Risk Scorecard (left, bottom):**
- Visual: **Table**
- Columns: `VENDOR CODE`, `Vendor PO Count`, `Vendor Delay Rate %`,
  `Vendor Avg Deviation (Delayed Only)`, `Total PO Spend`, `Vendor Risk Score`
- Filter: Top N by `Vendor Risk Score`, N = 10, and `Vendor PO Count >= 2`
- **Conditional formatting** on `Vendor Risk Score` column (Format → Conditional
  formatting → Background color, rules-based):
  - ≥ 70 → `#FBE7E3` background, `#C0392B` text (high risk)
  - 50–69 → `#FBF3DC` background, `#9C6B1F` text (medium)
  - < 50 → `#E7EFE8` background, `#3F6B4A` text (low)

**Chart 3 — MSME Category Spend Share (right, bottom):**
- Visual: **100% Stacked Column Chart**
- Axis: `po_master[FY]`
- Legend: `po_master[msme_category]`
- Values: `Total PO Spend`
- Colors: Micro = Forest Green `#3F6B4A`, Small = Gold `#E8C13C`,
  Medium = Navy `#243450`, Others = muted sage-gray `#C7CBB8`

**Optional tooltip page:** create a 4th hidden page sized as a tooltip
(Format → Page information → Tooltip = On, size 300×200), add a small line
chart of that vendor's cycle time over time, then set it as the **Tooltip**
for the Vendor Risk Scorecard table (Format → Tooltip → Report page).

### Page 3: CPBG Compliance & Exposure

**KPI Cards (top row, 3 cards, each with a clause citation):**
- Card 1: `CPBG Value Compliance %` — below it, a text box: "Clause 3.2.1A"
  in small gold `#E8C13C` pill-style text
- Card 2: `CPBG Duration Compliance %` — text box: "Clause 3.2.1 Note ii"
- Card 3: `Intimation Compliance %` — text box: "Clause 3.2.1 Note iii" — set
  this card's font color conditionally to GAIL Red `#C0392B` since it's the
  low-compliance headline finding

**Chart 1 — Compliance Rates by FY (left):**
- Visual: **Clustered Column Chart**
- Axis: `cpbg_info[FY]` (or a shared FY column if you've unified them)
- Values: `CPBG Value Compliance %`, `CPBG Duration Compliance %`,
  `Intimation Compliance %` (three value fields)
- Colors in order: Forest Green `#3F6B4A`, Gold `#E8C13C`, GAIL Red `#C0392B`
- Add a constant line at 100% for reference

**Panel — Live BG Exposure (right, top half):**
- Two large **Card** visuals side by side: `Live BG Count` and `Live BG Exposure`
  (format the exposure card as currency, `₹#,##0,,"L"` for lakhs)

**Table — Expiry Radar (right, bottom half):**
- Visual: **Table**
- Columns: `cpbg_info[Applicant]`, `cpbg_info[Term End]`, a calculated
  "Days to Expiry" column, `cpbg_info[Credit Amount]`
- Add this calculated column to `cpbg_info` for the days-remaining figure:
```dax
Days to Expiry = DATEDIFF(TODAY(), cpbg_info[Term End], DAY)
```
- Filter: `Days to Expiry >= 0 && Days to Expiry <= 90`
- Sort ascending by `Term End`
- Conditional formatting on `Days to Expiry`: ≤ 30 → red text `#C0392B` bold

---

## Part 5 — Final Polish Checklist

- [ ] Logo placed top-left with the disclaimer text nearby
- [ ] All 3 pages use identical nav bar styling
- [ ] Theme JSON applied (check View → Themes shows "GAIL Procurement Analytics")
- [ ] All KPI cards use consistent number formatting (1 decimal for %, "d" suffix for days)
- [ ] Gridlines/snap-to-grid used so visuals align across pages
- [ ] Tooltips added at minimum to the vendor risk table
- [ ] Footer disclaimer on every page: *"Anonymized data. Independent
      analytics project — not an official GAIL (India) Ltd. publication."*
- [ ] **Before sharing/publishing anywhere:** re-confirm the anonymization
      holds (no real vendor/employee names visible anywhere), and do **not**
      use Power BI's "Publish to Web" feature for this report — that makes it
      public with no access control, which isn't appropriate even for
      anonymized PSU procurement data. Share the `.pbix` file privately or
      take screenshots/screen-recordings for your portfolio instead.

---

## What to Say About This Project in an Interview

*"I built a 3-page Power BI dashboard analyzing GAIL's PO and bank guarantee
data across 3 fiscal years. Beyond the standard cycle-time and vendor
analysis, I read GAIL's own 250-page procurement manual and built three
compliance KPIs directly against cited clauses — CPBG value percentage,
guarantee duration, and a 30-day intimation deadline — rather than assuming
what 'good' looks like. That surfaced a real finding: intimation compliance
was only 12-21% every year, while value and duration compliance were much
healthier at 73-86%. I also caught and explicitly flagged several data
quality issues — identical approval-stage dates, impossible negative cycle
times — rather than letting them silently skew the averages."*
