#!/usr/bin/env node
/**
 * HyperFormula (v3.5.0) Headless Formula Evaluator & Validator for /xlsx Skill
 * 支援自動尋找全域 ~/.gemini/config/skills/xlsx/node_modules，並支援 --file 讀取 JSON。
 * Usage:
 *   node scripts/hyperformula_eval.js '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)"]]}'
 *   node scripts/hyperformula_eval.js --file payload.json
 */

const fs = require("fs");
const os = require("os");
const path = require("path");

module.paths.push(path.resolve(os.homedir(), ".gemini", "config", "skills", "xlsx", "node_modules"));
const { HyperFormula } = require("hyperformula");

function evaluateSheets(sheetsJson) {
  const data = JSON.parse(String(sheetsJson).replace(/^\uFEFF/, ""));
  const hf = HyperFormula.buildFromSheets(data, {
    licenseKey: "gpl-v3",
  });

  const output = {};
  for (const sheetName of hf.getSheetNames()) {
    const sheetId = hf.getSheetId(sheetName);
    output[sheetName] = hf.getSheetValues(sheetId);
  }

  return {
    engine: `handsontable/hyperformula v${HyperFormula.version}`,
    supported_functions_count: HyperFormula.getRegisteredFunctionNames("enGB").length,
    values: output,
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
  console.log(JSON.stringify(evaluateSheets(rawJson), null, 2));
}
