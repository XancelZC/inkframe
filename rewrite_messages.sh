#!/bin/bash
# Rewrite commit messages to Chinese
case "$GIT_COMMIT" in
  117152e*) echo "docs: 定义 InkFrame 产品契约" ;;
  d0f5176*) echo "feat: 定义数据契约 Pydantic 模型" ;;
  d2af3a7*) echo "feat: 搭建 monorepo，实现 mock 供应商和项目列表" ;;
  7d29625*) echo "feat: 支持粘贴文本或上传文件创建项目" ;;
  062663a*) echo "feat: 实现阶段 0 文本预处理，支持章节和段落切分" ;;
  5b429fc*) echo "feat: 实现阶段 1 角色提取，含可编辑角色表" ;;
  3f47921*) echo "feat: 实现阶段 2 场景合成，含分栏编辑器和 YAML 预览" ;;
  7f48e56*) echo "feat: 实现流水线进度状态和 SSE 事件" ;;
  0f47a4a*) echo "feat: 实现阶段 3 一致性校验和 YAML 导出" ;;
  55a3d1a*) echo "feat: 实现人物关系图谱和场景时间线" ;;
  9b1eabf*) echo "feat: 支持从指定阶段重跑流水线，含前置依赖检查" ;;
  f91288c*) echo "feat: 实现 OpenAI 兼容供应商，含错误映射" ;;
  9ad711e*) echo "feat: 添加示例小说数据和完善 README" ;;
  5c16206*) echo "i18n: 全面中文化前端 UI 和 README" ;;
  e3abe98*) echo "fix: 添加 python-multipart 依赖以支持表单数据解析" ;;
  39c841d*) echo "feat: 实现 LLM 设置页面（供应商 / API Key / URL / 模型选择）" ;;
  *) echo "$(cat .git/COMMIT_EDITMSG)" ;;
esac
