import { MultiverseRegistry } from './registry.js';
import { createServer } from './server.js';

const port = parseInt(process.env.PORT ?? '9000');
const entityId = process.env.ENTITY_ID ?? 'multiverse:ts';
const name = process.env.NAME ?? 'TypeScript Multiverse';
const conformanceCmd = process.env.CONFORMANCE_CMD?.split(' ');

const registry = new MultiverseRegistry({
  entity_id: entityId,
  name,
  conformance_command: conformanceCmd,
});

createServer(registry).listen(port, () => {
  console.log(`TypeScript Multiverse at http://localhost:${port}`);
  console.log(`  manifest:   http://localhost:${port}/manifest`);
  console.log(`  log:        http://localhost:${port}/log`);
  console.log(`  sub-entities: http://localhost:${port}/sub_entities`);
});
