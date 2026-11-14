/**
 * ?stocks=demo: the Stocks list with fixed example data, for PR screenshots and tests (#260).
 * &corp=N opens that corporation's page instead, &range=day|month|year picks the chart tab.
 */
import { loadUiAtlas } from "./atlas";
import { isDesktop } from "./layout";
import { Shell } from "./shell";
import { PriceRange, StockJson, StockRowJson, stockPage, stocksList } from "./stocks";

export const DEMO_STOCKS: StockRowJson[] = [
  { corp: 0, name: "Esteban Holdings", price: 18.25, pe_ratio: 14.2, owned_pct: 62.0, holding_value: 11_315_000 },
  { corp: 1, name: "Atlas Trading", price: 24.6, pe_ratio: 9.8, owned_pct: 4.5, holding_value: 1_107_000 },
  { corp: 2, name: "Northwind Foods", price: 7.1, pe_ratio: null, owned_pct: 0, holding_value: 0 },
  { corp: 3, name: "Crown Retail Group", price: 41.35, pe_ratio: 22.5, owned_pct: 0, holding_value: 0 },
];

const wave = (n: number, base: number, amp: number, step: number) =>
  Array.from({ length: n }, (_, i) => Math.round((base + amp * Math.sin(i / 3) + step * i) * 100) / 100);

export const DEMO_STOCK: StockJson = {
  corp: 1,
  price: 24.6,
  pe_ratio: 9.8,
  daily_prices: wave(30, 22, 1.5, 0.08),
  monthly_prices: wave(14, 15, 2, 0.6),
  yearly_prices: [12.4, 19.8],
  total_shares: 10_000_000,
  public_float: 3_550_000,
  dividend_yield: 0.024,
  shareholders: [
    { kind: "person", id: 0, name: "Founder", shares: 6_000_000, pct: 60, value: 147_600_000 },
    { kind: "corp", id: 0, name: "Esteban Holdings", shares: 450_000, pct: 4.5, value: 11_070_000 },
  ],
};

/** 1 Mar 1993; day serials count days since 1 Jan 1900 (news.ts serialDate). */
const TODAY = { year: 1993, month: 3, day_serial: (Date.UTC(1993, 2, 1) - Date.UTC(1900, 0, 1)) / 86_400_000 };

export async function showStocksDemo(resolution: number, params: URLSearchParams): Promise<void> {
  await loadUiAtlas(resolution);
  document.body.style.background = "#9fbf8a";
  const shell = new Shell(document.body);
  const corp = params.get("corp");
  let range = (params.get("range") as PriceRange | null) ?? "day";
  const page = () =>
    shell.open(
      stockPage(DEMO_STOCKS[1].name, DEMO_STOCK, {
        range,
        today: TODAY,
        chartWidth: isDesktop(window.innerWidth) ? 352 : Math.min(480, window.innerWidth - 48),
        onRange: (r) => ((range = r), page()),
        onList: list,
        onReport: (tab) => shell.toast(`Opens ${tab} (read-only).`),
      }),
    );
  const list = () => shell.open(stocksList(DEMO_STOCKS, () => page()));
  if (corp !== null) page();
  else list();
}
