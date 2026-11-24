#!/usr/bin/env node
/**
 * IronCalc (@ironcalc/wasm v0.9.1) Headless Rust/WASM Evaluator for /xlsx Skill
 * Usage:
 *   node scripts/ironcalc_eval.js '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)"]]}'
 *   node scripts/ironcalc_eval.js --file payload.json
 */

const fs = require("fs");
const os = require("os");
const path = require("path");

const wasmPkgDir = path.resolve(os.homedir(), ".gemini", "config", "skills", "xlsx", "node_modules", "@ironcalc", "wasm");
const ic = require(path.join(wasmPkgDir, "wasm.js"));
const wasmBytes = fs.readFileSync(path.join(wasmPkgDir, "wasm_bg.wasm"));
ic.initSync({ module: wasmBytes });

function evaluateWithIronCalc(sheetsJson) {
  const data = JSON.parse(String(sheetsJson).replace(/^\uFEFF/, ""));
  const sheetNames = Object.keys(data);
  const model = new ic.Model("workbook", "en", "UTC", "en");

  sheetNames.forEach((sname, idx) => {
    if (idx > 0) {
      model.newSheet();
    }
    model.renameSheet(idx, sname);
    const grid = data[sname] || [];
    grid.forEach((rowArr, rIdx) => {
      (rowArr || []).forEach((cellVal, cIdx) => {
        if (cellVal !== null && cellVal !== undefined && cellVal !== "") {
          model.setUserInput(idx, rIdx + 1, cIdx + 1, String(cellVal));
        }
      });
    });
  });

  model.evaluate();

  const values = {};
  sheetNames.forEach((sname, idx) => {
    const grid = data[sname] || [];
    values[sname] = grid.map((rowArr, rIdx) =>
      (rowArr || []).map((_, cIdx) => model.getFormattedCellValue(idx, rIdx + 1, cIdx + 1))
    );
  });

  return {
    engine: "ironcalc/IronCalc (@ironcalc/wasm v0.9.1)",
    values,
  };
}

if (require.main === module) {
  let rawJson = '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)", "=A1-B1", "=B1+C1"]]}';
  const args = process.argv.slice(2);
  if (args[0] === "--file" && args[1]) {
    rawJson = fs.readFileSync(args[1], "utf8");
  } else if (args[0]) {
    rawJson = args[0];
  }
  console.log(JSON.stringify(evaluateWithIronCalc(rawJson), null, 2));
}
