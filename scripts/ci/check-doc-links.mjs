import fs from "fs";
import path from "path";

const ROOT = process.cwd();
const DOCS_DIR = path.join(ROOT, "docs");
const README = path.join(ROOT, "README.md");
const IGNORE_PREFIXES = ["http://", "https://", "mailto:", "#"];

function walkMarkdownFiles(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const fullPath = path.join(dir, name);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      walkMarkdownFiles(fullPath, out);
      continue;
    }
    if (name.endsWith(".md")) {
      out.push(fullPath);
    }
  }
  return out;
}

function extractLinks(markdown) {
  const links = [];
  const regex = /\[[^\]]+\]\(([^)]+)\)/g;
  let match;
  while ((match = regex.exec(markdown)) !== null) {
    links.push(match[1].trim());
  }
  return links;
}

function normalizeTarget(filePath, linkTarget) {
  const clean = linkTarget.split("#")[0];
  if (!clean) {
    return null;
  }
  return path.resolve(path.dirname(filePath), clean);
}

const markdownFiles = [README, ...walkMarkdownFiles(DOCS_DIR)];
const errors = [];

for (const file of markdownFiles) {
  const content = fs.readFileSync(file, "utf8");
  const links = extractLinks(content);
  for (const link of links) {
    if (IGNORE_PREFIXES.some((prefix) => link.startsWith(prefix))) {
      continue;
    }
    const targetPath = normalizeTarget(file, link);
    if (!targetPath) {
      continue;
    }
    if (!fs.existsSync(targetPath)) {
      errors.push(`${path.relative(ROOT, file)} -> missing: ${link}`);
    }
  }
}

if (errors.length) {
  console.error("Markdown link check failed:");
  for (const err of errors) {
    console.error(`- ${err}`);
  }
  process.exit(1);
}

console.log(`Markdown link check passed (${markdownFiles.length} files).`);

