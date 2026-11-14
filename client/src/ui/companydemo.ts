/**
 * ?company=demo: the Company report with fixed example data, for PR screenshots (#257).
 * Operating profit is a loss that shrank (red figure, green up arrow); other profit fell
 * (green figure, red down arrow). Add &firm=1 for the By firm view.
 */
import { loadUiAtlas } from "./atlas";
import { CorpJson, ReportState, companyReport } from "./company";
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
  month_history: { operating_profit: [-300_000, -120_000], other_profit: [60_000, 45_000] },
};

const NAMES: Record<number, string> = { 3: "Department Store #3", 7: "Factory #7" };

export async function showCompanyDemo(resolution: number, byFirm: boolean): Promise<void> {
  await loadUiAtlas(resolution);
  document.body.style.background = "#9fbf8a";
  const shell = new Shell(document.body);
  const open = (s: ReportState) =>
    shell.open(companyReport(DEMO_CORP, s, { firmLabel: (id) => NAMES[id] ?? `Firm #${id}`, onFirm: () => {}, onState: open }));
  open({ tab: "Income", byFirm });
}
