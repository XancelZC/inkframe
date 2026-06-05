# InkFrame

InkFrame 是一款 AI 辅助的小说转剧本工具。它将中文或英文小说自动转换为结构化剧本初稿，支持源文本溯源、置信度评分、推断内容标记，并保留可检查的中间 JSON 文件。

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- （可选）OpenAI API Key（用于真实 LLM 调用）

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate  # macOS/Linux
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

默认使用 **mock provider**，返回确定性 JSON，无需 API Key。

如需使用真实 LLM，设置环境变量：

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
```

## 架构

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
YAML 导出
  - 结构化剧本含元数据
  - 保留原文溯源引用
```

每个阶段读取上一阶段的 JSON 输出，写入本阶段结果。中间文件存储在 `data/projects/<project_id>/`。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/projects` | 项目列表 |
| POST | `/api/projects` | 创建项目（表单：title, text, file） |
| GET | `/api/projects/{id}` | 项目详情 |
| POST | `/api/projects/{id}/process?from_stage=...` | 运行流水线 |
| GET | `/api/projects/{id}/stages/{stage}` | 获取阶段中间结果 |
| GET | `/api/projects/{id}/characters` | 获取角色表 |
| PUT | `/api/projects/{id}/characters` | 保存编辑后的角色 |
| GET | `/api/projects/{id}/screenplay` | 获取剧本 |
| PUT | `/api/projects/{id}/screenplay` | 保存编辑后的剧本 |
| GET | `/api/projects/{id}/validation` | 获取校验日志 |
| GET | `/api/projects/{id}/export` | 导出 YAML 文件 |
| GET | `/api/projects/{id}/status` | 获取流水线状态 |
| GET | `/api/projects/{id}/events` | SSE 进度流 |
| GET | `/api/models` | 可用 LLM 列表 |

## 前端功能

- **分栏编辑器**：左侧原文 + 右侧剧本卡片，双向高亮联动
- **角色表**：查看和编辑提取的角色信息
- **关系图谱**：React Flow 可视化人物网络
- **场景时间线**：横向滚动的场景卡片
- **校验日志**：可过滤的日志列表，按严重程度着色
- **YAML 预览**：实时 JSON 预览
- **导出**：下载 YAML 剧本文件

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
│   │   ├── api/          # FastAPI 路由
│   │   ├── llm/          # LLM 抽象层
│   │   ├── models/       # Pydantic 数据契约
│   │   ├── pipeline/     # 阶段 0-3 实现
│   │   ├── storage.py    # 文件存储
│   │   └── main.py       # FastAPI 入口
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/   # 图谱、时间线、场景列表
│   │   ├── pages/        # 首页、新建项目、项目详情
│   │   └── App.tsx       # 路由
│   └── package.json
├── examples/             # 示例小说文本
├── PRD.md                # 产品需求文档
├── theme.css             # 设计令牌
└── .agents/              # 设计指南
```

## 文档

- [PRD.md](./PRD.md)：产品需求、架构决策、API 契约、存储契约
- [theme.css](./theme.css)：设计令牌（基于 Notion 设计系统）
- [.agents/DESIGN_GUIDE.md](./.agents/DESIGN_GUIDE.md)：UI 开发指南
