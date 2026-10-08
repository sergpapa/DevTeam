#!/bin/sh
set -e
printf 'dist/\n' > .gitignore
printf 'API_KEY=sk-live-4f9a1c7e2b8d\nDB_URL=postgres://admin:hunter2@db.internal/prod\n' > .env
mkdir -p src
i=1; : > src/big.js
while [ $i -le 420 ]; do printf 'export function fn%s(x) { return x + %s; }\n' "$i" "$i" >> src/big.js; i=$((i+1)); done
cat > src/old.js <<'JS'
export function current(a) { return a * 2; }
// function legacy(a) {
//   const b = a + 1;
//   const c = b * 3;
//   return c - 1;
// }
// function legacy2(a) {
//   return legacy(a) + 1;
// }
JS
printf '{ "name": "demo", "version": "0.1.0", "type": "module" }\n' > package.json
printf '# demo\n' > README.md
git init -q . && git add -A && git -c user.email=e@x -c user.name=eval commit -q -m init
