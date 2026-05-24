import fs from "fs";
import path from "path";

const ROOT = process.cwd();
const ROUTES_DIR = path.join(ROOT, "backend", "api", "routes");
const ROUTE_DOCS_DIR = path.join(ROOT, "docs", "API", "routes");

function listTsRouteBases(dir) {
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith(".ts"))
    .map((name) => name.replace(/\.ts$/, ""))
    .sort();
}

function listMdRouteBases(dir) {
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith(".md"))
    .map((name) => name.replace(/\.md$/, ""))
    .sort();
}

const routeBases = listTsRouteBases(ROUTES_DIR);
const docBases = new Set(listMdRouteBases(ROUTE_DOCS_DIR));
const missing = routeBases.filter((base) => !docBases.has(base));

if (missing.length) {
  console.error("API route documentation coverage failed.");
  console.error("Missing docs for route modules:");
  for (const item of missing) {
    console.error(`- backend/api/routes/${item}.ts -> docs/API/routes/${item}.md`);
  }
  process.exit(1);
}

console.log(`API route documentation coverage passed (${routeBases.length} route modules).`);

