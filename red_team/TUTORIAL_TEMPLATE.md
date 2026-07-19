# Tutorial Authoring Guide — Concept-First, Source-Grounded

A reusable structure for writing module tutorials. The goal: teach the **concepts** first (grounded in official documentation), keep the page **scannable**, and put all **code at the end**. Use this as the blueprint when creating a tutorial for a new module.

> **Exemplar:** `promptfoo-tutorial.md` in this folder was built with this structure. Refer to it for a concrete example of every section below.

---

## 1. Core principles

1. **Concept-first, code-last.** Explain *what* and *why* in prose/tables. Collect all configuration/code into one section near the end. Concepts may name a feature or show a 1-line snippet for context, but never carry full config.
2. **Grounded in official sources.** Every fact — counts, IDs, commands, defaults, taxonomy — comes from the official docs, verified. Do not invent or infer. When docs conflict or a summary is uncertain, re-read the source before writing.
3. **Scannable, not text-heavy.** Prefer tables, short bullets, and one diagram over paragraphs. A reader should be able to skim headers and tables and still get the model.
4. **Consistent nomenclature.** Use the module's *own* terminology from its docs, so the tutorial transfers directly to the official reference.
5. **Coherent and cross-linked.** One consistent sequence throughout (diagram → overview → detail → config). Internal links between concept and its config; a docs link per section.
6. **Durable phrasing for volatile facts.** Counts and versions drift — write "30+ (X at time of writing)" rather than a bare number that will rot.

---

## 2. Section skeleton

Order matters. This is the do-it flow: understand → install → configure → run → troubleshoot → reference.

| # | Section | Purpose | Contains |
|---|---------|---------|----------|
| 1 | **Title + Intro** | What the module is, in 3–5 sentences | One-line definition · a small "what it does" table · a "works with" line. No code, no scope warnings. |
| 2 | **Contents (TOC)** | Navigation for longer tutorials | A bullet list linking each top-level section, with the components nested inline. Add once the page exceeds ~2 screens. |
| 3 | **How it works (conceptual model)** | The mental model in one loop/flow | A lead-in sentence · **one diagram** of the flow · a **building-blocks table** (each component, one line) · a one-line summary · a docs link. |
| 4 | **Components in detail** | Deep-dive each building block | One `###` subsection per component, **in the same order as the diagram**. Concept only — no YAML. See §3 for the per-component template. |
| 5 | **Installation** | How to install | Smallest viable set (one method + a link to the rest). A requirements note. |
| 6 | **Configuration** | All the code, in one place | One `###` per component showing its snippet + option table, then a **Full config** with a comment on each meaningful line. See §4. |
| 7 | **Running / Usage** | The commands to actually run it | A command table + a copy-paste block + a "start small" tip + docs link. |
| 8 | **Troubleshooting** | Common failures and fixes | A **symptom → likely cause → fix** table, grounded in the module's official troubleshooting/best-practices pages. |
| 9 | **Appendix(es)** | Operational/edge topics | Anything that would interrupt the main flow: deployment modes, environment variables, auth, local-vs-remote. |
| 10 | **Resources** | One link index | Every official page cited throughout, grouped by topic (getting started · components · troubleshooting). |

**Troubleshooting** and **Resources** are what make a tutorial *usable*, not just readable — don't skip them. Build Troubleshooting from the module's own troubleshooting/best-practices docs (symptom → cause → fix); build Resources by collecting every "Docs" link you cited into one grouped index.

---

## 3. Per-component template (Section 3 "Components in detail")

Each component subsection follows the same shape so the section reads predictably:

```
### N. <Component>

- **What it is** — one or two sentences, in the module's own terms.
- **Why it matters** — what breaks or degrades if you get it wrong.
- **At a glance** — (for rich components) counts / taxonomy / the "kinds" of this thing,
  pulled verbatim-in-spirit from the docs. Use a table when there are categories.
- **<Key sub-topics>** — naming conventions, options, sub-types — as short bullets or tables.
- **Which to pick / how to choose** — practical guidance mapping the component to the reader's case.
- **Docs** — [link to the official page for this component]
```

Notes:
- **Keep config out.** Where the reader would set it, link to the Configuration section instead of showing YAML.
- **Depth can vary** by how much surface a component has — that's fine, but keep the header bullets (What it is / Why it matters / Docs) consistent.
- **"At a glance"** is the high-value block: it answers "how many / what kinds / how capable" with a taxonomy table. Verify these numbers against the source.

---

## 4. Configuration section conventions

- **Per-component subsections first**, then a single **Full config**.
- Each subsection: a 1–2 sentence description, the minimal snippet, and an **option table** (key · what it does) where relevant. Link back to the matching concept (`see the [X concept](#n-x)`).
- **Full config** = a minimal, runnable file with a comment on each meaningful line. Label it as *minimal* — it need not include every optional key shown above; say so to avoid over-promising.
- End with a "to use it" line naming the few things the reader swaps for their own case.

---

## 5. Formatting conventions

- **Diagram:** one ASCII flow in the conceptual section, ordered the way the thing actually happens. Every later section follows that same order. **Verify alignment by reading it back** — in monospace, box borders, rails, and loop arrows must line up. A single vertical rail (one column of `│`/`▼`, with a small right-side loop for cycles) is easier to keep aligned than nested boxes.
- **Table of contents:** a bullet list right after the intro for anything longer than ~2 screens; nest the components inline under "Components in detail". Confirm each anchor resolves (watch punctuation-heavy headings, e.g. `Report / Findings` → `#report--findings`).
- **Tables** for: "what it does" comparisons, taxonomies/catalogs, options, command lists.
- **Bullets** with bold lead-ins (`- **Term** — explanation`) for component attributes.
- **Callouts** (`> **Note:**`) for a single important caveat.
- **Inline code** for every id, command, flag, and file/field name.
- **Emoji sparingly** (e.g. ⭐ for "recommended") and always define it.

---

## 6. Sourcing & accuracy rules

- **Fetch the official page** for each section before writing it; quote its structure/terminology.
- **Cross-check anything a summarizer returns.** If two fetches disagree (e.g. category counts, an ID), re-read the source with a targeted query until it's unambiguous.
- **Cite** the official page as a "Docs" link in each section.
- **Prefer the docs' own classification** over one you invent. If the docs have two overlapping groupings, pick one and say which.
- **Flag volatile facts** (counts, model defaults, prices) as "at time of writing".
- **Never state a command/flag you haven't confirmed.**

---

## 7. Coherence checklist (run before "done")

- [ ] Diagram order == building-blocks table order == Components order == Config order.
- [ ] ASCII diagram alignment verified by reading it back (borders/rails/arrows line up).
- [ ] Every internal link resolves to a real heading anchor (no dead `#...`), including the TOC.
- [ ] Terminology is consistent and matches the official docs.
- [ ] No YAML/code in concept sections; all code in Configuration/Running.
- [ ] Counts/IDs/commands verified against sources; volatile ones hedged.
- [ ] Each major section has a Docs link, and the Resources index includes every page cited.
- [ ] Troubleshooting rows are grounded in official troubleshooting/best-practices docs.
- [ ] Section order = understand → install → configure → run → troubleshoot → appendix → resources.
- [ ] No dangling references (a sentence that promises a list/diagram that isn't there).
- [ ] Claims are accurate (e.g. what runs locally vs remotely) across *all* sections, not just one.

---

## 8. Quick start for a new module tutorial

1. Identify the module's official **intro/overview**, **core-concept**, **per-feature**, **config**, and **CLI/usage** pages.
2. Draft the **conceptual model** (diagram + building-blocks table) from the overview.
3. Write **Components in detail** one component at a time (§3), verifying each against its docs page.
4. Move all code into **Configuration** (§4) as you go; keep concepts clean.
5. Add **Installation** and **Running**.
6. Add **Troubleshooting** (from the module's troubleshooting/best-practices pages) and a grouped **Resources** index.
7. Push operational/edge topics into an **Appendix**; add a **Contents (TOC)** at the top if the page is long.
8. Run the **coherence checklist** (§7).
