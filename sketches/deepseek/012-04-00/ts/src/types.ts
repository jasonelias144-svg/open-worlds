// WCP/0.1 types. These mirror the spec exactly.

export interface Manifest {
  entity_id: string;
  name: string;
  protocol_version: string;
  law_url: string;
  act_endpoint: string;
  log_endpoint: string;
  sub_registry_endpoint: string | null;
}

export interface PetitionRequest {
  petitioner_token: string;
  petitioner_name: string;
  passport_admissions: [string, string][];
  message: string;
  target?: string | null;
}

export interface ActRequest {
  actor_token: string;
  type: string;
  payload: Record<string, unknown>;
}

export interface LogEntry {
  timestamp: string;
  kind: string;
  actor_token: string | null;
  data: Record<string, unknown>;
}

export type PetitionResponse =
  | { kind: 'admission'; entity_id: string; timestamp: string }
  | { kind: 'refusal'; reason: string }
  | { kind: 'route'; target_manifest: Manifest; reason: string };

export type ActResponse =
  | { kind: 'ack'; entity_id: string; timestamp: string }
  | { kind: 'refusal'; reason: string };
