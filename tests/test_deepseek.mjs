// DeepSeek Harness 适配器契约测试：临时装配一份插件目录，动态导入并检查注册结果。
// 运行： node --test tests/test_deepseek.mjs
import assert from 'node:assert/strict';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const platformDir = join(root, 'platforms', 'deepseek');
const skillDir = join(root, 'skills', 'xunzi-perspective');

function stage() {
  const dir = mkdtempSync(join(tmpdir(), 'dsh-xunzi-'));
  for (const f of ['index.mjs', 'package.json', 'cordis.patch.yml']) {
    cpSync(join(platformDir, f), join(dir, f));
  }
  mkdirSync(join(dir, 'skills'), { recursive: true });
  cpSync(skillDir, join(dir, 'skills', 'xunzi-perspective'), { recursive: true });
  return dir;
}

const staged = stage();
const plugin = await import(pathToFileURL(join(staged, 'index.mjs')).href);
const edition = JSON.parse(readFileSync(join(skillDir, 'EDITION.json'), 'utf8'));
const pkg = JSON.parse(readFileSync(join(platformDir, 'package.json'), 'utf8'));

test.after(() => rmSync(staged, { recursive: true, force: true }));

test('插件导出协议字段', () => {
  assert.equal(plugin.name, 'dsh-xunzi-perspective');
  assert.deepEqual(plugin.inject, ['skills']);
  assert.equal(typeof plugin.apply, 'function');
});

test('apply 注册 skill 且名字与目录一致', async () => {
  let registered = null;
  const context = {
    skills: {
      register(payload) {
        registered = payload;
        return { ok: true, id: payload.name };
      },
    },
  };
  const result = await plugin.apply(context);
  assert.deepEqual(result, { ok: true, id: 'xunzi-perspective' });
  assert.ok(registered, 'register 必须被调用');
  assert.equal(registered.name, 'xunzi-perspective');
  assert.equal(registered.provider, 'dsh-xunzi-perspective');
  assert.equal(registered.source, 'bundled');
  assert.deepEqual(registered.invocation, { modelInvocable: true, userInvocable: true });
});

test('注入内容已剥离 frontmatter 且指向资源目录', async () => {
  let registered = null;
  await plugin.apply({ skills: { register: (p) => { registered = p; return null; } } });
  assert.ok(!registered.content.startsWith('---'), 'frontmatter 必须被剥离');
  assert.ok(registered.content.includes('## 核心心智模型'), '正文应包含心智模型段');
  assert.ok(registered.content.includes('references/troubleshooting.md'), '正文应指向排障文件');
  const normalize = (p) => p.replace(/[\\/]+$/, '');
  assert.ok(
    normalize(registered.resourceBase.path).endsWith(join('skills', 'xunzi-perspective')),
    'resourceBase 应指向打包内的 skills/xunzi-perspective',
  );
  assert.ok(registered.description.length > 0);
});

test('缺 frontmatter 时导入期即报错', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'dsh-broken-'));
  try {
    cpSync(join(platformDir, 'index.mjs'), join(dir, 'index.mjs'));
    mkdirSync(join(dir, 'skills', 'xunzi-perspective'), { recursive: true });
    const raw = readFileSync(join(skillDir, 'SKILL.md'), 'utf8');
    const stripped = raw.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');
    writeFileSync(join(dir, 'skills', 'xunzi-perspective', 'SKILL.md'), stripped);
    await assert.rejects(
      () => import(pathToFileURL(join(dir, 'index.mjs')).href),
      /frontmatter/i,
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('包版本与 EDITION.json 一致', () => {
  assert.equal(pkg.version, edition.public_version);
  assert.equal(pkg.name, 'dsh-xunzi-perspective');
  assert.deepEqual(pkg.dsh.bundle.patch, './cordis.patch.yml');
  assert.ok(pkg.files.includes('skills'));
});
