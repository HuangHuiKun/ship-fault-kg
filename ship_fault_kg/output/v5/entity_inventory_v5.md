# V5 实体、关系和属性清单

所有行来自本次实际构建，不是设计目标。详细节点见entities.jsonl，逐边见CSV。

| 类别 | 全部节点 | 通用概念 | 作用 |
| --- | ---: | ---: | --- |
| 船舶（Vessel） | 8 | — | 8条可以从资料识别船名的真实船舶；未具名的事故不捏造船名。船型、动力架构作为属性。 |
| 系统（System） | 6 | 6 | 1个动力系统根节点、5个功能子系统；动力架构不再混作系统类别。 |
| 设备（Equipment） | 64 | 45 | 设备的通用概念及案例内实例；名称不以船名开头，不以“系统”作为设备泛称。 |
| 部件（Component） | 140 | 107 | 零部件通用概念与案例内实例，通过包含关系和检查、维护关系连接。 |
| 故障（Fault） | 216 | 168 | 通用故障概念与案例内故障记录统一标签，用entity_level与INSTANCE_OF区分。 |
| 状态（State） | 350 | 278 | 物理状态、运行异常、症状及后果；不把所有状态都强行归为故障根因。 |
| 影响因素（Factor） | 110 | 85 | 材料、设计、制造、安装、维护、管理等因素；风险因素不等于已证实根因。 |
| 参数（Parameter） | 84 | 84 | 参数和派生特征，含原生单位；原始电压不能未经标定转成工程压力。 |
| 检查方法（Check） | 143 | 143 | 检查方法；关注查什么、使用什么参数，不能与维修动作混为一类。 |
| 运维措施（Action） | 170 | 170 | 维护、处置、预防措施；作为参考主题，不作为自动下发的操作指令。 |
| 事故案例（Case） | 19 | — | 19个原有正式事故案例；不把中文文章或试验工况冒充新增真实事故。 |
| 来源（Source） | 46 | — | 46份实际参与建图的资料或文章。全量注册资料不等于图中来源节点。 |

## 节点实际属性

### 检查方法

`aliases`（143节点）, `display_name`（143节点）, `entity_level`（143节点）, `graph_version`（143节点）, `id`（143节点）, `kind`（143节点）, `kind_zh`（143节点）, `knowledge_zone`（143节点）, `name`（143节点）, `scope_id`（143节点）

### 状态

`aliases`（350节点）, `case_code`（72节点）, `display_name`（350节点）, `entity_level`（350节点）, `graph_version`（350节点）, `id`（350节点）, `kind`（350节点）, `kind_zh`（350节点）, `knowledge_zone`（350节点）, `name`（350节点）, `scope_id`（350节点）

### 设备

`aliases`（64节点）, `applicability`（12节点）, `case_code`（19节点）, `display_name`（64节点）, `entity_level`（64节点）, `graph_version`（64节点）, `id`（64节点）, `kind`（64节点）, `kind_zh`（64节点）, `knowledge_zone`（64节点）, `name`（64节点）, `propulsion_architecture`（19节点）, `scope_id`（64节点）

### 部件

`aliases`（140节点）, `case_code`（33节点）, `display_name`（140节点）, `entity_level`（140节点）, `graph_version`（140节点）, `id`（140节点）, `kind`（140节点）, `kind_zh`（140节点）, `knowledge_zone`（140节点）, `name`（140节点）, `scope_id`（140节点）

### 影响因素

`aliases`（110节点）, `case_code`（25节点）, `display_name`（110节点）, `entity_level`（110节点）, `graph_version`（110节点）, `id`（110节点）, `kind`（110节点）, `kind_zh`（110节点）, `knowledge_zone`（110节点）, `name`（110节点）, `scope_id`（110节点）

### 来源

`aliases`（46节点）, `display_name`（46节点）, `entity_level`（46节点）, `expert_review`（46节点）, `graph_version`（46节点）, `id`（46节点）, `kind`（46节点）, `kind_zh`（46节点）, `knowledge_zone`（46节点）, `license`（46节点）, `local_paths`（46节点）, `name`（46节点）, `scope_id`（46节点）, `sha256`（46节点）, `source_id`（46节点）, `source_level`（46节点）, `source_tier`（46节点）, `url`（46节点）

### 运维措施

`aliases`（170节点）, `display_name`（170节点）, `entity_level`（170节点）, `graph_version`（170节点）, `id`（170节点）, `kind`（170节点）, `kind_zh`（170节点）, `knowledge_zone`（170节点）, `name`（170节点）, `scope_id`（170节点）

### 故障

`aliases`（216节点）, `applicability`（12节点）, `case_code`（48节点）, `display_name`（216节点）, `entity_level`（216节点）, `graph_version`（216节点）, `id`（216节点）, `kind`（216节点）, `kind_zh`（216节点）, `knowledge_zone`（216节点）, `name`（216节点）, `reference_unit`（12节点）, `scope_id`（216节点）

### 参数

`aliases`（84节点）, `definition`（84节点）, `display_name`（84节点）, `entity_level`（84节点）, `graph_version`（84节点）, `id`（84节点）, `kind`（84节点）, `kind_zh`（84节点）, `knowledge_zone`（84节点）, `measurement_form`（70节点）, `name`（84节点）, `native_note`（70节点）, `not_diagnostic_threshold`（70节点）, `parameter_source`（70节点）, `scope_id`（84节点）, `symbol`（70节点）, `unit`（84节点）

### 事故案例

`aliases`（19节点）, `applicability`（19节点）, `case_code`（19节点）, `case_id`（19节点）, `display_name`（19节点）, `entity_level`（19节点）, `graph_version`（19节点）, `id`（19节点）, `kind`（19节点）, `kind_zh`（19节点）, `knowledge_zone`（19节点）, `name`（19节点）, `propulsion_architecture`（19节点）, `scope_id`（19节点）, `vessel_identity_status`（19节点）, `vessel_name`（19节点）

### 船舶

`aliases`（8节点）, `display_name`（8节点）, `entity_level`（8节点）, `graph_version`（8节点）, `id`（8节点）, `kind`（8节点）, `kind_zh`（8节点）, `knowledge_zone`（8节点）, `name`（8节点）, `propulsion_architecture`（8节点）, `scope_id`（8节点）, `vessel_type`（8节点）

### 系统

`aliases`（6节点）, `display_name`（6节点）, `entity_level`（6节点）, `graph_version`（6节点）, `id`（6节点）, `kind`（6节点）, `kind_zh`（6节点）, `knowledge_zone`（6节点）, `name`（6节点）, `scope_id`（6节点）, `system_level`（6节点）

## 关系实际属性

`action_status`, `applicability`, `assertion_id`, `certainty`, `expert_review`, `graph_version`, `id`, `is_causal`, `locator`, `name`, `page`, `passage_id`, `polarity`, `quote`, `review_method`, `scope_id`, `source_file`, `source_id`, `source_sha256`, `source_tier`, `source_url`, `statement_nature`

## 关系编码

| 编码 | 中文名 | 数量 |
| --- | --- | ---: |
| IS_SUBSYSTEM_OF | 属于上级系统 | 5 |
| SERVES_SYSTEM | 服务于系统 | 50 |
| HAS_COMPONENT | 包含部件 | 33 |
| INSTANCE_OF | 是概念的实例 | 197 |
| APPLIES_TO | 适用于 | 544 |
| CAUSES | 导致 | 211 |
| CONTRIBUTES_TO | 促成 | 73 |
| INCREASES_RISK_OF | 增加风险 | 63 |
| WORSENS | 加剧 | 5 |
| HAS_MANIFESTATION | 表现为 | 19 |
| INDICATES | 提示 | 17 |
| ASSOCIATED_WITH | 相关联 | 11 |
| PRECEDES | 先于发生 | 6 |
| CHECKS | 检查 | 143 |
| ADDRESSES | 应对 | 98 |
| ACTS_ON | 作用于 | 80 |
| INVOLVES | 涉及 | 249 |
| OCCURS_ON | 发生于 | 48 |
| HAS_CASE | 发生案例 | 10 |
| DESCRIBED_BY_PARAMETER | 以参数描述 | 12 |
| CHARACTERIZES | 表征 | 70 |
| USES_PARAMETER | 使用参数 | 4 |
| IS_A | 属于概念类别 | 14 |
| DOCUMENTED_BY | 记载于 | 1381 |
