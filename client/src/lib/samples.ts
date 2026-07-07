import type { Verdict } from "../types";

export interface SampleDoc {
  id: string;
  label: string;
  hint: string;
  expected: Verdict;
  text: string;
}

// One-click demo documents. The first is the centrepiece: plain prose with no
// marking and no keyword — the legacy baseline waves it through, Spillguard
// catches it.
export const SAMPLES: SampleDoc[] = [
  {
    id: "money",
    label: "Unmarked CTI",
    hint: "The money shot — reads clean, isn't",
    expected: "BLOCK",
    text: "Team — quick update before the weekend. The propulsion test on the Vanguard program failed at 14:32 due to turbopump cavitation, and the measured thrust fell about 12% short of the spec. Let's regroup Monday to plan the retest.",
  },
  {
    id: "clean",
    label: "Clean memo",
    hint: "Genuinely harmless",
    expected: "ALLOW",
    text: "Reminder: the quarterly all-hands moved to Thursday at 10am in the main conference room. Lunch will be provided — please RSVP so we can get a headcount for catering.",
  },
  {
    id: "classified",
    label: "Classified banner",
    hint: "Literal marking → hard block",
    expected: "BLOCK",
    text: "SECRET//NOFORN\nThe following assessment concerns adversary radar capabilities observed during the exercise and must be handled per program guidance.",
  },
  {
    id: "marked",
    label: "Correctly marked CUI",
    hint: "Properly labelled → advisory flag",
    expected: "FLAG",
    text: "CUI//SP-CTI\nThe propulsion test on the Vanguard program failed at 14:32 due to turbopump cavitation. Distribution limited to program personnel.",
  },
  {
    id: "pii",
    label: "PII spillage",
    hint: "Unmarked SSN",
    expected: "BLOCK",
    text: "Please onboard the new contractor. Their SSN: 123-45-6789 and start date is next Monday. Forward this to the vendor so they can set up payroll.",
  },
  {
    id: "procure",
    label: "Source selection",
    hint: "Pre-award procurement info",
    expected: "BLOCK",
    text: "Between us before the award is announced: we evaluated the three offerors and ranked Cobalt Systems first on technical merit, mostly because their proposal pricing came in well under the others.",
  },
];
