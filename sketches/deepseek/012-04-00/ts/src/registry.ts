import { execFile } from 'child_process';
import * as http from 'http';
import {
  Manifest, PetitionRequest, ActRequest, LogEntry,
  PetitionResponse, ActResponse,
} from './types.js';

export interface MultiverseConfig {
  entity_id: string;
  name: string;
  conformance_command?: string[]; // defaults to ["python", "-m", "wcp_conformance"]
}

export class MultiverseRegistry {
  private manifest: Manifest;
  private log: LogEntry[] = [];
  private registry: Map<string, Manifest> = new Map();
  private admitted: Map<string, { timestamp: string }> = new Map();
  private conformanceCommand: string[];

  constructor(config: MultiverseConfig) {
    this.manifest = {
      entity_id: config.entity_id,
      name: config.name,
      protocol_version: 'WCP/0.1',
      law_url: `multiverse://${config.entity_id}/law`,
      act_endpoint: `multiverse://${config.entity_id}/act`,
      log_endpoint: `multiverse://${config.entity_id}/log`,
      sub_registry_endpoint: `multiverse://${config.entity_id}/worlds`,
    };
    this.conformanceCommand = config.conformance_command
      ?? ['python', '-m', 'wcp_conformance'];
  }

  getManifest(): Manifest { return { ...this.manifest }; }

  petition(req: PetitionRequest): PetitionResponse {
    const ts = new Date().toISOString();
    if (this.admitted.has(req.petitioner_token)) {
      const r: PetitionResponse = { kind: 'refusal', reason: 'Already admitted' };
      this.log.push({ timestamp: ts, kind: 'petition_refused',
                      actor_token: req.petitioner_token,
                      data: { reason: r.reason } });
      return r;
    }
    this.admitted.set(req.petitioner_token, { timestamp: ts });
    this.log.push({ timestamp: ts, kind: 'admission',
                    actor_token: req.petitioner_token,
                    data: { name: req.petitioner_name } });
    return { kind: 'admission', entity_id: this.manifest.entity_id,
             timestamp: ts };
  }

  async act(req: ActRequest): Promise<ActResponse> {
    const ts = new Date().toISOString();
    if (!this.admitted.has(req.actor_token)) {
      const r: ActResponse = { kind: 'refusal', reason: 'Actor is not admitted' };
      this.log.push({ timestamp: ts, kind: 'act_refused',
                      actor_token: req.actor_token,
                      data: { reason: r.reason } });
      return r;
    }
    if (req.type === 'multiverse.admit') {
      return this.handleAdmit(ts, req);
    }
    if (req.type === 'multiverse.remove') {
      return this.handleRemove(ts, req);
    }
    const r: ActResponse = { kind: 'refusal',
                             reason: `Unknown act type: ${req.type}` };
    this.log.push({ timestamp: ts, kind: 'act_refused',
                    actor_token: req.actor_token,
                    data: { reason: r.reason } });
    return r;
  }

  private async handleAdmit(ts: string, req: ActRequest): Promise<ActResponse> {
    const entityUrl = req.payload.entity_url as string | undefined;
    if (!entityUrl) {
      return { kind: 'refusal', reason: 'No entity_url in payload' };
    }
    let manifest: Manifest;
    try {
      manifest = await this.fetchManifest(entityUrl);
    } catch (e: unknown) {
      return { kind: 'refusal',
               reason: `Could not fetch manifest: ${(e as Error).message}` };
    }
    if (this.registry.has(manifest.entity_id)) {
      return { kind: 'refusal',
               reason: `Entity ${manifest.entity_id} already listed` };
    }
    const conformance = await this.runConformance(entityUrl);
    if (!conformance.passed) {
      this.log.push({ timestamp: ts, kind: 'entity_admit_refused',
                      actor_token: req.actor_token,
                      data: { entity_id: manifest.entity_id,
                              url: entityUrl,
                              failures: conformance.failures } });
      return { kind: 'refusal',
               reason: `Entity ${manifest.entity_id} fails conformance` };
    }
    this.registry.set(manifest.entity_id, manifest);
    this.log.push({ timestamp: ts, kind: 'entity_admitted',
                    actor_token: req.actor_token,
                    data: { entity_id: manifest.entity_id,
                            url: entityUrl, manifest } });
    return { kind: 'ack', entity_id: this.manifest.entity_id, timestamp: ts };
  }

  private handleRemove(ts: string, req: ActRequest): ActResponse {
    const entityId = req.payload.entity_id as string | undefined;
    if (!entityId) {
      return { kind: 'refusal', reason: 'No entity_id in payload' };
    }
    if (!this.registry.has(entityId)) {
      return { kind: 'refusal',
               reason: `Entity ${entityId} not in registry` };
    }
    this.registry.delete(entityId);
    this.log.push({ timestamp: ts, kind: 'entity_removed',
                    actor_token: req.actor_token,
                    data: { entity_id: entityId } });
    return { kind: 'ack', entity_id: this.manifest.entity_id, timestamp: ts };
  }

  private fetchManifest(entityUrl: string): Promise<Manifest> {
    const url = `${entityUrl.replace(/\/$/, '')}/manifest`;
    return new Promise((resolve, reject) => {
      http.get(url, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(data) as Manifest); }
          catch (e) { reject(e); }
        });
      }).on('error', reject);
    });
  }

  private runConformance(entityUrl: string): Promise<{ passed: boolean; failures: string[] }> {
    const [cmd, ...args] = this.conformanceCommand;
    return new Promise((resolve) => {
      execFile(cmd, [...args, '--url', entityUrl, '--quiet'],
               { timeout: 30_000 },
               (err, stdout, stderr) => {
        if (err) {
          resolve({ passed: false,
                    failures: [stdout || stderr || err.message] });
        } else {
          resolve({ passed: true, failures: [] });
        }
      });
    });
  }

  logSince(since?: string | null): LogEntry[] {
    if (!since) return [...this.log];
    return this.log.filter(e => e.timestamp > since);
  }

  listSubEntities(): Manifest[] {
    return Array.from(this.registry.values());
  }
}
