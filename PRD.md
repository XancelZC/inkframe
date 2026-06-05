# PRD: InkFrame — AI 小说转剧本工具

## Product Name

**InkFrame**。含义是把散文式的文字（Ink）转换成可被镜头组织的剧本框架（Frame）。名称足够短，便于作为 GitHub 仓库名、产品名和 API 包名前缀使用，也不绑定任何具体 LLM provider。

## Problem Statement

小说作者希望将自己的作品改编成剧本，但改编过程门槛高、耗时长。从散文式叙事到结构化剧本，需要理解角色关系、切分场景、转换对话、压缩叙述，并保留可回溯的原文依据。作者需要一个 AI 辅助工具，自动生成可编辑的结构化剧本初稿，让后续打磨从“修订”开始，而不是从零开始。

## Solution

InkFrame 是一个基于 LLM Pipeline 的 Web 工具，将中文或英文小说文本转换为结构化 YAML 剧本。系统按阶段生成可检查的中间 JSON：文本预处理、角色提取、场景合成、一致性校验、YAML 格式化。Web UI 提供原文/剧本左右分栏、角色关系图、场景时间线、中间结果查看、进度状态和 YAML 实时预览。

核心设计原则：
- **Pipeline 架构**：每个阶段独立可测、可调试，中间结果可检查。
- **文件即契约**：每个阶段的 JSON 输出都有稳定 schema，作为测试和前后端集成依据。
- **信息不丢失**：转换结果必须保留 `source_reference`，AI 推断内容标记 `inferred`。
- **本地文件优先 MVP**：第一版不引入数据库，用项目目录和索引文件支撑项目列表、处理状态和编辑保存。
- **作者拥有最终决定权**：AI 只生成初稿和提示，用户可直接编辑角色、场景和 YAML 输出。

## User Stories

1. 作为小说作者，我想上传或粘贴小说文本，以便系统开始自动转换。
2. 作为小说作者，我想选择或自动检测小说语言，以便系统使用正确的预处理策略。
3. 作为小说作者，我想看到自动识别的角色及其别名，以便确认角色提取是否准确。
4. 作为小说作者，我想编辑角色信息，包括名称、描述、别名和关系，以便修正识别错误。
5. 作为小说作者，我想看到系统自动将小说切分为场景，以便理解剧本结构。
6. 作为小说作者，我想看到每个场景包含的对话、动作描述、转场和旁白，以便评估转换质量。
7. 作为小说作者，我想看到间接引语被还原为直接对话，并带有推断标记，以便知道哪些内容需要重点审查。
8. 作为小说作者，我想看到内心独白被转换为动作描述或旁白，以便剧本更符合视觉叙事。
9. 作为小说作者，我想看到叙述性描写被压缩为简洁动作行，以便剧本节奏更紧凑。
10. 作为小说作者，我想左右分栏查看原文和剧本对照，以便快速定位需要修改的位置。
11. 作为小说作者，我想直接编辑剧本内容，以便即时修正转换错误。
12. 作为小说作者，我想看到角色关系图谱，以便理解人物网络。
13. 作为小说作者，我想看到每个转换结果的置信度分数，以便知道哪些部分需要检查。
14. 作为小说作者，我想看到 AI 推断内容被明确标注，以便区分原文信息和 AI 补充。
15. 作为小说作者，我想导出最终剧本为 YAML 文件，以便在其他工具中继续编辑。
16. 作为小说作者，我想看到一致性校验日志，以便了解潜在问题。
17. 作为小说作者，我想实时预览 YAML 输出，以便即时看到结构化结果。
18. 作为小说作者，我想按章节分批处理长篇小说，以便避免单次处理超时。
19. 作为小说作者，我想看到处理进度，包括当前阶段、章节和错误状态，以便了解等待时间。
20. 作为小说作者，我想重新运行某个 Pipeline 阶段，以便在修改输入后重新处理。
21. 作为小说作者，我想看到场景时间线，以便理解剧本时间结构。
22. 作为小说作者，我想选择不同 LLM provider，以便使用我偏好的服务。
23. 作为小说作者，我想查看每个 Pipeline 阶段的中间 JSON，以便调试转换问题。
24. 作为小说作者，我想使用示例小说快速体验工具效果，以便先了解工具能力。
25. 作为小说作者，我想通过场景标题快速跳转，以便在长剧本中导航。

## Implementation Decisions

### 1. Architecture: File-backed Pipeline

系统采用多阶段 Pipeline。每个阶段读取上一阶段文件，写入本阶段文件，不依赖进程内共享状态。MVP 使用文件系统持久化；数据库、多人协作和云部署不进入第一版。

Pipeline 阶段：
- **Stage 0 - Text Preprocessing**：生成章节、段落、语言和原文偏移。纯规则，无 LLM。
- **Stage 1 - Character Extraction**：从全文或章节摘要中识别角色、别名、描述和关系。LLM 调用，可使用 NLP 候选名辅助。
- **Stage 2 - Scene Synthesis**：按章节生成场景、对话、动作、旁白、转场、叙述压缩和间接引语还原。该阶段保持为一次章节级 LLM 合成，避免拆成多个互相覆盖的 LLM 阶段。
- **Stage 3 - Consistency Validation**：全局检查角色名一致性、场景连续性、缺失引用、低置信度内容和 YAML 契约问题。
- **Stage 4 - YAML Formatting**：将验证后的结构化 JSON 转换成最终 YAML。纯模板，无 LLM。

### 2. Canonical Data Contract

所有 ID 使用稳定字符串，格式如下：
- `project_id`: `prj_<slug>_<timestamp>`
- `chapter_id`: `ch_0001`
- `paragraph_id`: `p_000001`
- `character_id`: `char_<slug>`
- `scene_id`: `sc_0001`
- `element_id`: `el_000001`

`source_reference` 必须包含：
```json
{
  "chapter_id": "ch_0001",
  "paragraph_ids": ["p_000012", "p_000013"],
  "start_offset": 120,
  "end_offset": 268,
  "quote": "原文短摘录"
}
```

`confidence` 统一为 `0.0` 到 `1.0` 的浮点数。AI 推断、还原、补写或语义压缩内容必须设置 `inferred: true`。

核心 screenplay 结构：
```yaml
metadata:
  project_id: prj_demo_20260605
  title: Demo Novel
  source_language: zh
  created_at: "2026-06-05T00:00:00Z"
  model:
    provider: mock
    name: mock-screenplay
characters:
  - id: char_xiangzi
    name: 祥子
    aliases: ["车夫"]
    description: "年轻车夫"
    relationships:
      - target_character_id: char_huniu
        type: acquaintance
        description: "原文中存在多次互动"
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
            character_ids: [char_xiangzi]
            inferred: false
            confidence: 0.86
            source_reference:
              chapter_id: ch_0001
              paragraph_ids: [p_000012]
              start_offset: 120
              end_offset: 168
              quote: 祥子拉着车...
```

场景元素类型：
- `dialogue`: 必填 `character_id`, `content`；可选 `parenthetical`。
- `action`: 必填 `content`；可选 `character_ids`。
- `transition`: 必填 `content`。
- `narration`: 必填 `content`；用于保留无法视觉化但需要保留的信息。

### 3. LLM Provider Strategy

定义 `LLMProvider` 抽象接口：
- `provider_id`: provider 标识，如 `mock`、`openai`、`anthropic`、`compatible_openai`。
- `list_models()`: 返回可选模型。
- `generate_json(prompt, schema, options)`: 返回符合 schema 的 JSON。
- `stream_json(prompt, schema, options)`: 流式返回阶段进度和部分结果。

配置来源：
- 服务端通过环境变量读取 API key，例如 `OPENAI_API_KEY`、`ANTHROPIC_API_KEY`。
- MVP 必须包含 `mock` provider，用于无密钥开发、测试和演示。
- 国内模型第一版通过 `compatible_openai` 适配 OpenAI-compatible API，不单独实现多个厂商 SDK。

错误处理：
- Provider 错误统一映射为 `provider_error`、`rate_limited`、`invalid_json`、`schema_validation_failed`、`timeout`。
- Stage 失败时写入 `status.json`，前端显示失败阶段和错误摘要。

### 4. Progress and Async Processing

Pipeline 作为后台任务执行。MVP 可使用进程内任务队列；任务状态写入文件，避免前端刷新后丢失状态。

状态枚举：
- `idle`
- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

进度事件通过 SSE 暴露：
- `GET /api/projects/{project_id}/events`

事件结构：
```json
{
  "project_id": "prj_demo_20260605",
  "stage": "scene_synthesis",
  "status": "running",
  "chapter_id": "ch_0003",
  "progress": 0.48,
  "message": "Generating scenes for chapter 3"
}
```

`GET /api/projects/{project_id}/status` 仍保留，用于轮询和刷新后恢复。

### 5. Long Text Strategy

Stage 0 按章节和段落建立结构化输入。默认以章节为 Stage 2 处理单位。若章节超过配置阈值，则按自然段落分块，保留段落 ID 和偏移，后续再合并为章节级场景。

默认配置：
- `max_chapter_chars`: 60000
- `chunk_chars`: 4000
- `chunk_overlap_paragraphs`: 1

阈值必须可配置，不在 PRD 中绑定具体模型上下文长度。

### 6. Conversion Strategy

- **间接引语**：LLM 可还原为直接对话，必须标注 `inferred: true`，并保留来源引用。
- **内心独白**：默认转为动作描述；无法视觉化但必须保留的信息可转为 `narration`。
- **叙述性描写**：压缩为 1 到 2 行动作描述，不静默丢弃关键信息。
- **时间跳跃**：切新场景，写入 `time_of_day` 或场景 metadata。
- **低置信度内容**：保留但标记低 `confidence`，并在 Stage 3 校验日志中提示。

### 7. Technology Stack

- **Backend**: Python 3.11+ / FastAPI / Pydantic v2 / PyYAML
- **Frontend**: React 18+ / TypeScript / Vite / TailwindCSS
- **Editor**: CodeMirror 6。MVP 优先轻量集成；后续再评估 Monaco。
- **Graph**: React Flow。用于角色关系图和基础交互。
- **NLP Chinese**: jieba，用于章节和候选名辅助。
- **NLP English**: spaCy，用于 NER 和候选名辅助。
- **LLM**: `mock` provider 必须先实现；OpenAI/Anthropic/compatible provider 后续接入。

### 8. API Design

通用响应：
- 成功响应返回 JSON。
- 错误响应格式：
```json
{
  "error": {
    "code": "schema_validation_failed",
    "message": "Stage output did not match schema",
    "details": {}
  }
}
```

核心接口：
- `POST /api/projects`: 创建项目，支持 `{ title, source_language?, text }` 和文件上传。
- `GET /api/projects`: 获取项目列表。
- `GET /api/projects/{project_id}`: 获取项目详情。
- `POST /api/projects/{project_id}/process`: 触发 Pipeline，可指定 `from_stage`。
- `GET /api/projects/{project_id}/status`: 获取处理进度。
- `GET /api/projects/{project_id}/events`: SSE 进度事件。
- `GET /api/projects/{project_id}/stages/{stage}`: 获取阶段中间结果。
- `GET /api/projects/{project_id}/screenplay`: 获取最终或编辑后的剧本。
- `PUT /api/projects/{project_id}/screenplay`: 保存用户编辑后的剧本。
- `GET /api/projects/{project_id}/characters`: 获取角色表。
- `PUT /api/projects/{project_id}/characters`: 保存编辑后的角色表。
- `GET /api/projects/{project_id}/export`: 导出 YAML 文件。
- `GET /api/models`: 获取可用 provider 和模型。
- `GET /api/examples`: 获取示例小说列表。

### 9. Frontend Structure

- **Home**: 项目列表、新建项目、示例项目入口。
- **Project Detail**:
  - 顶部：项目标题、处理按钮、阶段状态、导出按钮。
  - 左侧：小说原文，只读，支持章节和段落定位。
  - 右侧：剧本编辑器，支持保存和 YAML 预览。
  - 侧边栏或底部标签页：角色表、关系图、场景时间线、中间 JSON、校验日志。
- **Settings**: Provider 配置说明、模型选择、mock provider 开关。

### 10. File Storage Structure

MVP 使用 `data/projects` 目录：
```text
/data/
  projects/
    index.json
    prj_demo_20260605/
      01_raw.txt
      02_preprocessed.json
      03_characters.json
      04_scenes.json
      05_validated.json
      06_screenplay.generated.yaml
      07_screenplay.edited.yaml
      status.json
      metadata.json
      validation_log.json
```

规则：
- `index.json` 存项目摘要，用于项目列表。
- `status.json` 存 Pipeline 状态和最近错误。
- 生成结果和用户编辑结果分开保存；导出优先使用 `07_screenplay.edited.yaml`，不存在时使用 `06_screenplay.generated.yaml`。
- 示例项目可以放在 `examples/`，首次运行时复制到 `data/projects` 或由 API 只读加载。

### 11. Design System and UI Rules

InkFrame 使用温暖、安静、专业的编辑工具风格。设计资产见 `theme.css` 和 `.agents/DESIGN_GUIDE.md`。

核心规范：
- 色彩：主背景 `#ffffff`，辅助背景 `#f6f5f4`，文字 `rgba(0,0,0,0.95)`，强调色 `#0075de`。
- 排版：Inter 字体族，字重 400/500/600/700。所有 letter spacing 统一为 `0`，避免响应式和编辑器界面出现文本挤压。
- 边框：默认 `1px solid rgba(0,0,0,0.1)`。
- 阴影：多层轻阴影，单层透明度不超过 `0.05`。
- 圆角：按钮/输入框 `4px`，卡片 `8px`，模态和大型面板 `12px`，徽章 `9999px`。
- 图标：禁止使用 Emoji，统一使用 SVG 图标或 Lucide Icons。
- 页面：第一屏必须是可用工具界面，不做营销式 landing page。

## Testing Decisions

### Testing Principles

- **测试外部行为，不测实现细节**：每个 Pipeline 阶段作为黑盒，验证输入到输出。
- **中间文件即契约**：阶段 JSON schema 是测试断言依据。
- **LLM 测试使用 mock provider**：默认测试不依赖真实 API。
- **端到端优先验证主路径**：从项目创建到生成 YAML 必须可在本地稳定跑通。

### Test Modules

1. **Schema tests**：验证 `source_reference`、ID、元素类型、状态枚举、错误响应。
2. **Pipeline stage tests**：固定输入文本，校验阶段输出文件。
3. **LLM provider tests**：mock provider 和错误映射。
4. **API endpoint tests**：FastAPI TestClient，验证请求、响应和错误格式。
5. **Frontend component tests**：项目列表、编辑器、进度状态、图谱基本渲染。
6. **End-to-end smoke test**：示例小说输入到 YAML 输出。

### Test Data

- 中文示例：使用公共领域或自造短篇片段，避免版权风险。
- 英文示例：使用公共领域短篇片段。
- 每个示例保存对应的期望中间 JSON，作为回归测试基准。

## Out of Scope

- 实时语音合成或语音识别。
- Final Draft、Fountain 等行业格式导出。
- 多人协作编辑。
- 用户认证系统。
- Docker、CI/CD、云部署脚本。
- 多 key 轮询、负载均衡和复杂限流。
- 小说内容审核或敏感词过滤。
- 数据库存储和跨设备同步。

## Issue and PR Split Strategy

后续 issue 拆分使用 tracer-bullet 方式：每个 issue 尽量交付一个可演示的端到端窄路径，覆盖必要的 schema、API、UI 和测试。基础契约类任务可作为 HITL 决策 issue，普通实现任务优先标为 AFK。

建议顺序：
1. **HITL: Confirm canonical schema and file storage contract**：冻结 ID、`source_reference`、状态枚举、文件结构和错误格式。
2. **AFK: Bootstrap app with mock provider and sample project list**：项目初始化、前后端骨架、mock provider、首页项目列表。
3. **AFK: Create project from pasted text and persist raw input**：创建项目、保存原文、项目详情展示。
4. **AFK: Run Stage 0 preprocessing and show intermediate JSON**：章节/段落切分、语言检测、中间结果查看。
5. **AFK: Extract characters with mock provider and editable character table**：角色表生成、编辑和保存。
6. **AFK: Generate scene synthesis for one chapter with YAML preview**：Stage 2 主路径、左右分栏、YAML 预览。
7. **AFK: Add progress status and SSE events for pipeline runs**：后台任务、状态文件、前端进度。
8. **AFK: Validate consistency and show validation log**：Stage 3、校验日志、低置信度提示。
9. **AFK: Export generated or edited screenplay YAML**：编辑保存、导出优先级、下载接口。
10. **AFK: Add relationship graph and scene timeline views**：角色图谱、时间线、场景跳转。
11. **AFK: Add real OpenAI-compatible provider behind existing interface**：不改变 UI 和 Pipeline 契约，只替换 provider。
12. **AFK: End-to-end demo data and README polish**：示例小说、回归数据、本地运行说明。
