const fs = require('node:fs');
const { looksBin, readLooks } = require('../looklab/app.js');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
try {
  const result = request.read ? readLooks(Buffer.from(request.read, 'hex')) : Buffer.from(looksBin(request.films)).toString('hex');
  process.stdout.write(JSON.stringify({ result }));
} catch (e) { process.stdout.write(JSON.stringify({ error: e.message })); }
