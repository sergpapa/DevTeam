#!/bin/sh
set -e
mkdir -p src
printf '{ "name": "orders-api", "version": "1.3.0", "type": "module", "dependencies": { "express": "^4.19.0" } }\n' > package.json
cat > src/server.js <<'JS'
import express from "express";
import { orders } from "./store.js";
const app = express();
app.use(express.json());
app.get("/orders", (req, res) => res.json(orders));
app.post("/orders", (req, res) => { const o = { id: orders.length + 1, ...req.body }; orders.push(o); res.status(201).json(o); });
app.get("/orders/:id", (req, res) => { const o = orders.find(x => x.id == req.params.id); o ? res.json(o) : res.status(404).end(); });
app.listen(3000);
JS
printf 'export const orders = [];\n' > src/store.js
git init -q . && git add -A && git -c user.email=e@x -c user.name=eval commit -q -m init
