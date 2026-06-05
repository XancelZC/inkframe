#!/bin/bash
# Read old message from stdin
OLD_MSG=$(cat)

# Map based on commit content (use the first few chars to identify)
case "$OLD_MSG" in
  "docs: define InkFrame product contract"*)
    echo "docs: 定义 InkFrame 产品契约" ;;
  "feat: define canonical schema contract as Pydantic models"*)
    echo "feat: 定义数据契约 Pydantic 模型" ;;
  "feat: bootstrap monorepo with mock provider and project list"*)
    echo "feat: 搭建 monorepo，实现 mock 供应商和项目列表" ;;
  "feat: create project from pasted or uploaded text"*)
    echo "feat: 支持粘贴文本或上传文件创建项目" ;;
  "feat: Stage 0 preprocessing with chapter/paragraph splitting"*)
    echo "feat: 实现阶段 0 文本预处理，支持章节和段落切分" ;;
  "feat: character extraction with mock provider and editable table"*)
    echo "feat: 实现阶段 1 角色提取，含可编辑角色表" ;;
  "feat: one-chapter screenplay draft in split editor with YAML preview"*)
    echo "feat: 实现阶段 2 场景合成，含分栏编辑器和 YAML 预览" ;;
  "feat: pipeline progress status and SSE events"*)
    echo "feat: 实现流水线进度状态和 SSE 事件" ;;
  "feat: consistency validation and YAML export"*)
    echo "feat: 实现阶段 3 一致性校验和 YAML 导出" ;;
  "feat: relationship graph and scene timeline views"*)
    echo "feat: 实现人物关系图谱和场景时间线" ;;
  "feat: re-run pipeline from specific stage with prerequisite checks"*)
    echo "feat: 支持从指定阶段重跑流水线，含前置依赖检查" ;;
  "feat: OpenAI-compatible provider with error mapping"*)
    echo "feat: 实现 OpenAI 兼容供应商，含错误映射" ;;
  "feat: demo data, examples, and README polish"*)
    echo "feat: 添加示例小说数据和完善 README" ;;
  "i18n: 全面中文化前端 UI 和 README"*)
    echo "i18n: 全面中文化前端 UI 和 README" ;;
  "fix: add python-multipart dependency for form data parsing"*)
    echo "fix: 添加 python-multipart 依赖以支持表单数据解析" ;;
  "feat: LLM 设置页面（API Key / URL / 模型选择）"*)
    echo "feat: 实现 LLM 设置页面（供应商 / API Key / URL / 模型选择）" ;;
  *)
    echo "$OLD_MSG" ;;
esac
