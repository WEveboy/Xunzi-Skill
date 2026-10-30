# GitHub 更新与发布流程

沿用 WEveboy 既有项目「密码函数指标分析」与「纠错码」两个仓库的最新流程，针对纯 Markdown skill 调整验证命令。

- 上游流程：https://github.com/WEveboy/Boolean_Function_Analysis/blob/main/docs/UPLOAD_WORKFLOW.md
- 参照仓库：https://github.com/WEveboy/The-Theory-of-Error-Correcting-Codes-skill
- 本仓库：https://github.com/WEveboy/Xunzi-Still

## 六步

1. **读远端，列改动。** `git ls-remote` 与 GitHub API 读 `main` 的当前状态；列出本次源码、教程 PDF、安装器、版本文件的改动清单；确认远端其他文件不被覆盖。**空仓库**（size 0、无分支）在全部交付准备就绪后才初始化。
2. **定入仓边界。** `main` 只收：skill 源文件、两份教程 PDF、安装器与适配器、测试、构建脚本、文档。排除：`dist/`、`__pycache__`、缓存、**底本 PDF（版权）**、私人绝对路径、令牌、依赖副本、临时渲染图。
3. **本地全绿。** 依次运行：
   ```bash
   python scripts/rebuild_skill.py --check
   python -m unittest discover -s tests
   node --test tests/test_deepseek.mjs
   python scripts/make_release.py            # 含解压烟测
   ```
   并渲染两份教程 PDF 首页，核对中文、代码块、表格未错版；检查 README 内相对链接均可达。
4. **再读远端后提交。** 提交前重新 `git ls-remote` 确认远端未变；对已有分支用预期 SHA 约束（`git push --force-with-lease` 而非 `--force`），禁止强覆盖他人改动。提交后核对提交 SHA、文件清单与关键页面。
5. **发版。** tag 采用 `edition-v1.0.0` 格式。资产：Codex ZIP、DeepSeek TGZ + ZIP、源码 ZIP、`SHA256SUMS`。**逐个下载回来核验 SHA256** 并做安装烟测。资产未上传成功时，不得在 README 或日志里描述为"已发布"。
6. **收尾。** 更新 README 下载入口、`CHANGELOG.md`、`release-info.json`；记录提交 SHA、资产哈希、未完成事项。后续版本沿用本流程；改版本号时先明确 tag 与新版本的关系，再发布。

## 本仓库的具体约定

- **版本一致性是硬门**：`EDITION.json` 记录 skill 内每个文件的 SHA256，安装器据此拒绝安装。改过 `skills/` 下任何文件而未重跑 `scripts/rebuild_skill.py`，第 3 步的 `--check` 会失败，测试也会失败。这是有意的摩擦。
- **不新增 LICENSE**：用户未指定许可；上游依赖按上游许可自行下载安装，不随本项目再分发。
- **底本不入库**：与纠错码仓库同一策略。调研记录里的逐字引文已覆盖全部被引原文，缺底本不影响使用。
- **发布方式**：本仓库第一版采用本地已认证客户端的 GitHub API 发布 Release（CI 令牌法在纠错码仓库用过，本仓库为纯文档型，暂不引入 Actions）。

## 校验命令一览

```bash
python scripts/rebuild_skill.py --check      # 版本清单 vs 实际文件
python -m unittest discover -s tests -v      # 10 项
node --test tests/test_deepseek.mjs          # 5 项
python scripts/make_release.py               # 打包 + 烟测 + SHA256SUMS
python scripts/smoke_release.py              # 单独跑发行包烟测
```
