import {mkdirSync,lstatSync,readlinkSync,symlinkSync,realpathSync,unlinkSync} from 'node:fs';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {homedir} from 'node:os';

const source = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), '..'));
export function install(base, {uninstall = false} = {}) {
  base = resolve(base);
  const target = join(base, 'vyibc-character-design');
  let existing;
  try { existing = lstatSync(target); } catch(e) { if(e.code !== 'ENOENT') throw e; }
  if (existing && (!existing.isSymbolicLink() || resolve(dirname(target),readlinkSync(target)) !== source)) throw Error('Existing skill has different ownership; nothing changed');
  if (uninstall) {
    if (existing) unlinkSync(target);
    return {target, changed: !!existing, operation: 'uninstall-link-only'};
  }
  if (!existing) { mkdirSync(base,{recursive:true}); symlinkSync(source,target,'dir'); }
  return {target, changed: !existing, operation: 'install'};
}
if(process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const args = process.argv.slice(2);
    const uninstall = args[0] === '--uninstall';
    if (uninstall) args.shift();
    if (args.length > 1 || args.some(a=>a.startsWith('--'))) throw Error('Usage: node install.mjs [--uninstall] [skills-directory]');
    console.log(JSON.stringify(install(args[0] || join(process.env.CODEX_HOME || join(homedir(),'.codex'),'skills'),{uninstall})));
  } catch(e) { console.error(e.message); process.exitCode=1; }
}
