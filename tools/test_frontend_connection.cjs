const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, '..');
const app = fs.readFileSync(path.join(root, 'static/app.js'), 'utf8');
const events = fs.readFileSync(path.join(root, 'static/events.js'), 'utf8');
const network = app.slice(app.indexOf('const connectionMessage='), app.indexOf("const modal=$('#modal')"));
const startup = events.slice(events.indexOf('async function start()'), events.indexOf('setInterval('));
let auth, warning, loaded;
const context = vm.createContext({
  AbortSignal, state: {me: null}, location: {pathname: '/'},
  fetch: async () => new Response('The page could not be found', {status:404}),
  showAuth: setup => {auth=setup;},
  $: () => ({insertAdjacentHTML: (_, html) => {warning=html;}}),
  notice: text => text, esc: text => text,
  loadAccount: async () => {loaded=true;}
});
vm.runInContext(network + '\n' + startup, context);
const run = expression => vm.runInContext(expression, context);
const json = (data, status=200) => new Response(JSON.stringify(data), {status, headers:{'Content-Type':'application/json'}});
(async () => {
  await run('start()');
  assert.equal(auth, false);
  assert.match(warning, /serviço está temporariamente indisponível/);
  assert.doesNotMatch(warning, /Unexpected token|The page/);
  await assert.rejects(run("api('/login','POST',{})"), /serviço está temporariamente indisponível/);
  await assert.rejects(run("download('/report')"), /serviço está temporariamente indisponível/);
  context.fetch = async () => new Response('{broken', {headers:{'Content-Type':'application/json'}});
  await assert.rejects(run("api('/status')"), /serviço está temporariamente indisponível/);
  context.fetch = async () => {throw new TypeError('Failed to fetch');};
  await assert.rejects(run("api('/status')"), /serviço está temporariamente indisponível/);
  context.fetch = async () => json({error:'Credenciais inválidas.'},401);
  await assert.rejects(run("api('/login','POST',{})"), /Credenciais inválidas/);
  context.fetch = async () => json({setup_required:true});
  await run('start()');
  assert.equal(auth,true);
  context.fetch = async () => json({setup_required:false});
  await run('start()');
  assert.equal(loaded,true);
  console.log('OK: login sem API, erro HTML, download, JSON inválido, falha de rede, credenciais, setup e inicialização conectada.');
})().catch(error => {console.error(error);process.exitCode=1;});
