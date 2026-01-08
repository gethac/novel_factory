# Token统计功能说明

## 已完成的功能

### 1. 数据库模型更新

#### Novel模型新增字段
- `total_tokens`: 总Token消耗
- `prompt_tokens`: 输入Token
- `completion_tokens`: 输出Token
- `total_cost`: 总费用（美元）

#### 新增TokenUsage模型
记录每次API调用的详细信息：
- Token使用量（prompt/completion/total）
- 费用计算
- 调用耗时
- 阶段和操作类型
- 章节号（如适用）

### 2. AI服务增强

#### 自动Token记录
- 每次API调用自动记录Token使用
- 支持多种模型的费用计算（GPT-4、GPT-3.5、Claude等）
- 记录调用耗时

#### 模型价格表
```python
MODEL_PRICING = {
    'gpt-4': {'prompt': 0.03, 'completion': 0.06},
    'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
    'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
    'claude-3-opus': {'prompt': 0.015, 'completion': 0.075},
    'claude-3-sonnet': {'prompt': 0.003, 'completion': 0.015},
}
```

### 3. Token统计API

#### GET /api/stats
全局统计，包含Token和费用总计

#### GET /api/token-stats
全局Token统计，支持参数：
- `days`: 统计天数（默认7天）
- `novel_id`: 按小说筛选

返回数据：
- 详细使用记录
- 按阶段统计
- 按日期统计

#### GET /api/novels/{id}/token-stats
单个小说的详细Token统计：
- 按阶段统计（设定、大纲、细纲、内容、检查）
- 按章节统计
- 按操作类型统计
- 平均调用耗时

## 待完成功能

### 1. ai_service.py更新
需要更新以下方法的API调用以记录Token：
- check_settings
- generate_outline
- check_outline
- generate_detailed_outline
- check_detailed_outline
- generate_chapter_content
- check_chapter_content

### 2. 前端Token统计仪表盘
需要添加：
- Token统计标签页
- 图表展示（使用Chart.js）
  - 按阶段的Token使用饼图
  - 按日期的Token使用趋势图
  - 按章节的Token使用柱状图
  - 费用统计
- 筛选功能（按小说、按时间范围）
- 详细数据表格

### 3. GitHub Actions工作流
创建自动化部署流程

## 使用示例

### API调用示例

```bash
# 获取全局统计
curl http://localhost:5000/api/stats

# 获取最近7天的Token统计
curl http://localhost:5000/api/token-stats?days=7

# 获取特定小说的Token统计
curl http://localhost:5000/api/novels/1/token-stats
```

### 响应示例

```json
{
  "novel": {
    "id": 1,
    "title": "修仙传奇",
    "total_tokens": 150000,
    "total_cost": 4.5
  },
  "stage_stats": [
    {
      "stage": "settings",
      "total_tokens": 5000,
      "total_cost": 0.15,
      "count": 2
    },
    {
      "stage": "content",
      "total_tokens": 120000,
      "total_cost": 3.6,
      "count": 30
    }
  ],
  "chapter_stats": [
    {
      "chapter_number": 1,
      "total_tokens": 4000,
      "total_cost": 0.12
    }
  ]
}
```

## 下一步工作

1. 完成ai_service.py中所有API调用的Token记录
2. 创建前端Token统计仪表盘
3. 添加图表可视化
4. 提交到GitHub
5. 创建GitHub Actions工作流

## 注意事项

- Token统计功能需要数据库迁移（删除旧的novels.db重新初始化）
- 费用计算基于OpenAI官方定价，实际费用可能有差异
- 建议定期导出Token使用数据进行分析
