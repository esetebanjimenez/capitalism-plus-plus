/** ?chart=demo: the three #178 sample charts, for screenshots next to docs/art/m2-views-preview.png. */
import { loadUiAtlas } from "./atlas";
import { ChartPoint, lineChart } from "./chart";

const MONTHS = "JFMAMJJASOND".split("");
export const DEMO_PROFIT: ChartPoint[] = [-420e3, -310e3, -150e3, -60e3, 40e3, 210e3, 190e3, 420e3, 650e3, 820e3, 1.08e6, 1.2e6].map(
  (value, i) => ({ label: MONTHS[i], value }),
);
export const DEMO_PRICE: ChartPoint[] = [18.2, 18.6, 18.4, 19.1, 19.0, 19.7, 20.3].map((value, i) => ({ label: String(9 + i), value }));
export const DEMO_SINGLE: ChartPoint[] = [{ label: "Jan", value: 12.5e6 }];

export async function showChartDemo(resolution: number): Promise<void> {
  await loadUiAtlas(resolution);
  const box = document.createElement("div");
  box.style.cssText = "position:fixed;inset:0;display:flex;flex-wrap:wrap;gap:16px;align-content:flex-start;padding:16px;background:#2e3440;overflow:auto";
  box.append(
    lineChart(DEMO_PROFIT, { title: "Operating profit, past 12 months", width: 470, height: 190 }),
    lineChart(DEMO_SINGLE, { title: "Net worth, first month", width: 240, height: 190 }),
    lineChart(DEMO_PRICE, { title: "Share price, day", width: 240, height: 190 }),
  );
  document.body.append(box);
  // Show the tip on the April point, as in the preview.
  const card = box.firstElementChild as HTMLElement;
  const r = card.getBoundingClientRect();
  const x = r.left + 40 + (3 / 11) * (470 - 54) ;
  card.dispatchEvent(new PointerEvent("pointerdown", { clientX: x, clientY: r.top + 100, pointerType: "touch" }));
}
