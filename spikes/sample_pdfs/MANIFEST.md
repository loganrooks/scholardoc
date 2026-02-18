# Sample PDF Corpus Manifest

These PDF files are the local test corpus used for spike experiments and pipeline
validation. They are **not version-controlled** (gitignored via `*.pdf` rule).
If you clone this repo, you will need to obtain these files independently.

## Corpus (20 files)

| Filename | Subject / Author | Notes |
|----------|-----------------|-------|
| Acts of Religion (Jacques Derrida) (2016) (Z-Library).pdf | Philosophy / Derrida | Full text |
| Aristotle- Nicomachean Ethics (Aristotle) (---) (Z-Library).pdf | Philosophy / Aristotle | Full text |
| ComayRebecca_MourningSickness_HegelAndTheFrenchRevolution.pdf | Philosophy / Comay | Full text |
| derrida_footnote_pages_120_125.pdf | Philosophy / Derrida | Page excerpt (pp. 120-125) -- footnote testing |
| Derrida_MarginsOfPhilosophy.pdf | Philosophy / Derrida | Full text |
| Derrida_TheBeastAndTheSovereignVol1.pdf | Philosophy / Derrida | Full text |
| Derrida_TheTruthInPainting.pdf | Philosophy / Derrida | Full text |
| Derrida_WritingAndDifference.pdf | Philosophy / Derrida | Full text |
| Dissemination (Jacques Derrida) (Z-Library).pdf | Philosophy / Derrida | Full text |
| Heidegger_BeingAndTime.pdf | Philosophy / Heidegger | Full text |
| Heidegger_DiscourseOnThinking.pdf | Philosophy / Heidegger | Full text |
| heidegger_pages_17-24_full_translator_preface.pdf | Philosophy / Heidegger | Page excerpt (pp. 17-24) -- translator preface testing |
| heidegger_pages_22-23_primary_footnote_test.pdf | Philosophy / Heidegger | Page excerpt (pp. 22-23) -- footnote testing |
| Heidegger_Pathmarks.pdf | Philosophy / Heidegger | Full text |
| Kant_CritiqueOfJudgement.pdf | Philosophy / Kant | Full text |
| kant_critique_pages_64_65.pdf | Philosophy / Kant | Page excerpt (pp. 64-65) -- targeted spike testing |
| Lenin_StateAndRevolution.pdf | Political Theory / Lenin | Full text |
| Monolingualism of the Other or, The Prosthesis of Origin (Cultural Memory in the Present) (Jacques Derrida) (Z-Library).pdf | Philosophy / Derrida | Full text |
| Plato Complete Works (Plato, John M. Cooper, D. S. Hutchinson) (1997) (Z-Library).pdf | Philosophy / Plato | Full text, large anthology |
| Rogues Two Essays on Reason (Meridian Crossing Aesthetics) (Jacques Derrida) (Z-Library).pdf | Philosophy / Derrida | Full text |

## Notes

- **16 full texts**: Primarily continental philosophy (Derrida, Heidegger, Kant, Plato,
  Aristotle) plus political theory (Lenin) and critical theory (Comay).
- **4 page excerpts**: `derrida_footnote_pages_120_125.pdf`,
  `heidegger_pages_17-24_full_translator_preface.pdf`,
  `heidegger_pages_22-23_primary_footnote_test.pdf`, and
  `kant_critique_pages_64_65.pdf` -- used for targeted spike testing of footnote
  extraction, translator prefaces, and layout edge cases.
- Total corpus size: ~131 MB.
