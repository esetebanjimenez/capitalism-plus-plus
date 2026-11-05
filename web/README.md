# Pyodide smoke test

Checks that the sim package (code plus `capitalism.db`) loads under Pyodide
and advances a few days of the bread chain without error. Smoke only.

```bash
python scripts/pyodide_bundle.py      # writes web/capitalism.zip
npm install --prefix web              # pinned pyodide from web/package.json
node web/smoke.mjs                    # prints PASS …
```

In a browser, serve `web/` and open the bare page:

```bash
python -m http.server -d web 8000     # then open http://localhost:8000/
```

The page shows `PASS …` and sets the tab title to `PASS` (or `FAIL`).
`pytest` runs the node check too when `node` and `web/node_modules/pyodide`
are present, and skips it otherwise. CI runs it in the `pyodide-smoke` job.
