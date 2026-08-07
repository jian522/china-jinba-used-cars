const fs = require("fs");
const root = "C:/Users/25394/Documents/金霸二手车网站";
const carFiles = fs.readdirSync(root + "/cars").filter(f => f.endsWith(".html")).sort();
let sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.99">\n';
const mains = [
  ["https://jinbacars.com/", "1.00", "weekly"],
  ["https://jinbacars.com/cars.html", "0.90", "daily"],
  ["https://jinbacars.com/about.html", "0.70", "monthly"],
  ["https://jinbacars.com/services.html", "0.80", "monthly"],
  ["https://jinbacars.com/contact.html", "0.70", "monthly"]
];
for (const m of mains) {
  sm += "  <url>\n    <loc>" + m[0] + "</loc>\n    <lastmod>2026-07-14</lastmod>\n    <changefreq>" + m[2] + "</changefreq>\n    <priority>" + m[1] + "</priority>\n  </url>\n";
}
for (const f of carFiles) {
  const n = f.replace(".html", "");
  sm += "  <url>\n    <loc>https://jinbacars.com/cars/" + n + ".html</loc>\n    <lastmod>2026-07-14</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.60</priority>\n  </url>\n";
}
sm += "</urlset>";
fs.writeFileSync(root + "/sitemap.xml", sm, "utf8");
console.log("Sitemap: " + (5 + carFiles.length) + " URLs");
