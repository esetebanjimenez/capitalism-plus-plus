/**
 * ?company=demo: the Company report with fixed example data, for PR screenshots (#257).
 * Operating profit is a loss that shrank (red figure, green up arrow); other profit fell
 * (green figure, red down arrow). Add &firm=1 for the By firm view, &tab=Charts for the
 * Charts tab (#258) and &range=years for its Past years switch.
 */
import { loadUiAtlas } from "./atlas";
import { CorpJson, ReportState, TABS, Tab, companyReport } from "./company";
import { isDesktop } from "./layout";
import { Shell } from "./shell";

const L = (m: number[], lm: number[], y: number[]) => ({ cash: 0, month: m, last_month: lm, year: y });

export const DEMO_CORP: CorpJson = {
  id: 0,
  name: "Player",
  revenue: 412_300,
  operating_expenses: 532_300,
  operating_profit: -120_000,
  other_profit: 45_000,
  net_profit: -75_000,
  ledger: L(
    [412_300, -186_000, -100_000, -12_000, -151_000, -38_500, -24_800, -2_000, -18_000, -9_000, 54_000, 0],
    [301_900, -181_000, -100_000, -12_000, -160_200, -35_100, -20_000, 0, -16_400, -9_000, 69_000, 0],
    [2_431_600, -1_402_000, -800_000, -96_000, -1_255_300, -301_600, -188_000, -6_200, -140_100, -72_000, 410_000, 0],
  ),
  by_firm: [
    { firm: 3, ledger: L([412_300, -98_000, -60_000, -8_000, -151_000, -38_500, -24_800, -2_000, 0, 0, 0, 0], [301_900, -95_000, -60_000, -8_000, -160_200, -35_100, -20_000, 0, 0, 0, 0, 0], [2_431_600, -760_000, -480_000, -64_000, -1_255_300, -301_600, -188_000, -6_200, 0, 0, 0, 0]) },
    { firm: 7, ledger: L([0, -88_000, -40_000, -4_000, 0, 0, 0, 0, -18_000, 0, 0, 0], [0, -86_000, -40_000, -4_000, 0, 0, 0, 0, -16_400, 0, 0, 0], [0, -642_000, -320_000, -32_000, 0, 0, 0, 0, -140_100, 0, 0, 0]) },
  ],
  // Twelve complete months up to Feb 1991 (the demo date is Mar 1991). Operating profit crosses zero.
  month_history: {
    revenue: [0, 0, 48_000, 96_500, 141_000, 180_200, 214_800, 251_000, 262_400, 288_900, 301_900, 412_300],
    operating_profit: [-210_000, -260_000, -312_000, -280_500, -190_000, -95_000, 12_000, 64_000, 41_000, -40_000, -300_000, -120_000],
    other_profit: [0, 0, 5_000, 12_000, 20_500, 31_000, 38_000, 44_500, 52_000, 58_000, 60_000, 45_000],
    expenses: [210_000, 260_000, 360_000, 377_000, 331_000, 275_200, 202_800, 187_000, 221_400, 328_900, 601_900, 532_300],
    net_worth: [9_790_000, 9_530_000, 9_223_000, 8_954_500, 8_785_000, 8_721_000, 8_771_000, 8_879_500, 8_972_500, 8_990_500, 8_750_500, 8_675_500],
  },
  year_history: {
    revenue: [1_284_600],
    operating_profit: [-1_420_500],
    other_profit: [261_000],
    expenses: [2_705_100],
    net_worth: [8_840_500],
  },
};

/** The demo's game date, so chart labels run Mar 1990 to Feb 1991. */
export const DEMO_TODAY = { year: 1991, month: 3 };

const NAMES: Record<number, string> = { 3: "Department Store #3", 7: "Factory #7" };

export async function showCompanyDemo(resolution: number, byFirm: boolean, params = new URLSearchParams()): Promise<void> {
  await loadUiAtlas(resolution);
  document.body.style.background = "#9fbf8a";
  const shell = new Shell(document.body);
  const open = (s: ReportState) =>
    shell.open(
      companyReport(DEMO_CORP, s, {
        firmLabel: (id) => NAMES[id] ?? `Firm #${id}`,
        onFirm: () => {},
        onState: open,
        today: DEMO_TODAY,
        chartWidth: isDesktop(window.innerWidth) ? 352 : Math.min(480, window.innerWidth - 48),
      }),
    );
  const tab = (TABS as readonly string[]).includes(params.get("tab") ?? "") ? (params.get("tab") as Tab) : "Income";
  open({ tab, byFirm, chartRange: params.get("range") === "years" ? "years" : "months" });
}
