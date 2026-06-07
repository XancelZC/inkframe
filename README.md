# InkFrame

InkFrame 是一款 AI 辅助的小说转剧本工具。它将中文或英文小说自动转换为结构化剧本初稿，支持源文本溯源、置信度评分、推断内容标记，并保留可检查的中间 JSON 文件。

## 🎬 演示视频

> **[👉 点击此处观看演示视频（百度网盘）](https://pan.baidu.com/s/1A5iy07THw8yLdcgzN2cAww)**

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

在浏览器中打开 http://localhost:5173。

### LLM 配置

默认使用 Mock 供应商（本地测试，无需 API Key）。

如需使用真实 LLM，在前端 **LLM 设置** 页面添加供应商：
- 选择协议类型（OpenAI 兼容 / Anthropic 兼容）
- 填写 API 地址和 API Key
- 点击「获取模型」从 API 拉取可用模型列表
- 点击「测试连接」验证配置是否正确

配置自动持久化到 `data/llm_config.json`，重启不丢失。

## 架构

### 数据层级

```
小说（Novel）── 一个小说对应一本完整作品
  └── 章节（Chapter/Project）── 每章独立运行 Pipeline
```

### Pipeline（每章节独立运行）

```
小说文本
  │
  ▼
阶段 0：文本预处理（纯规则）
  - 按章节和段落切分
  - 语言检测（中文/英文）
  - 分配稳定 ID
  │
  ▼
阶段 1：角色提取（LLM）
  - 提取角色名、别名、描述
  - 构建人物关系图
  - 使用 jieba/spaCy 辅助候选名
  │
  ▼
阶段 2：场景合成（LLM）
  - 生成场景、对话、动作、旁白
  - 元素关联到原文段落
  - 标记推断内容和置信度
  │
  ▼
阶段 3：一致性校验（规则）
  - 检查角色名引用
  - 验证场景连续性
  - 标记低置信度元素
  │
  ▼
YAML 导出（单章 / 整本小说）
```

每个阶段读取上一阶段的 JSON 输出，写入本阶段结果。中间文件存储在 `data/projects/<project_id>/`。小说元数据存储在 `data/novels/index.json`。

## API 接口

### 小说管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/novels` | 小说列表（含章节信息） |
| POST | `/api/novels` | 创建小说 |
| GET | `/api/novels/{id}` | 小说详情（含章节列表） |
| PUT | `/api/novels/{id}` | 修改小说标题/语言 |
| DELETE | `/api/novels/{id}` | 删除小说（级联删除章节） |
| POST | `/api/novels/{id}/chapters` | 在小说下创建章节（支持文本/文件上传） |
| GET | `/api/novels/{id}/export` | 导出小说全部章节为 YAML |

### 章节/项目

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects/{id}` | 项目详情 |
| PUT | `/api/projects/{id}` | 修改项目标题 |
| DELETE | `/api/projects/{id}` | 删除项目 |
| POST | `/api/projects/{id}/process?from_stage=...` | 运行流水线 |
| GET | `/api/projects/{id}/stages/{stage}` | 获取阶段中间结果 |
| GET | `/api/projects/{id}/characters` | 获取角色表 |
| PUT | `/api/projects/{id}/characters` | 保存编辑后的角色 |
| GET | `/api/projects/{id}/screenplay` | 获取剧本 |
| PUT | `/api/projects/{id}/screenplay` | 保存编辑后的剧本 |
| GET | `/api/projects/{id}/validation` | 获取校验日志 |
| GET | `/api/projects/{id}/export` | 导出单章 YAML |
| GET | `/api/projects/{id}/status` | 获取流水线状态 |
| GET | `/api/projects/{id}/events` | SSE 进度流 |

### LLM 供应商管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models/config` | 获取全部供应商配置（Key 遮罩） |
| POST | `/api/models` | 添加供应商 |
| PUT | `/api/models/{id}` | 更新供应商 |
| DELETE | `/api/models/{id}` | 删除供应商 |
| PUT | `/api/models/{id}/active` | 设为默认供应商 |
| POST | `/api/models/{id}/fetch` | 从 API 获取模型列表 |
| POST | `/api/models/{id}/test` | 测试连接 |

## 前端功能

- **小说列表**：树形结构，展开/折叠章节，支持搜索和排序（按时间/按名称）
- **小说详情**：章节卡片列表，新建章节（粘贴文本/上传文件），导出全部 YAML
- **分栏编辑器**：左侧原文 + 右侧剧本卡片，双向高亮联动
- **一键运行**：一键运行全部 4 个阶段，也可单阶段运行
- **角色表**：查看和编辑提取的角色信息
- **关系图谱**：React Flow 可视化人物网络
- **场景时间线**：横向滚动的场景卡片
- **校验日志**：可过滤的日志列表，按严重程度着色
- **YAML 预览**：实时 JSON 预览
- **LLM 设置**：多供应商管理，API Key 遮罩，模型获取，测试连接

## 运行测试

```bash
cd backend
python -m pytest tests/ -v
```

## 项目结构

```
inkframe/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI 路由
│   │   │   ├── novels.py     # 小说管理 API
│   │   │   ├── projects.py   # 章节/项目 API
│   │   │   └── models.py     # LLM 供应商 API
│   │   ├── llm/              # LLM 抽象层
│   │   │   ├── mock.py       # Mock 供应商
│   │   │   ├── openai_compat.py
│   │   │   └── anthropic_compat.py
│   │   ├── models/           # Pydantic 数据契约
│   │   │   ├── ids.py        # ID 格式与生成器
│   │   │   ├── novel.py      # 小说模型
│   │   │   ├── project.py    # 项目/章节模型
│   │   │   ├── screenplay.py # 剧本模型
│   │   │   └── ...
│   │   ├── pipeline/         # 阶段 0-3 实现
│   │   │   ├── stage0.py     # 文本预处理
│   │   │   ├── stage1.py     # 角色提取
│   │   │   ├── stage2.py     # 场景合成
│   │   │   ├── stage3.py     # 一致性校验
│   │   │   └── progress.py   # SSE 进度追踪
│   │   ├── storage.py        # 文件存储
│   │   └── main.py           # FastAPI 入口
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/       # 通用组件
│   │   │   ├── AddProviderModal.tsx
│   │   │   ├── CreateNovelModal.tsx
│   │   │   ├── MaskedInput.tsx
│   │   │   ├── ModelCombobox.tsx
│   │   │   ├── RelationshipGraph.tsx
│   │   │   ├── SceneList.tsx
│   │   │   └── SceneTimeline.tsx
│   │   ├── pages/            # 页面
│   │   │   ├── Home.tsx       # 小说列表
│   │   │   ├── NovelDetail.tsx # 小说详情（章节列表）
│   │   │   ├── ProjectDetail.tsx # 章节详情（分栏编辑器）
│   │   │   └── Settings.tsx   # LLM 设置
│   │   └── App.tsx           # 路由
│   └── package.json
├── examples/                 # 示例小说文本
│   ├── sample_novel_zh.txt   # 骆驼祥子（5 章）
│   ├── sample_novel_zh2.txt  # 青云修仙记（5 章）
│   └── sample_novel_en.txt   # Pride and Prejudice（3 章）
├── PRD.md                    # 产品需求文档
├── theme.css                 # 设计令牌
└── .agents/
    ├── DESIGN_GUIDE.md       # UI 设计指南
    └── DEVELOPMENT_RULES.md  # 开发规范
```

## 文档

- [PRD.md](./PRD.md)：产品需求、架构决策、API 契约、存储契约
- [theme.css](./theme.css)：设计令牌（基于 Notion 设计系统）
- [.agents/DESIGN_GUIDE.md](./.agents/DESIGN_GUIDE.md)：UI 开发指南
- [.agents/DEVELOPMENT_RULES.md](./.agents/DEVELOPMENT_RULES.md)：开发规范与提交纪律
