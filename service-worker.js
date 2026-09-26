const CACHE='catfood-compass-v0.3.5';
const ASSETS=['./','./index.html','./styles.css','./app.js','./data/foods.js','./data/tiki_cat.js','./data/fancy_feast.js','./data/friskies.js','./data/recall_brands.js','./data/recall_brands.json','./data/recalls.js','./data/recalls.json','./data/aliases.js','./data/manufacturer_nutrition.js','./data/manufacturer_nutrition.json','./manifest.webmanifest','./icon.svg'];

self.addEventListener('install',e=>e.waitUntil(
  caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())
));

self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));

self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  const url=new URL(e.request.url);
  const isRecallSnapshot=/\/data\/(?:recalls|recall_brands)\.(?:js|json)$/.test(url.pathname);

  // Recall snapshots and their catalog-brand whitelist can change independently
  // of application releases. Use network-first so an installed/offline-capable
  // GitHub Pages app sees GitHub Action updates while retaining the last good
  // copy when offline.
  if(isRecallSnapshot){
    e.respondWith(
      fetch(e.request).then(resp=>{
        const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put(e.request,copy));
        return resp;
      }).catch(()=>caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(r=>r||fetch(e.request).then(resp=>{
      const copy=resp.clone();
      caches.open(CACHE).then(c=>c.put(e.request,copy));
      return resp;
    }).catch(()=>caches.match('./index.html')))
  );
});
