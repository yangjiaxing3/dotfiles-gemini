#!/usr/bin/env node
/**
 * HyperFormula (v3.5.0) Headless Formula Evaluator & Validator for /xlsx Skill
 * Supports ~400 native Excel functions, array arithmetic, and instant syntax checking.
 * Usage:
 *   node scripts/hyperformula_eval.js '{"Sheet1": [["100", "200", "=SUM(A1:B1)"]]}'
 */

const { HyperFormula } = require("hyperformula");

function evaluateSheets(sheetsJson) {
  const data = JSON.parse(sheetsJson);
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
  const arg = process.argv[2] || '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)", "=A1-B1", "=B1+C1"]]}';
  console.log(JSON.stringify(evaluateSheets(arg), null, 2));
}
