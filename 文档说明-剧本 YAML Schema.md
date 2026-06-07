# InkFrame 剧本 YAML Schema 设计说明

## 目标

InkFrame 的核心交付物是一个可编辑、可导出的结构化剧本初稿。该 YAML Schema 用于承载小说文本经过 AI Pipeline 转换后的剧本结果，要求同时满足三件事：

1. 能表达剧本内容：角色、幕、场景、对话、动作、旁白、转场。
2. 能追溯原文来源：每个关键剧本元素都能回到原小说章节、段落和原文摘录。
3. 能支持作者二次打磨：字段清晰、结构稳定、可人工编辑，也方便后续导出到其他格式。

## 顶层结构

```yaml
metadata:
  project_id: prj_demo_20260607
  title: 示例章节
  source_language: zh
  created_at: "2026-06-07T10:00:00Z"
  model:
    provider: mock
    name: mock-screenplay

characters:
  - id: char_xiangzi
    name: 祥子
    aliases:
      - 车夫
    description: 年轻车夫，故事主要人物。
    relationships:
      - target_character_id: char_huniu
        type: acquaintance
        description: 与虎妞有多次互动。

acts:
  - id: act_01
    title: 第一幕
    scenes:
      - id: sc_0001
        chapter_id: ch_0001
        title: 街口初遇
        location: 北平街口
        time_of_day: morning
        timeline_order: 1
        elements:
          - id: el_000001
            type: action
            content: 祥子拉着车穿过清晨的街口。
            character_ids:
              - char_xiangzi
            inferred: false
            confidence: 0.92
            source_reference:
              chapter_id: ch_0001
              paragraph_ids:
                - p_000001
              start_offset: 0
              end_offset: 24
              quote: 祥子拉着车穿过清晨的街口。
```

## 字段定义

### metadata

`metadata` 描述剧本来源和生成信息。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `project_id` | string | 是 | 单个章节转换工作区 ID，格式为 `prj_<slug>_<timestamp>` |
| `title` | string | 是 | 剧本标题，通常来自章节标题 |
| `source_language` | `zh` / `en` | 是 | 原文语言 |
| `created_at` | ISO datetime | 否 | 生成时间 |
| `model.provider` | string | 否 | 使用的模型供应商 |
| `model.name` | string | 否 | 使用的模型名称 |

设计原因：`metadata` 让导出的 YAML 离开系统后仍能说明来源、语言和生成上下文，便于复现与归档。

### characters

`characters` 是全局人物表。场景元素只引用 `character_id`，不重复保存完整人物信息。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 人物 ID，格式为 `char_<slug>` |
| `name` | string | 是 | 规范人物名 |
| `aliases` | string[] | 否 | 别名、称呼、代称 |
| `description` | string | 否 | 人物描述 |
| `relationships` | object[] | 否 | 与其他人物的关系 |

`relationships` 字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `target_character_id` | string | 是 | 关系目标人物 ID |
| `type` | string | 是 | 关系类型，如 `family`、`friend`、`enemy`、`acquaintance` |
| `description` | string | 否 | 关系说明 |

设计原因：人物表独立出来，可以避免同一个人物在多个场景中重复描述，也方便作者集中修正角色名、别名和关系。

### acts

`acts` 是剧本的戏剧结构容器。当前 MVP 可只生成一个 `act_01`，但 Schema 保留多幕能力。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 幕 ID，如 `act_01` |
| `title` | string | 否 | 幕标题 |
| `scenes` | Scene[] | 是 | 场景列表 |

设计原因：即使当前主要按章节生成，保留 `acts` 可以让未来支持整本小说的三幕式、分集、分场等更复杂结构，而不破坏顶层契约。

### scenes

`scenes` 表示一个连续的可拍摄场景。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 场景 ID，格式为 `sc_0001` |
| `chapter_id` | string | 是 | 来源章节 ID，格式为 `ch_0001` |
| `title` | string | 否 | 场景标题 |
| `location` | string | 否 | 场景地点 |
| `time_of_day` | string | 否 | 时间，如 `morning`、`night` |
| `timeline_order` | number | 是 | 场景在时间线中的顺序 |
| `elements` | SceneElement[] | 是 | 场景内剧本元素 |

设计原因：场景是小说转剧本的核心中间单位。它比原文段落更接近影视创作，也比完整剧本更容易让作者逐段检查和编辑。

## SceneElement 类型

`elements` 是场景内部的内容单元。所有元素共享以下字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 元素 ID，格式为 `el_000001` |
| `type` | enum | 是 | 元素类型 |
| `content` | string | 是 | 元素正文 |
| `inferred` | boolean | 是 | 是否包含 AI 推断或改写 |
| `confidence` | number | 是 | 置信度，范围 `0.0` 到 `1.0` |
| `source_reference` | object | 强烈建议 | 原文引用 |

### dialogue

角色对白。

```yaml
- id: el_000002
  type: dialogue
  character_id: char_xiangzi
  content: 我今天一定要把车拉回来。
  parenthetical: 低声
  inferred: true
  confidence: 0.76
  source_reference:
    chapter_id: ch_0001
    paragraph_ids: [p_000003]
    start_offset: 40
    end_offset: 88
    quote: 他心里暗暗发誓，今天一定要把车拉回来。
```

额外字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `character_id` | string | 是 | 说话人物 |
| `parenthetical` | string | 否 | 括注，如语气、动作提示 |

设计原因：对白需要绑定唯一说话人。`parenthetical` 用于表达必要的表演提示，但不和正文混在一起。

### action

动作或舞台指示。

```yaml
- id: el_000003
  type: action
  content: 祥子停下脚步，回头看向街角。
  character_ids: [char_xiangzi]
  inferred: false
  confidence: 0.9
  source_reference:
    chapter_id: ch_0001
    paragraph_ids: [p_000004]
    start_offset: 90
    end_offset: 116
    quote: 祥子停下脚步，回头看向街角。
```

额外字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `character_ids` | string[] | 否 | 参与动作的人物 |

设计原因：动作是最接近可拍摄内容的元素，用于承载小说中的动作描写、环境互动和可视化叙事。

### narration

旁白或必须保留但无法直接视觉化的信息。

```yaml
- id: el_000004
  type: narration
  content: 那一年，北平的冬天来得格外早。
  inferred: false
  confidence: 0.86
  source_reference:
    chapter_id: ch_0001
    paragraph_ids: [p_000005]
    start_offset: 120
    end_offset: 146
    quote: 那一年，北平的冬天来得格外早。
```

设计原因：不是所有小说信息都适合转成动作或对白。`narration` 可以保留关键背景、时间跨度、心理信息，避免信息丢失。

### transition

转场。

```yaml
- id: el_000005
  type: transition
  content: CUT TO:
  inferred: true
  confidence: 0.7
```

设计原因：转场是剧本格式的一部分，但很多时候来自结构判断而不是原文直接描写，因此常见 `inferred: true`。

## source_reference

`source_reference` 是 InkFrame 的核心设计之一，用于把剧本元素追溯回原小说。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `chapter_id` | string | 是 | 来源章节 ID |
| `paragraph_ids` | string[] | 是 | 来源段落 ID，至少一个 |
| `start_offset` | number | 是 | 原文起始字符偏移 |
| `end_offset` | number | 是 | 原文结束字符偏移 |
| `quote` | string | 是 | 原文短摘录，最长建议 500 字 |

设计原因：AI 改编最容易出现的问题是“看起来合理但不知道从哪来”。`source_reference` 让作者能快速核对生成内容是否忠于原文，也能为低置信度内容提供审查入口。

## ID 规范

| 类型 | 格式 | 示例 |
| --- | --- | --- |
| Project | `prj_<slug>_<timestamp>` | `prj_demo_20260607` |
| Chapter | `ch_0001` | `ch_0001` |
| Paragraph | `p_000001` | `p_000001` |
| Character | `char_<slug>` | `char_xiangzi` |
| Scene | `sc_0001` | `sc_0001` |
| Element | `el_000001` | `el_000001` |

设计原因：稳定 ID 可以让前端编辑、关系图、时间线、校验日志和导出结果互相引用，避免依赖显示文本作为关联键。

## 设计取舍

### 为什么使用 YAML

YAML 比 JSON 更适合作为作者可读、可编辑的导出格式。剧本内容包含大量自然语言文本，YAML 的层级结构更清楚，也更适合手动修改。

### 为什么不是传统剧本格式

Final Draft、Fountain 等格式更适合最终排版，但不适合承载 AI 生成过程中的置信度、推断标记、原文引用和人物关系。InkFrame 的 YAML 是“可审查的结构化初稿”，不是最终排版格式。

### 为什么保留 confidence 和 inferred

AI 生成内容并不天然可信。`confidence` 帮作者判断哪些地方需要重点检查，`inferred` 明确标出由 AI 推断、补写或转换的内容，避免把推断误认为原文事实。

### 为什么 characters 与 scenes 分离

角色是全局实体，场景是局部结构。分离后，同一个角色可以跨场景复用，关系图也能直接从人物表生成。

### 为什么 source_reference 是强约束

本产品面向小说改编，不是自由创作工具。保留原文依据是作者信任系统的关键，也是后续审查、编辑和调试生成质量的基础。

## 最小合法示例

```yaml
metadata:
  project_id: prj_demo_20260607
  title: 第一章
  source_language: zh
characters: []
acts:
  - id: act_01
    title: 第一章
    scenes:
      - id: sc_0001
        chapter_id: ch_0001
        title: 开场
        timeline_order: 1
        elements:
          - id: el_000001
            type: narration
            content: 故事开始。
            inferred: false
            confidence: 1.0
            source_reference:
              chapter_id: ch_0001
              paragraph_ids:
                - p_000001
              start_offset: 0
              end_offset: 5
              quote: 故事开始。
```

InkFrame 的 YAML Schema 把“剧本表达”和“原文可追溯性”绑定在一起。每个场景元素都可以标记来源、置信度和是否由 AI 推断，作者可以快速定位需要审查的位置，并在结构化结果上继续打磨。
