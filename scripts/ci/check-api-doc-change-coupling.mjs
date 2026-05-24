import { execSync } from "child_process";

function getChangedFiles() {
  const baseSha = process.env.BASE_SHA;
  const headSha = process.env.HEAD_SHA || "HEAD";

  if (!baseSha) {
    console.log("BASE_SHA is not set. Skipping API-doc coupling check.");
    return [];
  }

  const trackedOutput = execSync(`git diff --name-only ${baseSha}..${headSha}`, {
    encoding: "utf8",
  });
  const tracked = trackedOutput
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const untrackedOutput = execSync("git ls-files --others --exclude-standard", {
    encoding: "utf8",
  });
  const untracked = untrackedOutput
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return [...new Set([...tracked, ...untracked])];
}

const changedFiles = getChangedFiles();
if (!changedFiles.length) {
  process.exit(0);
}

const routeChanged = changedFiles.some((f) => f.startsWith("backend/api/routes/") && f.endsWith(".ts"));
if (!routeChanged) {
  console.log("No route module changes detected. Coupling check passed.");
  process.exit(0);
}

const apiDocsChanged = changedFiles.some((f) => f.startsWith("docs/API/"));
if (!apiDocsChanged) {
  console.error("Route changes detected without docs/API updates.");
  console.error("Changed route files:");
  for (const file of changedFiles.filter((f) => f.startsWith("backend/api/routes/") && f.endsWith(".ts"))) {
    console.error(`- ${file}`);
  }
  process.exit(1);
}

console.log("API route/doc coupling check passed.");
