// Real end-to-end check: drives the actual UI in Chromium against the
// actually-running backend — login form, question submit, grounded answer
// with sources, refusal badge for an off-topic question. Also captures the
// README screenshots. Not part of the pytest suite (it needs both servers
// and a live Groq call); run manually:
//   $env:E2E_USER="..." ; $env:E2E_PASS="..." ; node e2e-check.mjs

import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const UI = process.env.E2E_URL || "http://127.0.0.1:5173";
const user = process.env.E2E_USER;
const pass = process.env.E2E_PASS;
if (!user || !pass) throw new Error("Set E2E_USER and E2E_PASS");

mkdirSync("screenshots", { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 900, height: 900 } });

await page.goto(UI);
await page.fill('input[autocomplete="username"]', user);
await page.fill('input[type="password"]', pass);
await page.screenshot({ path: "screenshots/login.png" });
await page.click('button[type="submit"]');
await page.waitForSelector(".ask-bar input", { timeout: 15000 });
console.log("LOGIN: ok (chat visible)");

await page.fill(".ask-bar input", "What was the BigQuery bytes-scanned reduction?");
await page.click(".ask-bar button");
await page.waitForSelector(".bubble.answer.grounded", { timeout: 90000 });
const answer = await page.textContent(".bubble.answer.grounded p");
console.log("ANSWER:", answer.slice(0, 160));
if (!answer.includes("58.7")) throw new Error("Answer missing the documented 58.7% figure");
console.log("BADGE:", await page.textContent(".badge-grounded"));
const sources = await page.$$eval(".sources li .citation", (els) =>
  els.map((e) => e.textContent)
);
console.log("SOURCES:", sources.join(" | "));
if (sources.length === 0) throw new Error("No sources displayed");

await page.fill(".ask-bar input", "What is the capital of France?");
await page.click(".ask-bar button");
await page.waitForSelector(".bubble.answer.refused", { timeout: 30000 });
console.log("REFUSAL BADGE:", await page.textContent(".badge-refused"));

await page.screenshot({ path: "screenshots/chat.png", fullPage: true });
await browser.close();
console.log("E2E PASS — real UI round-trip verified");
