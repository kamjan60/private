"use strict";
/** Runs every *.test.js in this directory and fails the process if any did. */

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const dir = __dirname;
const files = fs.readdirSync(dir).filter((f) => f.endsWith(".test.js")).sort();

let failed = 0;
for (const f of files) {
  console.log(`\n=== ${f} ===`);
  try {
    execFileSync(process.execPath, [path.join(dir, f)], { stdio: "inherit" });
  } catch {
    failed++;
  }
}

console.log(failed ? `\n${failed} of ${files.length} files failed` : `\nall ${files.length} files passed`);
process.exit(failed ? 1 : 0);
