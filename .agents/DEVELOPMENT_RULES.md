# InkFrame 开发规范

## 0. 提交纪律

- **未经用户明确允许，禁止执行 git commit 和 git push**
- 每个功能完成后，先展示改动内容，等用户确认无误后再提交
- 用户说"可以提交了"或"提交吧"才能提交

## 1. Git 提交规范

- commit message **统一使用中文**，`feat:` / `fix:` / `docs:` 等前缀除外
- 正确示例：`feat: 定义数据契约 Pydantic 模型`
- 错误示例：`feat: define canonical schema contract as Pydantic models`

## 2. 前端 UI 规范

- 所有用户可见文本使用中文
- 禁止使用 Emoji，统一使用 SVG 图标（Lucide Icons）
- 设计风格基于 Notion 设计系统，见 `theme.css` 和 `.agents/DESIGN_GUIDE.md`

## 3. LLM 配置规范

- 支持多种供应商：Mock、OpenAI 兼容、Anthropic 兼容
- 每个供应商独立配置 URL 和 API Key
- 模型列表通过 API 获取 + 支持手动添加
- 支持测试连接是否通畅
- 不给默认模型展示，模型从 API 动态获取

## 4. 项目管理规范

- 新项目排在最前面（按创建时间倒序）
- 项目支持删除功能，需二次确认
- 项目过多时支持搜索/筛选

## 5. 后端规范

- API 错误响应统一格式：`{"error": {"code": "...", "message": "...", "details": {}}}`
- 所有 ID 使用 `app/models/ids.py` 中定义的格式和生成器
- Pipeline 阶段间通过文件传递数据，不共享内存状态
- 测试使用 mock provider，不依赖真实 API
