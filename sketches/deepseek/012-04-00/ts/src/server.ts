import * as http from 'http';
import { MultiverseRegistry } from './registry.js';

export function createServer(registry: MultiverseRegistry): http.Server {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url ?? '/', `http://${req.headers.host}`);
    const path = url.pathname;

    const send = (status: number, payload: unknown) => {
      const body = JSON.stringify(payload);
      res.writeHead(status, {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      });
      res.end(body);
    };

    try {
      if (req.method === 'GET' && path === '/manifest') {
        return send(200, registry.getManifest());
      }
      if (req.method === 'GET' && path === '/log') {
        const since = url.searchParams.get('since');
        return send(200, { entries: registry.logSince(since) });
      }
      if (req.method === 'GET' && path === '/sub_entities') {
        return send(200, { entities: registry.listSubEntities() });
      }
      if (req.method === 'POST' && path === '/petition') {
        const body = await readJson(req);
        return send(200, registry.petition(body));
      }
      if (req.method === 'POST' && path === '/act') {
        const body = await readJson(req);
        return send(200, await registry.act(body));
      }
      return send(404, { error: 'not found' });
    } catch (e: unknown) {
      return send(500, { error: (e as Error).message ?? String(e) });
    }
  });
}

function readJson(req: http.IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => data += chunk);
    req.on('end', () => {
      try { resolve(JSON.parse(data || '{}')); }
      catch (e) { reject(e); }
    });
    req.on('error', reject);
  });
}
