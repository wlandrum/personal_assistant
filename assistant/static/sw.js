const CACHE = "assistant-v1";
const SHELL = ["/", "/style.css", "/app.js", "/manifest.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/message") || url.pathname.startsWith("/voice")) return;
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
