# Codex 安装说明（第一版）

本包只用两种文件构成：一个安装脚本 + 一个 skill 目录。没有运行时依赖。

## 三步装完

```bat
:: 1. 解压到一个你记得住的位置，例如 C:\SkillLab\xunzi-perspective-Codex-1.0.1
cd C:\SkillLab\xunzi-perspective-Codex-1.0.1

:: 2. 先干跑一次，看清会装到哪（一个字节都不写）
python install_codex.py --dry-run

:: 3. 真装
python install_codex.py
```

成功标志：输出里 `"status": "installed_and_verified"`。

## 装完立刻做

**新开一个任务**（Codex 只在任务启动时扫描 skills 目录），输入：

```
用荀子的视角看：一个团队里最能干的人为什么总被排挤？
```

判断是否真的加载成功，看四条：第一句是判断 / 中间分档且给轴 / 引了原书句子并标篇名 / 结尾是反问或命名。
四条全中才算装好；都不是，读本包内 `xunzi-perspective\references\troubleshooting.md`。

## 没有 Python 也能装

手工把 `xunzi-perspective` 整个目录复制到：

- `%USERPROFILE%\.codex\skills\xunzi-perspective\`（旧布局），或
- `%USERPROFILE%\.agents\skills\xunzi-perspective\`（新布局）

必须保证 `…\skills\xunzi-perspective\SKILL.md` 在这个深度（不能多套一层）。

## 常用选项

| 命令 | 作用 |
|---|---|
| `python install_codex.py --dry-run` | 只校验，不写盘 |
| `python install_codex.py --destination D:\my-skills` | 装到指定目录 |
| `python install_codex.py --replace` | 升级（先整份备份，再精确镜像） |

## 回滚与卸载

升级会自动备份到 `<skills根>\xunzi-perspective.backup-<时间戳>`。回滚即删掉当前目录、把备份改回原名。
卸载即删除 `xunzi-perspective` 目录；本 skill 不在系统其它位置写文件。

## 底本说明

底本《荀子》（方勇、李波 译注，中华书局 2010）受版权保护，**不随本包分发**。不装底本也能完整使用本 skill；只有想回原书核对页码时，才需要自备扫描件（详见 `references\quickstart.md`）。

## 完整教程

见 `Codex-First-Edition.pdf`。
