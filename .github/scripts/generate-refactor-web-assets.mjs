/**
 * Temporary CI-only stand-ins for missing imported Refactor web images.
 * Not original/credited imagery: replace with the original manifest assets
 * before distributing the app.
 */
import fs from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
// Resolve sharp from the extracted project's node_modules, not this script's folder.
const requireFromProject = createRequire(pathToFileURL(process.cwd() + "/package.json"));
const sharp = requireFromProject("sharp");

const photos = {
  "dawn.jpg": ["#241b3a", "#7a4a6e", "#d79bb0"],
  "noon.jpg": ["#4f93d6", "#9cc8ef", "#dcefff"],
  "asr.jpg": ["#9c6a24", "#c89238", "#f0cf8e"],
  "maghrib.jpg": ["#2c0f1e", "#7e2f3a", "#e0703a"],
  "night.jpg": ["#04060f", "#0b1430", "#16235a"],
  "snow.jpg": ["#b9d2e6", "#dcebf6", "#ffffff"],
  "autumn-tree.jpg": ["#5e2f17", "#9c4f22", "#e3a23a"],
};
const decor = {
  maple:"#c0492b", fallen:"#a85a2a", wind:"#8fb6d6", snow:"#ffffff",
  star:"#ffe27a", sparkle:"#fff0a8", crescent:"#ffe9a8", blossom:"#f7b6d2",
  tulip:"#e26d8a", wave:"#7fc4d6", balloon:"#e26d8a", confetti:"#7ad1a0",
  heart:"#e85d75", lotus:"#f2a9c4", dove:"#dfe7ef", herb:"#6fae5a",
  snowman:"#eaf2f8", gift:"#e07a5f", books:"#9b6bd6",
};
const gradient = (w,h,[a,b,c]) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${a}"/><stop offset="55%" stop-color="${b}"/><stop offset="100%" stop-color="${c}"/></linearGradient></defs><rect width="100%" height="100%" fill="url(#g)"/><circle cx="${w*.7}" cy="${h*.32}" r="${h*.13}" fill="#fff" opacity=".18"/></svg>`;
const circle = (c) => `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><defs><radialGradient id="r"><stop stop-color="${c}"/><stop offset="1" stop-color="${c}" stop-opacity=".65"/></radialGradient></defs><circle cx="32" cy="30" r="20" fill="url(#r)" stroke="#fff" stroke-opacity=".25" stroke-width="2"/></svg>`;

fs.mkdirSync("src/assets/photos",{recursive:true});
fs.mkdirSync("src/assets/decor",{recursive:true});
fs.mkdirSync("src/assets/art",{recursive:true});
const made=[];
for (const [name, colors] of Object.entries(photos)) {
  const path = `src/assets/photos/${name}`;
  if (!fs.existsSync(path)) {
    await sharp(Buffer.from(gradient(1200,800,colors))).jpeg({quality:82}).toFile(path);
    made.push(path);
  }
}
for (const [name,color] of Object.entries(decor)) {
  const path = `src/assets/decor/${name}.png`;
  if (!fs.existsSync(path)) {
    await sharp(Buffer.from(circle(color))).png().toFile(path);
    made.push(path);
  }
}
for (const [name,colors] of [
  ["cairo-night.jpg",["#05060f","#0b1430","#1b2a5a"]],
  ["fanous.jpg",["#1a0a2a","#4a1d52","#c9542e"]],
]) {
  const path = `src/assets/art/${name}`;
  if (!fs.existsSync(path)) {
    await sharp(Buffer.from(gradient(1000,700,colors))).jpeg({quality:82}).toFile(path);
    made.push(path);
  }
}
const notice = `# CI-only generated image fallbacks

${made.length} missing image files were generated as simple gradients/circles solely to make the Refactor web source resolvable for CI. They are NOT the original photographs or licensed decorative artwork listed in docs/reference/assets-manifest.json. Replace them with the original assets before a production release.

Generated:
${made.map(x=>"- "+x).join("\n")}
`;
fs.writeFileSync("CI_ASSET_FALLBACK_NOTICE.md",notice);
fs.writeFileSync("public/ci-asset-fallbacks.json",JSON.stringify({kind:"temporary-ci-fallbacks",generated:made},null,2));
console.log(`Generated ${made.length} CI-only image fallbacks; see CI_ASSET_FALLBACK_NOTICE.md.`);
