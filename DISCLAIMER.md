# 免责声明与第三方资料权利说明

更新日期：2026-10-07。适用仓库：`HuangHuiKun/ship-fault-kg`。

## 1. 科研用途与安全边界

本项目用于船舶动力系统故障知识图谱构建、知识检索评价及大语言模型诊断报告增强的科研与教学演示。目前交付的是研究数据、方法原型和开发测试结果，不是经船级社认证的诊断、预测或控制产品。

图谱、因果链、检索结果及大语言模型输出可能存在遗漏、错误、过时信息或适用范围不匹配。参考机理不等于具体船舶已发生相应故障；调查报告中的“可能”“很可能”等表述也不应被解释为已证实的因果结论。开发测试指标不代表实船诊断准确率或安全保障能力。

不得仅依据本项目输出进行停机、降负荷、拆检、调整保护参数、电网操作或其他影响船舶安全的决定。实际运维须由具备资质的人员结合本船构型、实时工况、原厂手册、适用规范和现场检查独立复核。项目按现状提供，不承诺准确性、完整性、适用性或持续可用性；本说明不排除依法不能排除的责任。

## 2. 第三方资料不因仓库公开而获得新授权

仓库包含第三方数据集、事故调查报告、厂家技术文档、论文、代码、图像及其衍生摘录。相关著作权、商标及其他权利仍归原权利人所有。本项目不代表原作者、厂家、调查机构、船东或运营方，也不意味着其认可本项目。

第三方材料应分别遵守原许可证、署名、引用及其他使用条件，优先以原始发布页面和原许可文件为准。来源清单位于 `ship_fault_kg_data/05_metadata/`，许可文件保留在相应资料目录。来源链接或可免费下载不等于允许再分发。

部分中文语料、厂家资料及其他材料的再分发许可尚未核实。本仓库的公开状态、来源标注、“科研用途”说明和本免责声明，**均不构成第三方资料的再分发授权，也不能替代权利人许可**。使用者在复制、发布、改编或商业使用前，应核实相应权利与许可；未明确授权的材料应向原权利人申请许可。

本仓库未通过本说明为全部内容统一授予开源许可证。代码或数据已有明确许可证的，按各自许可证使用；没有许可证的，不应仅因仓库可见就推定获得任意使用或再许可的权利。

## 3. 来源溯源与资料更正

引用本项目中的第三方材料时，应同时引用原报告、论文或数据集，不应将其全部归为本项目原创。图谱关系、证据编号和页码仅用于辅助溯源，使用者仍需核对原文、版本和适用边界。

如权利人认为仓库中的材料涉及权利、保密或个人信息问题，请通过本仓库的 GitHub Issues 提供相关文件路径、来源和权利说明；请勿在公开 Issue 中提交敏感信息。维护者将核查并采取更正、限制或移除等适当措施，必要时进一步处理历史记录。删除当前版本文件不会自动删除其 Git 历史，也不能保证收回已下载、克隆或派生的副本。

## 4. 凭据与本地环境

密码、访问令牌、私钥、个人环境配置及运行中的 Neo4j 数据库目录不应提交到仓库。`.gitignore` 只影响未跟踪文件，并不能清理已经提交的凭据或历史。发现凭据泄露时应立即撤销或轮换，再处理仓库内容。

## English summary

This repository is a research prototype, not a certified marine diagnostic or control product. Outputs require qualified review against the vessel configuration, operating conditions and original documentation. Third-party materials retain their original rights and licenses. Public availability, attribution and this disclaimer do not grant redistribution permission. Some materials have unverified redistribution terms. This notice is not a blanket open-source license and does not exclude liability that cannot legally be excluded. Rights or privacy concerns may be reported through repository Issues without posting sensitive information.
