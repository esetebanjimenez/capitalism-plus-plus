import "./shell.css";
import { SHEET_SHARE, SheetHeight, isDesktop, sheetPt } from "./layout";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export interface PanelSpec {
  /** What the panel is about, e.g. "tile:12,40" or "firm:3"; reopening the same key keeps height. */
  key: string;
  title: string;
  body: HTMLElement;
  /** Buttons along the bottom; the first is the main action. */
  actions?: HTMLElement[];
  height: SheetHeight;
  /** Heights the sheet may be dragged to (phone). */
  heights?: SheetHeight[];
}

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

export const button = (label: string, kind: "primary" | "secondary" | "danger" = "secondary", onClick?: () => void) => {
  const b = el("button", `btn ui-btn_${kind}`, label);
  b.dataset.kind = kind;
  if (onClick) b.onclick = onClick;
  return b;
};

/** A label / value row for panel bodies. */
export function rows(pairs: [string, string][]): HTMLElement {
  const dl = el("dl", "rows");
  for (const [k, v] of pairs) dl.append(el("dt", "", k), el("dd", "", v));
  return dl;
}

/**
 * The clear-map HUD and panel host: status pill (top left), menu button (bottom right),
 * toasts, and one panel at a time, a bottom sheet with peek/half/full on phones or a
 * 400 pt side panel on desktop (docs/m2-ux-spec.md, "Screen layout").
 */
export class Shell {
  readonly root = el("div", "shell");
  private readonly pill = el("div", "pill ui-card_float");
  private readonly date = el("span", "pill-date");
  private readonly cash = el("span", "pill-cash");
  private readonly speed = el("button", "pill-speed ui-btn_primary");
  private readonly menuBtn = el("button", "menu-btn ui-btn_secondary");
  private readonly badge = el("span", "badge ui-badge");
  private readonly toasts = el("div", "toasts");
  private readonly panel = el("section", "panel ui-card");
  private readonly handle = el("div", "handle-zone");
  private readonly head = el("header", "panel-head");
  private readonly titleEl = el("h2", "panel-title");
  private readonly bodyEl = el("div", "panel-body");
  private readonly actionsEl = el("footer", "panel-actions");
  private spec: PanelSpec | null = null;
  private height: SheetHeight = "peek";
  private paused = true;

  /** Called whenever a panel opens, closes or changes height (null = closed). */
  onLayout: (h: SheetHeight | null) => void = () => {};
  onMenu: () => void = () => {};
  onSpeed: () => void = () => {};

  constructor(parent: HTMLElement) {
    this.speed.setAttribute("aria-label", "Pause or resume");
    this.speed.append(el("span", "ui-icon_pause_on"));
    this.speed.onclick = () => this.onSpeed();
    this.pill.append(el("span", "ui-icon_cal"), this.date, el("span", "ui-icon_cash"), this.cash, this.speed);
    this.menuBtn.setAttribute("aria-label", "Menu");
    this.menuBtn.append(el("span", "ui-icon_menu"), this.badge);
    this.menuBtn.onclick = () => this.onMenu();
    this.setBadge(0);

    const close = el("button", "close");
    close.setAttribute("aria-label", "Close");
    close.append(el("span", "ui-icon_close"));
    close.onclick = () => this.close();
    this.handle.append(el("div", "ui-handle"));
    this.head.append(this.titleEl, close);
    this.panel.append(this.handle, this.head, this.bodyEl, this.actionsEl);
    this.panel.hidden = true;
    this.root.append(this.pill, this.menuBtn, this.toasts, this.panel);
    parent.append(this.root);

    this.dragSheet();
    window.addEventListener("keydown", (e) => e.key === "Escape" && this.close());
    window.addEventListener("resize", () => this.layout());
  }

  setStatus(year: number, month: number, day: number, cash: number, paused = this.paused): void {
    this.date.textContent = `${day} ${MONTHS[month - 1]} ${year}`;
    this.cash.textContent = `${cash < 0 ? "\u2212" : ""}$${Math.round(Math.abs(cash)).toLocaleString("en-US")}`;
    this.paused = paused;
    this.speed.firstElementChild!.className = paused ? "ui-icon_pause_on" : "ui-icon_play_on";
  }

  setBadge(n: number): void {
    this.badge.textContent = String(n);
    this.badge.hidden = n === 0;
  }

  toast(text: string): void {
    const t = el("div", "toast ui-card_float", text);
    this.toasts.append(t);
    setTimeout(() => t.remove(), 4000);
  }

  get current(): PanelSpec | null {
    return this.spec;
  }

  get openHeight(): SheetHeight | null {
    return this.spec ? this.height : null;
  }

  /** Open a panel, replacing whatever is open. */
  open(spec: PanelSpec): void {
    if (this.spec?.key !== spec.key) this.height = spec.height;
    this.spec = spec;
    this.titleEl.textContent = spec.title;
    this.bodyEl.replaceChildren(spec.body);
    this.actionsEl.replaceChildren(...(spec.actions ?? []));
    this.actionsEl.hidden = !spec.actions?.length;
    this.panel.hidden = false;
    this.layout();
  }

  close(): void {
    if (!this.spec) return;
    this.spec = null;
    this.panel.hidden = true;
    this.layout();
  }

  private layout(): void {
    const desktop = isDesktop(window.innerWidth);
    this.root.classList.toggle("desktop", desktop);
    this.root.classList.toggle("panel-open", !!this.spec);
    this.root.classList.toggle("sheet-full", !!this.spec && this.height === "full");
    if (this.spec) {
      const h = sheetPt(this.height, window.innerHeight);
      this.panel.style.height = desktop ? "" : `${h}px`;
      this.root.style.setProperty("--sheet-h", `${h}px`);
      this.panel.dataset.height = this.height;
    }
    this.onLayout(this.openHeight);
  }

  /** Phone: drag the handle to snap between the panel's heights; drag below peek to close. */
  private dragSheet(): void {
    let start: { y: number; h: number } | null = null;
    const zone = this.handle;
    zone.addEventListener("pointerdown", (e) => {
      if (isDesktop(window.innerWidth) || !this.spec) return;
      zone.setPointerCapture(e.pointerId);
      start = { y: e.clientY, h: this.panel.getBoundingClientRect().height };
    });
    zone.addEventListener("pointermove", (e) => {
      if (start) this.panel.style.height = `${Math.max(0, start.h - (e.clientY - start.y))}px`;
    });
    const end = (e: PointerEvent) => {
      if (!start || !this.spec) return;
      const h = start.h - (e.clientY - start.y);
      start = null;
      const allowed = this.spec.heights ?? [this.spec.height];
      const H = window.innerHeight;
      if (h < sheetPt("peek", H) * 0.6) return this.close();
      let best = allowed[0];
      for (const a of allowed) if (Math.abs(SHEET_SHARE[a] * H - h) < Math.abs(SHEET_SHARE[best] * H - h)) best = a;
      this.height = best;
      this.layout();
    };
    zone.addEventListener("pointerup", end);
    zone.addEventListener("pointercancel", end);
  }
}
