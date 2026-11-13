import "./shell.css";

/** Full-screen loading screen with progress while the worker boots Pyodide and the sim. */
export class LoadingOverlay {
  private readonly root = document.createElement("div");
  private readonly text = document.createElement("div");
  private readonly fill = document.createElement("div");

  constructor(parent: HTMLElement = document.body) {
    this.root.className = "sim-overlay";
    const box = document.createElement("div");
    box.className = "box";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.append(this.fill);
    box.append(this.text, bar);
    this.root.append(box);
    this.set("Starting the sim", 0, 1);
    parent.append(this.root);
  }

  set(stage: string, done: number, total: number): void {
    this.text.textContent = `${stage}\u2026`;
    this.fill.style.width = `${Math.round((100 * done) / Math.max(1, total))}%`;
  }

  remove(): void {
    this.root.remove();
  }
}

/** Shows a Python traceback from the worker over everything; the sim has stopped. */
export function showSimError(message: string, traceback: string, parent: HTMLElement = document.body): HTMLElement {
  const root = document.createElement("div");
  root.className = "sim-overlay sim-error";
  const box = document.createElement("div");
  box.className = "box";
  const h = document.createElement("h2");
  h.textContent = "The sim stopped with an error";
  const p = document.createElement("p");
  p.textContent = message;
  const pre = document.createElement("pre");
  pre.textContent = traceback;
  box.append(h, p, pre);
  root.append(box);
  parent.append(root);
  return root;
}
