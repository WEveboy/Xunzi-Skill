// 最小探针：对一个已解压的 dsh 插件目录做注册烟测。
// 用法： node scripts/probe_plugin.mjs <插件根目录>
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.argv[2];
if (!root) {
  console.error('usage: node scripts/probe_plugin.mjs <plugin-root>');
  process.exit(2);
}

const plugin = await import(pathToFileURL(join(root, 'index.mjs')).href);
assert.equal(typeof plugin.apply, 'function', 'apply 必须是函数');
assert.deepEqual(plugin.inject, ['skills'], 'inject 必须是 skills');

let captured = null;
const result = await plugin.apply({ skills: { register: (p) => { captured = p; return { ok: true }; } } });
assert.deepEqual(result, { ok: true }, 'apply 必须把 register 的返回值透出');
assert.ok(captured, '必须调用 skills.register');
assert.equal(captured.name, 'xunzi-perspective', '技能名必须与目录一致');
assert.ok(!captured.content.startsWith('---'), 'frontmatter 必须被剥离');
assert.ok(captured.content.includes('## 核心心智模型'), '正文必须包含心智模型段');
assert.ok(captured.resourceBase.path.replace(/[\\/]+$/, '').endsWith(join('skills', 'xunzi-perspective')),
  'resourceBase 必须指向包内 skills/xunzi-perspective');

console.log(JSON.stringify({ probe: 'ok', skill: captured.name, provider: captured.provider, content_bytes: Buffer.byteLength(captured.content) }, null, 2));
