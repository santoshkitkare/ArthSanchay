# Product Requirements Document
## Retirement Planner — Web Application

| | |
|---|---|
| **Document version** | 1.0 (draft for review) |
| **Date** | 2026-09-08 |
| **Source of truth** | `Retirement_Planner_Calculator_05102025.xlsx` (sheets `Inputs`, `Projection`) |
| **Target stack** | Python 3.11+ · FastAPI · SQLAlchemy · SQLite · React (SPA) · Chart.js |
| **Status** | Requirements only — no implementation authorised by this document |

---

### Contents

1. [Overview & Problem Statement](#1-overview--problem-statement)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [Personas and User Journeys](#3-personas-and-user-journeys)
4. [Functional Requirements](#4-functional-requirements)
5. [Calculation Specification](#5-calculation-specification)
6. [Data Model](#6-data-model)
7. [API Specification](#7-api-specification)
8. [Frontend Specification](#8-frontend-specification)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Architecture and Deployment](#10-architecture-and-deployment)
11. [Testing Strategy](#11-testing-strategy)
12. [Phased Roadmap](#12-phased-roadmap)
13. [Assumptions and Open Questions](#13-assumptions-and-open-questions)
14. [Appendix](#14-appendix)

---

## 1. Overview & Problem Statement

### 1.1 What exists today

A single Excel workbook models one household's retirement trajectory. It has two sheets:

- **`Inputs`** — 21 hand-entered assumptions in cells `B3:B23`: the planner's age, retirement age
  and life expectancy; the current corpus; today's annual household expense; three inflation rates;
  pre- and post-retirement return rates; and the ages, school fees, graduation costs and marriage
  costs for exactly two children, labelled "Son" and "Daughter".
- **`Projection`** — a 39-row × 18-column annual grid running from calendar year 2026 (age 43) to
  2064 (age 81). Each row inflates every expense forward, sums them into a total withdrawal,
  subtracts that from the corpus, applies one year of investment return to the remainder, and
  carries the result into the next row.

The workbook answers one question: *given this corpus and these costs, when does the money run out?*
For the sample data the answer is **age 65** — the corpus peaks at roughly ₹1.77 crore at age 55,
survives the son's marriage at age 58, is halved by the daughter's marriage at age 64, and turns
negative at age 65, fifteen years short of the age-80 life expectancy.

### 1.2 Why it needs to become an application

The workbook is a good model trapped in a bad container. Six problems make it unfit for repeated,
confident use:

1. **It cannot be shared or accessed remotely.** It lives on one machine, in one file, with no
   history and no way for a second person to view or reuse it.
2. **It only simulates; it never solves.** The stated purpose is to determine *the retirement corpus
   needed*, but the sheet only tells you whether a corpus you already typed in happens to survive.
   Finding the required corpus means manually retyping values until the last row stops going
   negative.
3. **It has no income side at all.** There is no salary, no monthly SIP, no annual step-up, no
   post-retirement pension or rental income anywhere in the model. The corpus can only shrink. For
   anyone still working — the majority of people who need this tool — the model is unusable as-is.
4. **It is annual.** Cash flow is a monthly reality: salaries, SIPs, school-fee instalments and
   living expenses all land monthly. An annual grid cannot show a mid-year shortfall, and it
   overstates the cost of goals by withdrawing a full year of expenses on day one.
5. **It is hardcoded to two children.** "Son" and "Daughter" are column headers, not data. A user
   with one child, three children, elderly parents to support, or a house down-payment to fund
   cannot express that without rewriting formulas.
6. **It produces a spreadsheet, not a picture.** There is no chart. The single most valuable output
   of a retirement model — seeing the corpus curve rise, peak, and fall against the expense curve —
   is absent.

### 1.3 What we are building

A hosted web application that:

- captures every assumption through a guided, validated multi-section form;
- runs a **month-by-month** projection from today to life expectancy;
- charts corpus, income, expenses and goal events on one timeline so the user can *see* the plan;
- **solves backwards** for the corpus required at retirement and the monthly investment needed to
  reach it;
- lets each user keep several named scenarios side by side and export them.

---

## 2. Goals and Non-Goals

### 2.1 Goals

| # | Goal | Success measure |
|---|---|---|
| G1 | Reproduce the workbook's arithmetic exactly, so existing numbers are trusted | A golden-file test reproduces all 39×18 cached cell values within ₹1 |
| G2 | Upgrade the model to monthly granularity without losing that trust | Monthly mode's year-end corpus is explainable against annual mode; both are selectable |
| G3 | Answer "how much do I need?" and "how much must I invest?" | Two solvers converge in under a second for any valid input set |
| G4 | Make the plan visual | Corpus/income/expense chart with goal and depletion markers on the results page |
| G5 | Support real households, not one household | N dependents, N custom goals, N income streams |
| G6 | Deploy anywhere | One `Dockerfile`, config from environment variables, no host-specific code |

### 2.2 Non-Goals (explicitly out of scope for v1)

- **This is not investment advice.** The application performs arithmetic on user-supplied
  assumptions. Every results page carries a disclaimer to that effect.
- **No live market data.** Returns are user-entered assumptions, not fetched from any index or fund.
- **No bank, broker, mutual-fund or account-aggregator integration.** All data is typed in.
- **No tax computation.** Capital-gains and income-tax modelling is deferred to a later phase; v1
  treats all returns as net-of-tax and says so in the field help text.
- **Single currency (INR) in v1.** The number formatter uses the Indian digit-grouping
  (lakh/crore) convention. Multi-currency is a P3 item.
- **No native mobile apps.** The React SPA must be responsive, but there is no App Store or Play
  Store build.
- **No collaborative editing.** One scenario has exactly one owner.

---

## 3. Personas and User Journeys

### 3.1 Personas

**P1 — the self-directed planner (primary).** Mid-forties, salaried, two children, maintains the
workbook personally. Comfortable with numbers, impatient with formulas. They want to change the
retirement age from 43 to 50 and immediately see what that does to the curve. This is the persona
the workbook was built for and the one the app must not disappoint.

**P2 — the first-timer (secondary).** Early thirties, has never built a projection, does not know
what a reasonable inflation rate is or what "corpus" means. They need sensible defaults, help text
on every field, and a clear headline answer rather than a 400-row table.

**P3 — the fee-only adviser (tertiary, informs the multi-user requirement).** Runs the tool for a
handful of clients, keeps a separate named scenario per client, and needs to export a clean PDF to
hand over.

### 3.2 Primary journey — building a first plan

1. Land on the public route, then **sign up** with email and password.
2. Prompted to **create the first scenario**; give it a name ("Base case").
3. **Input wizard**, five sections, each independently valid and savable:
   *You and your timeline* → *Money you have and add* → *Living expenses* → *Dependents* →
   *Goals and other income*.
4. On completion the app runs the projection and lands on the **results dashboard**: a headline
   verdict ("Your corpus lasts to age 65 — 15 years short"), the corpus chart, key metric tiles,
   and the projection table below.
5. The user drags the retirement-age slider; the chart **recalculates and redraws** without leaving
   the page.
6. They click **"What do I need?"**; the solver reports the corpus required at retirement and the
   monthly SIP that closes the gap.
7. **"Save as new scenario"** → "Retire at 50". They open **Compare** and view both corpus curves on
   one chart.
8. **Export** the preferred scenario to Excel for their records and to PDF to share.

### 3.3 Secondary journeys

- **Return visit:** log in → scenario list with last-modified dates → open → results are recomputed
  fresh, never served stale.
- **Duplicate and tweak:** clone a scenario, change two fields, compare.
- **Recover access:** password reset by emailed single-use token.

---

## 4. Functional Requirements

Requirements are numbered `FR-<area>-<n>` and carry a phase tag (`P0`–`P3`, see §12).

### 4.1 Accounts and authentication

| ID | Requirement | Phase |
|---|---|---|
| FR-AUTH-1 | A visitor can register with email and password. Email must be unique and syntactically valid; password minimum 10 characters. | P1 |
| FR-AUTH-2 | Passwords are stored only as Argon2id hashes (bcrypt is an acceptable fallback). Plaintext or reversible storage is prohibited. | P1 |
| FR-AUTH-3 | Login issues a signed JWT access token (30 minutes) and a refresh token (14 days, rotating, stored hashed server-side and revocable). | P1 |
| FR-AUTH-4 | Tokens are delivered in `HttpOnly`, `Secure`, `SameSite=Lax` cookies. The SPA never reads tokens from JavaScript. | P1 |
| FR-AUTH-5 | Every scenario endpoint authorises on `scenario.user_id == current_user.id` and returns `404` rather than `403` for another user's scenario, so IDs cannot be enumerated. | P1 |
| FR-AUTH-6 | Password reset by single-use, 30-minute, emailed token. | P2 |
| FR-AUTH-7 | Rate limit: five failed logins per email per fifteen minutes, then exponential lockout. | P1 |
| FR-AUTH-8 | A user can delete their account, which hard-deletes all their scenarios and dependent rows. | P2 |

### 4.2 Scenario management

| ID | Requirement | Phase |
|---|---|---|
| FR-SCN-1 | A user can create, rename, list, open, duplicate and delete named scenarios. No cap below 50 per user. | P1 |
| FR-SCN-2 | A scenario holds one complete input set: the scalar assumptions plus its dependents, goals and income streams. | P1 |
| FR-SCN-3 | The scenario list shows name, created date, last-modified date and a one-line verdict ("Lasts beyond 80" / "Short by 15 years"). | P2 |
| FR-SCN-4 | Duplicating a scenario deep-copies all child rows and appends " (copy)" to the name. | P2 |
| FR-SCN-5 | Every new scenario is pre-filled with the documented defaults (§4.3) so a new user sees a working projection immediately, before typing anything. | P1 |
| FR-SCN-6 | Deleting a scenario requires explicit confirmation and is irreversible. | P1 |

### 4.3 Input model

The form is organised into five sections. **Every workbook input is preserved.** New fields are
marked **NEW**.

#### Section A — You and your timeline

| Field | Type | Unit | Default | Validation | Help text |
|---|---|---|---|---|---|
| Current age | int | years | 43 | 18–75 | Your age today. |
| Retirement age | int | years | 43 | ≥ current age, < life expectancy | The age at which you stop earning a salary. |
| Life expectancy | int | years | 80 | > retirement age, ≤ 110 | Plan to a conservative age — outliving the plan is the risk that matters. |
| Plan start date **NEW** | date | — | 1st of next month | within ±1 year of today | Replaces "Base Year"; the projection's month zero. |
| Base year *(workbook field)* | int | year | 2026 | 1900–2200 | Derived from the plan start date; retained in exports for parity with the original sheet. |

#### Section B — Money you have and money you add

| Field | Type | Unit | Default | Validation | Help text |
|---|---|---|---|---|---|
| Current corpus | money | ₹ | 15,000,000 | ≥ 0 | Everything invested today: equity, debt, EPF, PPF, NPS, deposits. Exclude the home you live in. |
| Monthly contribution (SIP) **NEW** | money | ₹/month | 0 | ≥ 0 | What you invest every month out of income. The workbook had no field for this at all. |
| Annual step-up on contribution **NEW** | percent | %/yr | 0% | 0–25% | Raise your SIP by this much each year, typically in line with salary growth. |
| Contributions stop at age **NEW** | int | years | = retirement age | ≤ retirement age | Contributions normally cease when the salary does. |
| Pre-retirement return | percent | %/yr | 10% | −20% to 40% | Expected annual return while still working. Enter a figure net of tax and fees. |
| Post-retirement return | percent | %/yr | 10% | −20% to 40% | Expected return after retiring — usually lower, as the portfolio de-risks. |

#### Section C — Living expenses

| Field | Type | Unit | Default | Validation | Help text |
|---|---|---|---|---|---|
| Annual household expense today | money | ₹/yr | 600,000 | ≥ 0 | Everything you spend in a year at today's prices, excluding the child costs entered separately. |
| Household expense inflation | percent | %/yr | 7% | 0–20% | The rate at which your cost of living rises. |
| Charge household expense before retirement? **NEW** | bool | — | off | — | Off by default, matching the workbook: while you are working, salary covers living costs and only the corpus's growth is modelled. |
| Medical / health expense today **NEW** | money | ₹/yr | 0 | ≥ 0 | Premiums and out-of-pocket medical costs, tracked separately because they inflate faster. |
| Medical inflation **NEW** | percent | %/yr | 10% | 0–25% | Medical inflation in India runs well above general inflation; separating it out is the most commonly missed line in home-made plans. |
| Post-retirement expense factor **NEW** | percent | % | 100% | 30–150% | Many households spend less after retiring — no commute, no dependents. 100% keeps workbook parity. |

#### Section D — Dependents (replaces the hardcoded Son / Daughter columns)

A repeating list, zero or more entries. The sample workbook maps to exactly two.

| Field | Type | Unit | Default | Validation | Help text |
|---|---|---|---|---|---|
| Name / label | text | — | "Child 1" | 1–40 chars | For your reference only. |
| Current age | int | years | — | 0–40 | |
| Annual school fee today | money | ₹/yr | — | ≥ 0 | Today's annual fee. |
| School fee hike | percent | % per step | 25% | 0–50% | Applied as a step; see the next field. |
| School fee hike frequency | int | years | 2 | 1–10 | A 25% hike every 2 years is about 11.8% a year compounded. The form shows this equivalent rate live — check it against your actual fee history. |
| Schooling ends at age **NEW** | int | years | 18 | 10–30 | Was hardcoded to 18 inside the workbook's formulas. |
| Graduation total cost today | money | ₹ | 1,200,000 | ≥ 0 | Full cost of the degree at today's prices. |
| Graduation inflation | percent | %/yr | 7% | 0–20% | |
| Graduation start age **NEW** | int | years | 18 | 15–30 | Was hardcoded. |
| Graduation duration **NEW** | int | years | 4 | 1–8 | Was hardcoded to 4. |
| Inflate graduation instalments **NEW** | bool | — | on | — | The workbook froze all four instalments at the age-18 price. On (the default) inflates each year's instalment; off reproduces the workbook exactly. |
| Marriage cost today **NEW: now per dependent** | money | ₹ | 500,000 | ≥ 0 | The workbook shared a single figure across both children; each dependent now has their own. |
| Marriage inflation | percent | %/yr | 7% | 0–20% | |
| Marriage age | int | years | 28 | 18–45, or blank | Leave blank to exclude this goal. |
| Fund school fees from corpus before retirement **NEW** | bool | — | on | — | Surfaces an inconsistency in the workbook, which charged school fees to the corpus while working but not household expenses. |

#### Section E — Custom goals and other income **NEW**

**Custom goals** (repeating): label; amount at today's prices; the planner's age at which it
occurs; inflation rate; one-off or recurring; if recurring, duration in years and frequency.
This covers car replacement, a house down-payment, travel, parental support, and everything else
the fixed school/graduation/marriage triple cannot express.

**Income streams** (repeating): label; monthly amount at today's prices; start age; end age (blank
means life expectancy); annual escalation rate. This covers pension, annuity, rental income,
part-time consulting and a spouse's income.

### 4.4 Projection engine

| ID | Requirement | Phase |
|---|---|---|
| FR-ENG-1 | The engine produces one row per month, from the plan start to the end of the month in which the planner reaches life expectancy. | P0 |
| FR-ENG-2 | Two modes are supported and selectable per request. **`annual_parity`** reproduces the workbook's annual, begin-of-year-withdrawal arithmetic exactly. **`monthly`**, the default, runs month by month. Both are specified in §5. | P0 |
| FR-ENG-3 | Annual rates convert geometrically: `r_m = (1 + r_a)^(1/12) − 1`, so twelve months compound to exactly the annual rate. Simple division by twelve is prohibited — it would turn a 10% assumption into 10.47% effective. | P0 |
| FR-ENG-4 | Expense amounts hold flat within a plan year and step on the plan anniversary. Inflation is not applied month over month. | P0 |
| FR-ENG-5 | **The corpus is floored at zero.** Once exhausted it must not go negative and must not accrue return. This fixes the workbook's most serious defect. | P0 |
| FR-ENG-6 | On exhaustion the engine records the exhaustion month and age, and reports the **unfunded shortfall** for every subsequent month. The projection still runs to life expectancy so the user sees the full size of the gap. | P0 |
| FR-ENG-7 | The projection ends at life expectancy and never beyond. | P0 |
| FR-ENG-8 | The rate applied in a month is the pre-retirement rate while age is below the retirement age, and the post-retirement rate from the retirement age onward. | P0 |
| FR-ENG-9 | All money is computed in `decimal.Decimal` at 28-digit precision and quantised to two decimal places only at serialisation. Binary floats are prohibited for currency. | P0 |
| FR-ENG-10 | Every row carries a per-category breakdown so the interface can explain why a given month was expensive. | P0 |
| FR-ENG-11 | Each row also reports the corpus in **today's rupees**, deflated by household inflation, to drive the real-terms toggle. | P2 |
| FR-ENG-12 | The engine is a pure function of the input set: no database access, no I/O, no clock reads. This is what makes it testable and directly reusable by the solvers. | P0 |

### 4.5 Solvers

| ID | Requirement | Phase |
|---|---|---|
| FR-SOL-1 | **Required corpus at retirement.** Compute the smallest corpus held on the retirement date that keeps the balance at or above zero through life expectancy. | P1 |
| FR-SOL-2 | **Required monthly contribution.** Given the current corpus and a target retirement age, compute the smallest monthly SIP — respecting the step-up — that reaches the required corpus. | P1 |
| FR-SOL-3 | **Longevity.** Report the age at which the corpus is exhausted, or "lasts beyond life expectancy" together with the terminal surplus. | P1 |
| FR-SOL-4 | Solvers use bisection on the monotone input, bounded to 80 iterations, tolerance ₹100 or 1e-6 relative. Non-convergence returns a structured error, never a silent wrong number. | P1 |
| FR-SOL-5 | Infeasible cases are reported honestly: if no contribution within a sane upper bound closes the gap, the response says so and names the levers — retire later, spend less, accept a lower terminal balance. | P1 |
| FR-SOL-6 | **Sensitivity grid.** Terminal corpus and exhaustion age across a 5×5 grid of return × inflation deltas, ±2 percentage points in one-point steps. | P3 |

### 4.6 Results and visualisation

| ID | Requirement | Phase |
|---|---|---|
| FR-VIZ-1 | **Headline verdict** in plain language above the fold: whether the plan survives, and by how much it succeeds or falls short, in both years and rupees. | P0 |
| FR-VIZ-2 | **Corpus timeline chart** — corpus balance as a filled area against age, with a vertical marker at the retirement age and, where applicable, at the exhaustion age. | P0 |
| FR-VIZ-3 | **Income vs. expenses chart** — contributions and income streams above the axis, expense categories stacked below, so the crossover from accumulation to drawdown is visible at a glance. | P0 |
| FR-VIZ-4 | **Goal markers** — school, graduation, marriage and custom goal events annotated on the timeline, with label and amount on hover. | P1 |
| FR-VIZ-5 | Charts toggle between **monthly and annual** aggregation, and between **nominal and today's rupees**. | P2 |
| FR-VIZ-6 | **Key metric tiles** — corpus at retirement; peak corpus and the age it occurs; exhaustion age or terminal corpus; total lifetime withdrawals; total return earned; and the first-year withdrawal rate at retirement. | P1 |
| FR-VIZ-7 | **Projection table** — the full grid, containing all 18 workbook columns plus the new ones, virtualised for smooth scrolling and collapsible from monthly to annual. | P0 |
| FR-VIZ-8 | Every currency figure uses Indian digit grouping (₹1,50,00,000), with a lakh/crore short form on the metric tiles. | P0 |
| FR-VIZ-9 | A persistent footer disclaimer: an illustrative projection based on the user's own assumptions, not investment advice. | P0 |
| FR-VIZ-10 | Charts and tables must remain readable on a 375 px-wide viewport. | P1 |

### 4.7 Comparison and export

| ID | Requirement | Phase |
|---|---|---|
| FR-CMP-1 | Select two to four scenarios and overlay their corpus curves on one chart, with a side-by-side metrics table and a highlighted diff of the inputs that differ. | P2 |
| FR-CMP-2 | **Excel export** — an `.xlsx` with an `Inputs` sheet and a `Projection` sheet mirroring the original workbook's layout, so the export is a drop-in replacement for the file it came from. | P2 |
| FR-CMP-3 | **CSV export** of the projection grid. | P2 |
| FR-CMP-4 | **PDF summary** — one to two pages covering inputs, verdict, key metrics and both charts, suitable for handing to a spouse or a client. | P2 |
| FR-CMP-5 | **JSON import/export** of a scenario's input set, so plans are portable and diffable. | P2 |

### 4.8 Defects in the source workbook and their required resolutions

This section is the audit trail from spreadsheet to specification. Each item was found by reading
the workbook's formulas and cached values directly.

| # | Observation in the workbook | Severity | Resolution |
|---|---|---|---|
| D1 | `Corpus_End = (Corpus_Start − Withdrawals) × 1.10` continues to apply a **positive 10% return to a negative balance**. From age 65 the corpus falls from −₹4.5 lakh to **−₹17.34 crore** by age 81 — a fictitious figure that overstates the true shortfall by roughly two orders of magnitude. | **Critical** | FR-ENG-5, FR-ENG-6 |
| D2 | The grid runs to age 81 against a life expectancy of 80 — one row too many. The row count is hardcoded rather than driven by the life-expectancy input. | Low | FR-ENG-7 |
| D3 | **No income, salary, SIP or contribution exists anywhere in the model.** The corpus can only be drawn down. | **Critical** | Input model, Section B; FR-SOL-2 |
| D4 | The sheet never computes a required corpus, despite that being its stated purpose. | High | FR-SOL-1 |
| D5 | Both children's marriages draw on the same `Marriage Cost Today` cell (`Inputs!B18`); there is no separate figure per child. | Medium | Per-dependent marriage cost, Section D |
| D6 | Graduation cost is inflated to the year the child turns 18 and then split into **four equal, un-inflated instalments**. At 7% inflation the age-21 instalment is understated by about 22%. | Medium | `Inflate graduation instalments` flag, on by default |
| D7 | The school cutoff (age 18), the graduation window (ages 18–21) and the graduation duration (4 years) are hardcoded inside formulas rather than exposed as inputs. | Medium | New fields in Section D |
| D8 | **Inconsistent pre-retirement treatment.** Household expense is suppressed before retirement — `IF(Age < RetirementAge, 0, …)` — on the assumption that salary covers it, yet school fees, graduation and marriage *are* charged to the corpus in those same years. Either the salary covers household costs and the children's fees, or it covers neither. | Medium | Explicit toggles: `Charge household expense before retirement` and per-dependent `Fund school fees from corpus before retirement` |
| D9 | The 25%-per-two-years school fee step compounds to about **11.8% a year**, far above the 7% used everywhere else in the sheet. Across the four-year-old's remaining fourteen school years it roughly triples the fee in real terms. This is a legitimate assumption, but it is invisible in the sheet. | Low | Retained as the default, with the implied annual rate computed and displayed live in the form |
| D10 | Cell `Inputs!D7` (`=B7/12`) computes a monthly expense that nothing consumes — a leftover helper. | Trivial | Not carried forward; monthly figures are first-class in the new engine |
| D11 | The whole year's expenses are withdrawn on day one of the year and the remainder then compounds for twelve months. Relative to spending monthly, this understates the corpus. | Medium (by design) | Preserved exactly in `annual_parity` mode; `monthly` mode is the realistic default (§5.6) |
| D12 | `Corpus Start` is guarded by `IF(ROW()=2, …)`, so inserting a row above the table silently corrupts the model. | Low (structural) | Not applicable — the engine is code, not cell references |

---

## 5. Calculation Specification

This is the authoritative section. Where §4 says *what*, this says *exactly how*. It has been
validated against the source workbook: a reference implementation of §5.2 reproduces all 38 rows
of the `Projection` sheet to within **₹0.04**, the residual being Excel's binary-float rounding
against the specified decimal arithmetic.

### 5.1 Notation

| Symbol | Meaning |
|---|---|
| `A0` | current age (years) |
| `AR` | retirement age |
| `AL` | life expectancy |
| `y` | plan year index, `0` for the first year; age in year `y` is `A0 + y` |
| `m` | month index within a plan year, `0`–`11` |
| `t` | absolute month index, `t = 12y + m` |
| `C0` | current corpus |
| `E0` | annual household expense today |
| `i_h` | household expense inflation (annual) |
| `r_pre`, `r_post` | pre- and post-retirement annual return |
| `c_j.age0` | dependent `j`'s age today |

The plan spans plan years `y = 0 … AL − A0` inclusive, i.e. ages `A0` through `AL`. **The workbook's
39th row (age 81) is not reproduced** — see D2.

### 5.2 Annual cost formulas (identical in both engine modes)

These are the workbook's formulas, restated. All are evaluated once per plan year `y`.

**Household expense**

```
HH(y) = 0                              if (A0 + y) < AR and charge_pre_retirement is off
      = E0 × (1 + i_h)^y × f_post      otherwise
```

where `f_post` is the post-retirement expense factor (100% by default, applied only from `AR`).
Medical expense, when entered, is an independent line inflated at its own rate `i_med`.

**School fee, per dependent `j`** — with `ca = c_j.age0 + y` the dependent's age in year `y`:

```
SCH_j(y) = fee_j × (1 + hike_j)^⌊y / freq_j⌋    if ca < school_end_age_j
         = 0                                     otherwise
```

The step exponent `⌊y / freq_j⌋` counts elapsed *plan* years, so the fee escalates with time rather
than with the dependent's grade — the workbook's behaviour, retained. Note that `25%` every `2`
years is an effective **11.83% per year** (`1.25^(1/2) − 1`); the form displays this equivalent.

**Graduation, per dependent `j`** — with `g0 = graduation_start_age_j`, `n = graduation_duration_j`:

```
GRAD_j(y) = 0                                          if not (g0 ≤ ca ≤ g0 + n − 1)
          = GRAD_j × (1 + i_g)^(g0 − c_j.age0) / n      if inflate_instalments is off  [workbook]
          = GRAD_j × (1 + i_g)^(ca − c_j.age0) / n      if inflate_instalments is on   [default]
```

The workbook inflates the total to the year the dependent turns `g0` and then splits it into `n`
equal, frozen instalments. The default corrects this so each instalment is priced in its own year.

**Marriage, per dependent `j`** — fires in the single year where `ca == marriage_age_j`:

```
MAR_j(y) = MAR_COST_j × (1 + i_m)^(marriage_age_j − c_j.age0)
```

`MAR_COST_j` is now per dependent (D5).

**Custom goals** — a one-off goal at planner age `ag` with today's cost `G` and inflation `i_g`:

```
GOAL(y) = G × (1 + i_g)^y     where y = ag − A0
```

Recurring goals repeat this at their stated frequency for their stated duration.

**Total withdrawals**

```
W(y) = HH(y) + MED(y) + Σ_j [SCH_j(y) + GRAD_j(y) + MAR_j(y)] + Σ GOAL(y)
```

**Income and contributions** (new; absent from the workbook)

```
SIP(y)    = sip_monthly × (1 + stepup)^y      if (A0 + y) < contributions_stop_age, else 0
INC_k(y)  = inc_k.monthly × (1 + esc_k)^y      if inc_k.start_age ≤ A0 + y ≤ inc_k.end_age, else 0
```

Both are monthly amounts, held flat within the plan year and stepped on the anniversary (FR-ENG-4).

### 5.3 Rate conversion

```
r_m = (1 + r_a)^(1/12) − 1
```

applied with `r_a = r_pre` while `A0 + y < AR` and `r_a = r_post` from `AR` onward. Twelve
applications of `r_m` compound to exactly `r_a`. Simple division (`r_a / 12`) is prohibited by
FR-ENG-3: it would silently turn a 10% assumption into a 10.47% effective rate and break
reconciliation with the workbook.

### 5.4 `annual_parity` mode — exact workbook reproduction

One step per plan year. Withdrawals are taken at the **start** of the year; the remainder earns a
full year of return.

```
after(y)  = max(0, C(y) − W(y))          # FR-ENG-5: floored, unlike the workbook
short(y)  = max(0, W(y) − C(y))          # FR-ENG-6: the unfunded amount
C(y + 1)  = after(y) × (1 + r_a(y))
```

With the floor removed this is precisely the workbook's
`R = (C − P) + (C − P) × rate`. The floor is the **only** intentional divergence, and it applies
only once the corpus is already exhausted.

### 5.5 `monthly` mode — the default

One step per month. Recurring costs are spread evenly across the twelve months of their plan year;
lump-sum goals (marriage, graduation instalments, custom one-offs) land in the **first month** of
their plan year, which is the conservative choice.

```
recurring(y) = [HH(y) + MED(y) + Σ_j SCH_j(y)] / 12
lump(y, m)   = Σ_j MAR_j(y) + Σ_j GRAD_j(y) + Σ GOAL(y)      if m = 0, else 0
inflow(y)    = SIP(y) + Σ_k INC_k(y)

net(t)       = recurring(y) + lump(y, m) − inflow(y)
after(t)     = max(0, C(t) − net(t))
short(t)     = max(0, net(t) − C(t))
C(t + 1)     = after(t) × (1 + r_m)
```

Cash flows are applied at the **start** of the month, mirroring the workbook's begin-of-period
convention so that the two modes differ only in period length, not in timing convention.

### 5.6 Reconciliation: what monthly granularity changes, and by how much

Spreading a year's spending across twelve months leaves money invested for longer, so the monthly
engine is always at least as favourable as the annual one. For the workbook's own sample inputs
the divergence is material and grows over time:

| Age | `annual_parity` corpus end | `monthly` corpus end | Difference |
|---:|---:|---:|---:|
| 43 | ₹1,55,10,000 | ₹1,55,51,960 | +0.27% |
| 50 | ₹1,74,21,561 | ₹1,80,45,968 | +3.58% |
| 55 | ₹1,75,73,403 | ₹1,90,23,374 | +8.25% |
| 60 | ₹1,08,77,305 | ₹1,38,73,202 | +27.5% |
| 64 | ₹22,48,696 | ₹71,18,140 | +217% |
| **Exhaustion age** | **65** | **67** | **+2 years** |

Two consequences the interface must communicate:

- Switching from annual to monthly buys the sample household **two extra years** of solvency. This
  is a modelling artefact, not free money, and the mode selector carries an explanatory tooltip.
- The workbook's terminal figure of **−₹17.34 crore** is fictitious. With the corpus correctly
  floored, the honest statement of the gap is the cumulative unfunded shortfall:
  **₹7.19 crore** in `annual_parity` mode and **₹6.60 crore** in `monthly` mode, both in nominal
  (future) rupees — or **₹78.8 lakh** in today's rupees, which is the figure a user can actually
  reason about and so is the one shown first.

### 5.7 Derived metrics

| Metric | Definition |
|---|---|
| Corpus at retirement | `C` at the first month where age = `AR` |
| Peak corpus | `max C(t)` and the age at which it occurs |
| Exhaustion age | age at the first `t` where `C(t + 1) = 0` and `short(t) > 0`; null if never |
| Terminal corpus | `C` at the final month |
| Unfunded shortfall | `Σ short(t)`, nominal; also reported in today's rupees |
| First-year withdrawal rate | `W(y_ret) / C(y_ret)` — flagged in the UI if above 4% |
| Real (today's rupees) value | `C(t) / (1 + i_h)^y` |

### 5.8 Required-corpus solver (FR-SOL-1)

The terminal corpus is monotonically non-decreasing in the corpus held at retirement, so bisection
is valid and cannot converge on a false root.

1. Run the projection from today to `AR` to establish the accumulation phase unchanged.
2. Bisect on the retirement-date corpus `X` over `[0, 100 × total lifetime withdrawals]`.
3. The objective is the minimum `X` for which `short(t) = 0` for every `t` and the terminal corpus
   is ≥ the user's desired legacy amount (default ₹0).
4. Stop at a tolerance of ₹100 or 1e-6 relative, capped at 80 iterations.
5. Report `X`, the gap against the corpus the current plan actually delivers at `AR`, and the
   corresponding figures in today's rupees.

### 5.9 Required-contribution solver (FR-SOL-2)

Identical bisection, on `sip_monthly` over `[0, 10 × current monthly expense]`, holding the step-up
fixed. If the upper bound still fails, return the structured infeasibility response required by
FR-SOL-5 rather than an arbitrary large number.

---

## 6. Data Model

SQLite via SQLAlchemy, migrated with Alembic. Money is stored as `NUMERIC` and handled as
`Decimal` in Python; rates are stored as decimal fractions (`0.07`, not `7`).

**Projections are never stored.** They are a pure function of the input set (FR-ENG-12) and are
recomputed on every request, then cached in-process for 60 seconds keyed by a hash of the input
set. This removes any possibility of a stale projection outliving an edited input.

```
users
  id                INTEGER PK
  email             TEXT UNIQUE NOT NULL
  password_hash     TEXT NOT NULL
  created_at        TIMESTAMP NOT NULL
  last_login_at     TIMESTAMP

refresh_tokens
  id                INTEGER PK
  user_id           INTEGER FK -> users.id ON DELETE CASCADE
  token_hash        TEXT NOT NULL
  expires_at        TIMESTAMP NOT NULL
  revoked_at        TIMESTAMP

scenarios
  id                INTEGER PK
  user_id           INTEGER FK -> users.id ON DELETE CASCADE
  name              TEXT NOT NULL
  created_at        TIMESTAMP NOT NULL
  updated_at        TIMESTAMP NOT NULL
  UNIQUE (user_id, name)

scenario_inputs                       -- 1:1 with scenarios; all Section A/B/C scalars
  scenario_id       INTEGER PK FK -> scenarios.id ON DELETE CASCADE
  current_age, retirement_age, life_expectancy        INTEGER
  plan_start_date                                     DATE
  current_corpus, annual_expense_today                NUMERIC
  monthly_contribution, contribution_stepup           NUMERIC
  contributions_stop_age                              INTEGER
  expense_inflation, pre_retirement_return,
    post_retirement_return                            NUMERIC
  medical_expense_today, medical_inflation            NUMERIC
  charge_household_expense_pre_retirement             BOOLEAN
  post_retirement_expense_factor                      NUMERIC
  engine_mode                                         TEXT  -- 'monthly' | 'annual_parity'

dependents
  id                INTEGER PK
  scenario_id       INTEGER FK -> scenarios.id ON DELETE CASCADE
  sort_order        INTEGER
  label             TEXT
  current_age                                         INTEGER
  school_fee_today, school_fee_hike                   NUMERIC
  school_fee_hike_frequency, school_end_age           INTEGER
  graduation_cost_today, graduation_inflation         NUMERIC
  graduation_start_age, graduation_duration           INTEGER
  inflate_graduation_instalments                      BOOLEAN
  marriage_cost_today, marriage_inflation             NUMERIC
  marriage_age                                        INTEGER NULL
  fund_school_from_corpus_pre_retirement              BOOLEAN

goals
  id                INTEGER PK
  scenario_id       INTEGER FK -> scenarios.id ON DELETE CASCADE
  label             TEXT
  amount_today      NUMERIC
  at_age            INTEGER
  inflation         NUMERIC
  recurrence        TEXT     -- 'once' | 'annual' | 'every_n_years'
  recurrence_years  INTEGER NULL
  duration_years    INTEGER NULL

income_streams
  id                INTEGER PK
  scenario_id       INTEGER FK -> scenarios.id ON DELETE CASCADE
  label             TEXT
  monthly_amount_today  NUMERIC
  start_age         INTEGER
  end_age           INTEGER NULL          -- NULL means life expectancy
  annual_escalation NUMERIC
```

Indexes: `scenarios(user_id, updated_at DESC)`; foreign keys on all child tables; `PRAGMA
foreign_keys = ON` must be enabled per connection, as SQLite does not enforce them by default.

---

## 7. API Specification

All endpoints are under `/api`, accept and return JSON, and are authenticated by cookie except
where noted. Validation is by Pydantic v2 models; failures return `422` with per-field messages
the SPA maps back onto form fields.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Create account; returns the user and sets auth cookies |
| `POST` | `/api/auth/login` | — | Authenticate; sets auth cookies |
| `POST` | `/api/auth/refresh` | refresh cookie | Rotate the access token |
| `POST` | `/api/auth/logout` | ✓ | Revoke the refresh token, clear cookies |
| `GET` | `/api/auth/me` | ✓ | Current user |
| `POST` | `/api/auth/password-reset/request` | — | Email a reset token |
| `POST` | `/api/auth/password-reset/confirm` | — | Consume the token, set a new password |
| `GET` | `/api/scenarios` | ✓ | List the user's scenarios with summary verdicts |
| `POST` | `/api/scenarios` | ✓ | Create a scenario, pre-filled with defaults |
| `GET` | `/api/scenarios/{id}` | ✓ | Full input set including dependents, goals, income |
| `PUT` | `/api/scenarios/{id}` | ✓ | Replace the full input set |
| `PATCH` | `/api/scenarios/{id}` | ✓ | Partial update — used by the live sliders |
| `DELETE` | `/api/scenarios/{id}` | ✓ | Delete |
| `POST` | `/api/scenarios/{id}/duplicate` | ✓ | Deep-copy |
| `POST` | `/api/scenarios/{id}/project` | ✓ | Run the projection; body may override inputs transiently for what-if without saving |
| `POST` | `/api/scenarios/{id}/solve` | ✓ | Body: `{"target": "required_corpus" \| "required_contribution" \| "longevity"}` |
| `POST` | `/api/scenarios/{id}/sensitivity` | ✓ | The 5×5 return × inflation grid (P3) |
| `POST` | `/api/scenarios/compare` | ✓ | Body: `{"scenario_ids": [...]}`; aligned series plus a metrics table |
| `GET` | `/api/scenarios/{id}/export.xlsx` | ✓ | Workbook-shaped Excel export |
| `GET` | `/api/scenarios/{id}/export.csv` | ✓ | Projection grid as CSV |
| `GET` | `/api/scenarios/{id}/export.pdf` | ✓ | One-to-two-page PDF summary |
| `GET` | `/api/scenarios/{id}/export.json` | ✓ | Portable input set |
| `POST` | `/api/scenarios/import` | ✓ | Create a scenario from an exported JSON input set |
| `POST` | `/api/project/anonymous` | — | Run a projection without saving; powers a try-before-signup demo, rate-limited by IP |
| `GET` | `/api/health` | — | Liveness probe for the host platform |

**`POST /api/scenarios/{id}/project` response shape**

```jsonc
{
  "mode": "monthly",
  "meta": {
    "plan_start": "2026-10-01",
    "months": 456,
    "current_age": 43, "retirement_age": 43, "life_expectancy": 80
  },
  "summary": {
    "verdict": "shortfall",                  // "sustainable" | "shortfall"
    "corpus_at_retirement": "15000000.00",
    "peak_corpus": "19023374.04", "peak_age": 55,
    "exhaustion_age": 67, "years_short": 13,
    "terminal_corpus": "0.00",
    "unfunded_shortfall_nominal": "65998192.05",
    "unfunded_shortfall_today": "7881027.77",
    "total_withdrawals": "...", "total_return": "...",
    "first_year_withdrawal_rate": "0.0600"
  },
  "rows": [
    {
      "t": 0, "year": 2026, "age": 43, "month": 10,
      "corpus_start": "15000000.00",
      "inflow": { "contribution": "0.00", "income": "0.00" },
      "outflow": {
        "household": "50000.00", "medical": "0.00",
        "school": "25000.00", "graduation": "0.00",
        "marriage": "0.00", "custom": "0.00", "total": "75000.00"
      },
      "investment_return": "119014.05",
      "corpus_end": "15044014.05",
      "corpus_end_today_rupees": "15044014.05",
      "shortfall": "0.00",
      "events": []
    }
  ]
}
```

Rows are returned monthly; the client aggregates to annual for the collapsed table view. For a
40-year plan this is roughly 456 rows — small enough to send in full, so no pagination is needed.
An `aggregate=annual` query parameter is available for the export and comparison paths.

---

## 8. Frontend Specification

React with TypeScript, Vite build, React Router, TanStack Query for server state, React Hook Form
with Zod for the input forms, and Chart.js (via `react-chartjs-2`) for visualisation. The build is
emitted to `app/static/` and served by FastAPI, so the whole product deploys as one process.

### 8.1 Routes

| Route | Purpose |
|---|---|
| `/` | Landing page with an anonymous, non-persisted quick calculator |
| `/login`, `/register`, `/reset-password` | Authentication |
| `/scenarios` | Scenario list, create, duplicate, delete |
| `/scenarios/:id/edit` | Five-section input wizard |
| `/scenarios/:id` | Results dashboard |
| `/compare?ids=1,2,3` | Multi-scenario overlay |

### 8.2 Input wizard

A five-step wizard on first creation and a five-tab editor thereafter, so returning users can jump
straight to the field they want. Each section validates independently and saves on blur via
`PATCH`, so no work is lost. Requirements:

- Currency fields accept `1.5cr`, `15L`, `1500000` and render back as `₹15,00,000`.
- Percentage fields accept `7` or `7%` and store `0.07`.
- The dependents and goals sections are add/remove/reorder repeaters.
- Derived values are shown live beside their inputs: monthly household expense next to the annual
  figure (restoring the intent of the orphaned `Inputs!D7`), and the effective annual school-fee
  inflation next to the biennial step (D9).
- Cross-field validation is surfaced inline, not on submit: retirement age below current age, life
  expectancy below retirement age, a marriage age below a dependent's current age.

### 8.3 Results dashboard

Top to bottom:

1. **Verdict banner** — green when sustainable, amber when the shortfall is under five years, red
   beyond that. One sentence, no jargon.
2. **Metric tiles** — the six metrics of FR-VIZ-6, in lakh/crore short form.
3. **Corpus timeline** — filled area chart, age on the x-axis, with the retirement age marked, the
   exhaustion age marked where applicable, and goal events as annotated points.
4. **Income vs. expenses** — stacked bars, inflows above the axis and outflow categories below.
5. **What-if strip** — sliders for retirement age, monthly SIP, expected return and expense
   inflation. Each change triggers a debounced (250 ms) transient `project` call; the charts
   re-render without a save, and a "Save as new scenario" button captures the result.
6. **Solver panel** — "What do I need?" reveals the required corpus and the required SIP, with the
   gap against the current plan.
7. **Projection table** — virtualised, monthly/annual toggle, nominal/real toggle, per-category
   columns, exhausted months tinted.

### 8.4 Accessibility and presentation

- Charts must not encode meaning by colour alone: the exhaustion point carries a label and the
  table marks exhausted rows textually.
- Full keyboard navigation through the wizard; visible focus rings; labels bound to inputs.
- Chart colours must hold contrast in both light and dark themes.
- All figures respect the Indian numbering convention throughout.

---

## 9. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | A full monthly projection over 40 years (≈456 rows) computes server-side in under 150 ms at the 95th percentile. |
| NFR-2 | A solver call completes in under 1 s at the 95th percentile — 80 bisection iterations over the same engine. |
| NFR-3 | All monetary arithmetic uses `decimal.Decimal`. Binary floating point for currency is prohibited. |
| NFR-4 | Every input is validated server-side against the ranges in §4.3 regardless of client validation. The engine must never receive an out-of-range value. |
| NFR-5 | Divide-by-zero, negative ages, `life_expectancy ≤ current_age` and similar degenerate inputs return `422`, never a `500` or a `NaN` in the payload. |
| NFR-6 | HTTPS enforced in production; HSTS enabled; `Secure` cookies. |
| NFR-7 | No personal data beyond email is collected. Financial inputs are stored per user and never aggregated, shared, or sent to a third party. |
| NFR-8 | Structured JSON logging with a request ID. Financial values and email addresses must never be written to logs. |
| NFR-9 | Generic OWASP baseline: parameterised queries throughout (SQLAlchemy), CORS restricted to the app origin, security headers set, request body capped at 1 MB. |
| NFR-10 | The app runs in a single container against a mounted SQLite file and must start cold in under 10 s. |
| NFR-11 | Python 3.11+; dependencies pinned in `requirements.txt` with hashes. |
| NFR-12 | The engine module carries no framework imports, so it stays usable from a CLI, a test, or a future worker. |

---

## 10. Architecture and Deployment

### 10.1 Module layout

```
app/
  main.py                 FastAPI app, router registration, static mount
  config.py               Pydantic Settings, all config from environment
  db.py                   Engine, session dependency, PRAGMA foreign_keys
  models/                 SQLAlchemy ORM models (§6)
  schemas/                Pydantic request/response models
  api/
    auth.py  scenarios.py  projection.py  export.py  health.py
  core/
    engine.py             Pure projection engine — both modes (§5.4, §5.5)
    solver.py             Bisection solvers (§5.8, §5.9)
    money.py              Decimal helpers, Indian number formatting
    defaults.py           The documented default input set
  services/
    xlsx_export.py  pdf_export.py
  static/                 Built React bundle
tests/
  test_engine_parity.py   Golden test against the source workbook
  test_engine_monthly.py  test_solver.py  test_api.py
alembic/
Dockerfile
requirements.txt
```

### 10.2 Configuration

Everything from environment variables, no host-specific code:
`DATABASE_URL` (default `sqlite:///./data/planner.db`), `SECRET_KEY`, `ACCESS_TOKEN_MINUTES`,
`REFRESH_TOKEN_DAYS`, `CORS_ORIGINS`, `SMTP_*` for password reset, `LOG_LEVEL`.

### 10.3 Deployment

A single `Dockerfile` — multi-stage: Node builds the SPA, then the Python runtime image copies the
bundle into `app/static/`. Runs `uvicorn app.main:app`. Alembic migrations run on startup.

**The SQLite caveat, stated plainly:** most PaaS hosts (Railway, Render, Fly.io, Heroku) use
ephemeral container filesystems. A SQLite file written to the container's disk is **lost on every
redeploy and restart**, taking all user scenarios with it. Two acceptable configurations:

1. **Attach a persistent volume** and point `DATABASE_URL` at a path on it — supported by Railway,
   Render and Fly. This keeps SQLite viable for the expected single-digit-to-low-hundreds user
   count. This is the recommended v1 configuration.
2. **Switch to Postgres** by changing `DATABASE_URL` alone. Because all access is through
   SQLAlchemy and Alembic, no application code changes. This is the migration path if the app ever
   outgrows single-writer concurrency.

The deployment documentation must state this prominently; silently losing a user's financial plan
on redeploy would be the single worst failure this product could have.

Also required: a daily backup task copying the SQLite file to object storage
(`VACUUM INTO` for a consistent snapshot), and a documented restore procedure.

---

## 11. Testing Strategy

| Layer | What is tested |
|---|---|
| **Golden parity test** | `test_engine_parity.py` loads `Retirement_Planner_Calculator_05102025.xlsx` with `openpyxl`, reads the cached values of all 38 in-range rows × 18 columns, and asserts the `annual_parity` engine matches within ₹1. A reference implementation has already been validated at **₹0.04 maximum deviation**, so this test is known achievable. Rows beyond the exhaustion point assert the corrected floored behaviour instead, with the divergence from the workbook documented in the test itself. |
| **Unit — cost formulas** | Each of `HH`, `SCH_j`, `GRAD_j`, `MAR_j`, `GOAL`, `SIP`, `INC_k` tested independently against hand-computed values, including the boundary years: the year a dependent turns 18, the first and last graduation instalment, the exact marriage year, the retirement transition year. |
| **Unit — rate conversion** | `(1 + r_m)^12 == 1 + r_a` to 10 decimal places, across a range including zero and negative returns. |
| **Unit — floor behaviour** | A corpus driven to exactly zero, and one driven negative, both assert no negative balance and no return accrued after exhaustion. This is the regression test for D1. |
| **Property-based** (Hypothesis) | Over valid input ranges: the corpus is never negative; a higher starting corpus never produces a worse outcome; a higher return never produces a worse outcome; monthly mode is never worse than annual mode. |
| **Solver** | Convergence within tolerance and iteration cap; round-trip consistency — feeding the solved required corpus back through the engine yields no shortfall; documented infeasible cases return the structured error rather than a number. |
| **API contract** | Each endpoint's happy path, `401` when unauthenticated, `404` for another user's scenario (FR-AUTH-5), `422` for each documented validation rule. |
| **Frontend** | Component tests for the currency and percentage parsers, the repeater controls, and cross-field validation; one Playwright end-to-end run covering register → create scenario → view results → adjust slider → solve → export. |
| **Export fidelity** | The exported `.xlsx` reopens in `openpyxl` with the expected sheet names, headers and values. |

---

## 12. Phased Roadmap

**P0 — Trustworthy engine and a picture** *(the minimum that beats the spreadsheet)*
Projection engine in both modes; the corpus floor and exhaustion reporting; contributions and
income inputs; the anonymous single-page calculator; corpus and income/expense charts; projection
table; golden parity test. No accounts yet — inputs live in the URL or local storage.

**P1 — Accounts and answers**
Registration, login, sessions; scenario CRUD; the required-corpus and required-contribution
solvers; metric tiles; the what-if slider strip.

**P2 — Real households and sharing**
Generalised dependents, custom goals and income streams; scenario comparison; Excel, CSV, PDF and
JSON export/import; password reset; the real-terms and monthly/annual toggles; goal markers.

**P3 — Depth** *(stretch; explicitly deferred so it cannot bloat v1)*
Sensitivity grid; Monte Carlo and sequence-of-returns risk; Indian income and capital-gains tax
modelling; asset-class allocation with per-class returns; multi-currency; adviser mode with client
grouping.

---

## 13. Assumptions and Open Questions

### 13.1 Assumptions taken where the workbook was ambiguous

1. **Lump-sum goals land in the first month of their plan year.** The annual model gives no
   intra-year timing. First-month placement is conservative — the money leaves earlier and earns
   less — and is stated in the UI.
2. **The pre-retirement expense suppression is retained as the default**, matching the workbook,
   but is now an explicit toggle rather than an invisible formula branch (D8).
3. **Returns are net of tax and fees.** Since v1 models no tax, the field help text instructs the
   user to enter a net figure.
4. **The biennial school-fee step is time-anchored, not grade-anchored** — it escalates with
   elapsed plan years, identically for every dependent. This is the workbook's behaviour and is
   preserved; the form now shows the implied annual rate so the assumption is visible.
5. **"Base Year" becomes a derived display field.** The plan start date is the real anchor; base
   year is retained only so exports resemble the original sheet.
6. **A single household.** Spouse income is expressed as an income stream rather than as a second
   modelled person with their own retirement date.

### 13.2 Open questions for the product owner

| # | Question | Why it matters | Proposed default if unanswered |
|---|---|---|---|
| Q1 | Should the anonymous calculator on the landing page be built in P0, or should everything sit behind login? | Changes P0 scope and the shape of the rate limiting | Build it — it is the cheapest way to demonstrate value before asking for a signup |
| Q2 | Is a desired legacy/inheritance amount a real requirement, or is "corpus reaches zero exactly at life expectancy" sufficient? | Adds a field and changes the solver's objective | Include the field, default ₹0 |
| Q3 | Should partial-year handling matter — a plan starting mid-year against birthdays that fall mid-year? | Ages currently step on the plan anniversary, not the actual birthday, which can be up to eleven months out | Keep the anniversary convention, matching the workbook; document it |
| Q4 | Is email delivery available for password reset in P2, or should recovery be deferred? | Requires SMTP credentials and a provider | Defer reset to P2 and require a support-contact route until then |
| Q5 | Is Postgres acceptable from day one instead of SQLite on a volume? | Removes the persistence caveat in §10.3 entirely | Ship SQLite on a volume, keep the one-line migration path |

---

## 14. Appendix

Extracted mechanically from `Retirement_Planner_Calculator_05102025.xlsx` so the golden parity
test of §11 has a source of truth that cannot drift from this document.

### A. `Inputs` sheet — verbatim

| Cell | Label | Value |
|---|---|---|
| `B3` | Current Age (You) | 43 |
| `B4` | Life Expectancy | 80 |
| `B5` | Retirement Age | 43 |
| `B6` | Current Corpus (₹) | 15,000,000 |
| `B7` | Annual Household Expense Today (₹) | 600,000 |
| `B8` | Household Expense Inflation (annual) | 7% |
| `B9` | Pre-Retirement Return (annual) | 10% |
| `B10` | Post-Retirement Return (annual) | 10% |
| `B11` | Son Age Now | 13 |
| `B12` | Daughter Age Now | 4 |
| `B13` | Son School Fee Today (₹) | 200,000 |
| `B14` | Daughter School Fee Today (₹) | 100,000 |
| `B15` | School Fee Hike (step every 2 yrs) | 25% |
| `B16` | Graduation Total Today (4 yrs) (₹) | 1,200,000 |
| `B17` | Graduation Inflation (annual) | 7% |
| `B18` | Marriage Cost Today (₹) | 500,000 |
| `B19` | Marriage Inflation (annual) | 7% |
| `B20` | Marriage Age (Son) | 28 |
| `B21` | Marriage Age (Daughter) | 25 |
| `B22` | School Fee Hike Frequency (yrs) | 2 |
| `B23` | Base Year | 2026 |
| `D7` | *(orphan helper)* | `=B7/12` → 50,000 |

### B. `Projection` sheet — the formula of row 2, copied down all 39 rows

Every data row is this same formula set with the row number advanced.

| Col | Header | Formula |
|---|---|---|
| `A` | Year | `=Inputs!B23 + ROW()-2` |
| `B` | Your Age | `=Inputs!B3 + ROW()-2` |
| `C` | Corpus Start (₹) | `=IF(ROW()=2,Inputs!B6,R1)` |
| `D` | Household Expense (₹) | `=IF(B2<Inputs!B5,0, Inputs!B7*(1+Inputs!B8)^(B2-Inputs!B3))` |
| `E` | Son Age | `=Inputs!B11 + (B2-Inputs!B3)` |
| `F` | Daughter Age | `=Inputs!B12 + (B2-Inputs!B3)` |
| `G` | Son School Fee (₹) | `=IF(E2<18, Inputs!B13*(1+Inputs!B15)^(INT((B2-Inputs!B3)/Inputs!B22)), 0)` |
| `H` | Daughter School Fee (₹) | `=IF(F2<18, Inputs!B14*(1+Inputs!B15)^(INT((B2-Inputs!B3)/Inputs!B22)), 0)` |
| `I` | Total School Fees (₹) | `=G2+H2` |
| `J` | Son Graduation (₹) | `=IF(AND(E2>=18,E2<=21), (Inputs!B16*(1+Inputs!B17)^(18-Inputs!B11))/4, 0)` |
| `K` | Daughter Graduation (₹) | `=IF(AND(F2>=18,F2<=21), (Inputs!B16*(1+Inputs!B17)^(18-Inputs!B12))/4, 0)` |
| `L` | Total Graduation (₹) | `=J2+K2` |
| `M` | Son Marriage (₹) | `=IF(E2=Inputs!B20, Inputs!B18*(1+Inputs!B19)^(Inputs!B20-Inputs!B11), 0)` |
| `N` | Daughter Marriage (₹) | `=IF(F2=Inputs!B21, Inputs!B18*(1+Inputs!B19)^(Inputs!B21-Inputs!B12), 0)` |
| `O` | Total Marriage (₹) | `=M2+N2` |
| `P` | Total Withdrawals (₹) | `=D2+I2+L2+O2` |
| `Q` | Investment Return (₹) | `=(C2-P2)*IF(B2<Inputs!B5,Inputs!B9,Inputs!B10)` |
| `R` | Corpus End (₹) | `=(C2-P2)+Q2` |

### C. `Projection` cached values — the golden fixture

Ages 43–80 are the in-range rows the parity test asserts. **The age-81 row is the off-by-one
of defect D2 and is excluded.** All values are in ₹.

| Year | Age | Corpus Start | Household | Son School | Dau School | School Total | Grad Total | Marriage Total | Withdrawals | Return | Corpus End |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 43 | 15,000,000 | 600,000 | 200,000 | 100,000 | 300,000 | 0 | 0 | 900,000 | 1,410,000 | 15,510,000 |
| 2027 | 44 | 15,510,000 | 642,000 | 200,000 | 100,000 | 300,000 | 0 | 0 | 942,000 | 1,456,800 | 16,024,800 |
| 2028 | 45 | 16,024,800 | 686,940 | 250,000 | 125,000 | 375,000 | 0 | 0 | 1,061,940 | 1,496,286 | 16,459,146 |
| 2029 | 46 | 16,459,146 | 735,026 | 250,000 | 125,000 | 375,000 | 0 | 0 | 1,110,026 | 1,534,912 | 16,884,032 |
| 2030 | 47 | 16,884,032 | 786,478 | 312,500 | 156,250 | 468,750 | 0 | 0 | 1,255,228 | 1,562,880 | 17,191,685 |
| 2031 | 48 | 17,191,685 | 841,531 | 0 | 156,250 | 156,250 | 420,766 | 0 | 1,418,547 | 1,577,314 | 17,350,452 |
| 2032 | 49 | 17,350,452 | 900,438 | 0 | 195,312 | 195,312 | 420,766 | 0 | 1,516,516 | 1,583,394 | 17,417,330 |
| 2033 | 50 | 17,417,330 | 963,469 | 0 | 195,312 | 195,312 | 420,766 | 0 | 1,579,547 | 1,583,778 | 17,421,561 |
| 2034 | 51 | 17,421,561 | 1,030,912 | 0 | 244,141 | 244,141 | 420,766 | 0 | 1,695,818 | 1,572,574 | 17,298,318 |
| 2035 | 52 | 17,298,318 | 1,103,076 | 0 | 244,141 | 244,141 | 0 | 0 | 1,347,216 | 1,595,110 | 17,546,212 |
| 2036 | 53 | 17,546,212 | 1,180,291 | 0 | 305,176 | 305,176 | 0 | 0 | 1,485,467 | 1,606,075 | 17,666,820 |
| 2037 | 54 | 17,666,820 | 1,262,911 | 0 | 305,176 | 305,176 | 0 | 0 | 1,568,087 | 1,609,873 | 17,708,606 |
| 2038 | 55 | 17,708,606 | 1,351,315 | 0 | 381,470 | 381,470 | 0 | 0 | 1,732,785 | 1,597,582 | 17,573,403 |
| 2039 | 56 | 17,573,403 | 1,445,907 | 0 | 381,470 | 381,470 | 0 | 0 | 1,827,377 | 1,574,603 | 17,320,629 |
| 2040 | 57 | 17,320,629 | 1,547,120 | 0 | 0 | 0 | 773,560 | 0 | 2,320,681 | 1,499,995 | 16,499,943 |
| 2041 | 58 | 16,499,943 | 1,655,419 | 0 | 0 | 0 | 773,560 | 1,379,516 | 3,808,495 | 1,269,145 | 13,960,593 |
| 2042 | 59 | 13,960,593 | 1,771,298 | 0 | 0 | 0 | 773,560 | 0 | 2,544,858 | 1,141,573 | 12,557,308 |
| 2043 | 60 | 12,557,308 | 1,895,289 | 0 | 0 | 0 | 773,560 | 0 | 2,668,849 | 988,846 | 10,877,305 |
| 2044 | 61 | 10,877,305 | 2,027,959 | 0 | 0 | 0 | 0 | 0 | 2,027,959 | 884,935 | 9,734,280 |
| 2045 | 62 | 9,734,280 | 2,169,917 | 0 | 0 | 0 | 0 | 0 | 2,169,917 | 756,436 | 8,320,800 |
| 2046 | 63 | 8,320,800 | 2,321,811 | 0 | 0 | 0 | 0 | 0 | 2,321,811 | 599,899 | 6,598,888 |
| 2047 | 64 | 6,598,888 | 2,484,337 | 0 | 0 | 0 | 0 | 2,070,281 | 4,554,619 | 204,427 | 2,248,696 |
| 2048 | 65 | 2,248,696 | 2,658,241 | 0 | 0 | 0 | 0 | 0 | 2,658,241 | -40,954 | -450,499 |
| 2049 | 66 | -450,499 | 2,844,318 | 0 | 0 | 0 | 0 | 0 | 2,844,318 | -329,482 | -3,624,299 |
| 2050 | 67 | -3,624,299 | 3,043,420 | 0 | 0 | 0 | 0 | 0 | 3,043,420 | -666,772 | -7,334,491 |
| 2051 | 68 | -7,334,491 | 3,256,460 | 0 | 0 | 0 | 0 | 0 | 3,256,460 | -1,059,095 | -11,650,046 |
| 2052 | 69 | -11,650,046 | 3,484,412 | 0 | 0 | 0 | 0 | 0 | 3,484,412 | -1,513,446 | -16,647,903 |
| 2053 | 70 | -16,647,903 | 3,728,321 | 0 | 0 | 0 | 0 | 0 | 3,728,321 | -2,037,622 | -22,413,846 |
| 2054 | 71 | -22,413,846 | 3,989,303 | 0 | 0 | 0 | 0 | 0 | 3,989,303 | -2,640,315 | -29,043,464 |
| 2055 | 72 | -29,043,464 | 4,268,554 | 0 | 0 | 0 | 0 | 0 | 4,268,554 | -3,331,202 | -36,643,220 |
| 2056 | 73 | -36,643,220 | 4,567,353 | 0 | 0 | 0 | 0 | 0 | 4,567,353 | -4,121,057 | -45,331,631 |
| 2057 | 74 | -45,331,631 | 4,887,068 | 0 | 0 | 0 | 0 | 0 | 4,887,068 | -5,021,870 | -55,240,568 |
| 2058 | 75 | -55,240,568 | 5,229,162 | 0 | 0 | 0 | 0 | 0 | 5,229,162 | -6,046,973 | -66,516,704 |
| 2059 | 76 | -66,516,704 | 5,595,204 | 0 | 0 | 0 | 0 | 0 | 5,595,204 | -7,211,191 | -79,323,098 |
| 2060 | 77 | -79,323,098 | 5,986,868 | 0 | 0 | 0 | 0 | 0 | 5,986,868 | -8,530,997 | -93,840,963 |
| 2061 | 78 | -93,840,963 | 6,405,949 | 0 | 0 | 0 | 0 | 0 | 6,405,949 | -10,024,691 | -110,271,603 |
| 2062 | 79 | -110,271,603 | 6,854,365 | 0 | 0 | 0 | 0 | 0 | 6,854,365 | -11,712,597 | -128,838,565 |
| 2063 | 80 | -128,838,565 | 7,334,171 | 0 | 0 | 0 | 0 | 0 | 7,334,171 | -13,617,274 | -149,790,010 |
| 2064 | 81 | -149,790,010 | 7,847,563 | 0 | 0 | 0 | 0 | 0 | 7,847,563 | -15,763,757 | -173,401,330 |

The corpus turns negative at age 65 and, because the workbook keeps applying a +10% return to a
negative balance (defect D1), reaches **−₹17,34,01,330** by age 81. Neither that figure nor any
value after exhaustion is reproduced by the new engine; see FR-ENG-5.

---

*End of document.*
