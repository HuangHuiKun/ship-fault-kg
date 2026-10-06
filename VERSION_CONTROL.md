# Git版本管理、上传与安全回退

准备日期：2026-10-06。项目：船舶动力系统故障知识图谱。

## 管理范围

代码、Markdown、来源元数据、评估配置及结果通过普通Git保存历史；论文/报告PDF、原始实验CSV、图像、PPT及SQLite快照通过Git LFS保存。LFS大文件内容也必须上传成功，仅推送指针文件不构成完整备份。

排除Python缓存、node_modules、日志、临时下载、SQLite临时日志、`.env`、密钥及Neo4j本机配置备份。忽略不等于删除，以上文件仍留在本机；第三方原数据、代码的许可和引用应保留。报告与厂家资料建议在私有仓库中用于个人研究，未核实许可前不要公开整包再分发。

本目录之外的Ollama模型、Neo4j Desktop实例目录、密码和运行环境不在Git快照中。当前SQLite快照是500节点/1201关系；Git不能直接备份或回退正在运行的Neo4j服务。

## 查看版本与日常提交

在PowerShell中进入项目：

```powershell
Set-Location 'D:\RAGQnASystem\RAGQnASystem-main'
git status
git log --oneline --decorate -10
git diff
```

修改代码、构建完图谱并测试后：

```powershell
git add .
git diff --cached --stat
git lfs status
git commit -m "说明本次修改，例如补充烧瓦因果链及来源"
```

确认远程已配置再上传：

```powershell
git remote -v
git push
```

首次远程关联必须使用本人确认的目标仓库地址。现有非空远程先检查历史并协商分支，不使用force覆盖。

## 在另一台电脑还原

安装Git及Git LFS，登录有仓库权限的GitHub账号。用实际仓库地址替换占位符：

```powershell
git lfs install
git clone <本人确认的GitHub仓库地址>
```

进入克隆目录后：

```powershell
git lfs pull
git lfs fsck
```

确认SQLite/PDF不是小型LFS指针文本，再按`ship_fault_kg/README_CN.md`配置Python、Ollama与Neo4j。

## 推荐回退方式

先用`git status`确认未提交工作；需要保留就先提交或暂存。不要直接使用`git reset --hard`。

只查看旧版本而不改当前工作目录：

```powershell
git show <提交号>:ship_fault_kg/README_CN.md
git diff <旧提交号> <新提交号> -- ship_fault_kg/
```

需要保留现有历史、撤销一次已提交修改，使用：

```powershell
git revert <要撤销的提交号>
```

会新建一条反向提交；有冲突需审核解决，不要盲目继续。也可在独立目录创建旧版本的研究工作区：

```powershell
git worktree add --detach '..\shipkg-old-version' <旧提交号>
```

进入新目录运行`git lfs pull`取得对应大文件，不影响当前目录。命令中的提交号和目录需要替换为实际值。

## Neo4j回退的特殊注意

Git回退仅改变文件，**不会自动改变Neo4j**。`import_neo4j.py`是MERGE增量导入，不会删去数据库中多出来的节点，不能当作数据库完整回退命令。

最稳妥是在Neo4j中另建测试实例/空数据库，导入旧版本SQLite并核验；正式库的替换须先备份及确认。此前55个传感器的恢复资料位于`ship_fault_kg/output/maintenance_20261005/deleted_sensors_backup.json`，仅用于显式恢复，不应日常执行。

## 远程上传状态

本地Git与LFS已初始化，首个快照为`e5043f4`，回退标签为`shipkg-v3-baseline-20261006`；1659个文件纳入该快照，其中131个文件使用LFS，本地完整性检查通过。

已在本人GitHub账号`HuangHuiKun`下创建[私有仓库ship-fault-kg](https://github.com/HuangHuiKun/ship-fault-kg)，并设置为本地`origin`：`https://github.com/HuangHuiKun/ship-fault-kg.git`。Git Credential Manager设备授权已完成；首轮`main`推送已成功，132个LFS文件对应117个去重对象，约342 MB，已实际上传，不只是保存指针。初始回退标签也纳入远程上传。Git上传授权由本人完成，不要把密码或令牌写进代码/聊天。

每次更新后均须核对远程提交号与本地一致，并确认Git LFS对象上传成功。未推送前本地提交只是本机版本历史，不算GitHub备份。`tools/github_private_repo.py`仅使用既有Git凭据进行私有仓库创建/检查，不显示或持久化令牌；默认只检查，创建需显式`--create`。

可在工作目录干净且完成推送后运行只读核验：

```powershell
python .\tools\verify_github_upload.py
```

核验内容：本人私有仓库、本地HEAD与远程main一致、远程回退标签一致、全部LFS对象可下载，并实际下载当前SQLite快照核对SHA256与长度。脚本不打印令牌、授权头或带签名的下载URL；不会修改远程。
