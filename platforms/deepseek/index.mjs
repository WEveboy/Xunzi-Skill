import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const name = 'dsh-xunzi-perspective';
export const inject = ['skills'];

const directory = new URL('./skills/xunzi-perspective/', import.meta.url);
const markdown = readFileSync(new URL('SKILL.md', directory), 'utf8');
const boundary = markdown.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n/);
if (!boundary) throw new Error('The packaged skill requires YAML frontmatter');

const content = markdown.slice(boundary[0].length);

export function apply(context) {
  return context.skills.register({
    name: 'xunzi-perspective',
    description:
      '第一版：荀子（名况，又称荀卿、孙卿）的思维框架与表达方式。' +
      '6 个心智模型、9 条决策启发式、完整表达 DNA 与 6 对未解张力，附 7 份逐字标注书页的调研记录。',
    content,
    invocation: { modelInvocable: true, userInvocable: true },
    provider: name,
    source: 'bundled',
    resourceBase: { kind: 'directory', path: fileURLToPath(directory) },
  });
}
