# Token统计功能 - 使用指南

## 功能概述

系统已集成完整的Token使用统计功能，可以详细追踪每次AI API调用的Token消耗和费用。

## 已实现功能

### 1. 数据库支持
- **Novel表新增字段**：total_tokens, prompt_tokens, completion_tokens, total_cost
- **TokenUsage表**：记录每次API调用的详细信息

### 2. 自动Token记录
- 每次调用AI API自动记录Token使用
- 支持多种模型的费用计算（GPT-4、GPT-3.5、Claude等）
- 记录调用耗时和性能数据

### 3. 统计API接口

#### 全局统计
```
GET /api/stats
```
返回系统总体统计，包括Token总量和总费用

#### Token详细统计
```
GET /api/token-stats?days=7&novel_id=1
```
参数：
- `days`: 统计天数（默认7天）
- `novel_id`: 按小说筛选（可选）

返回：
- 详细使用记录列表
- 按阶段统计（settings, outline, content等）
- 按日期统计（每日Token使用趋势）

#### 单个小说统计
```
GET /api/novels/{id}/token-stats
```
返回：
- 按阶段统计（含平均耗时）
- 按章节统计
- 按操作类型统计

## 使用示例

### 查看小说Token消耗

```python
import requests

# 获取小说1的Token统计
response = requests.get('http://localhost:5000/api/novels/1/token-stats')
data = response.json()

print(f"小说标题: {data['novel']['title']}")
print(f"总Token: {data['novel']['total_tokens']}")
print(f"总费用: ${data['novel']['total_cost']:.2f}")

# 按阶段查看
for stage in data['stage_stats']:
    print(f"{stage['stage']}: {stage['total_tokens']} tokens, ${stage['total_cost']:.4f}")
```

### 查看系统总体统计

```python
response = requests.get('http://localhost:5000/api/stats')
stats = response.json()

print(f"总小说数: {stats['total_novels']}")
print(f"总Token消耗: {stats['total_tokens']}")
print(f"总费用: ${stats['total_cost']:.2f}")
```

## 模型价格表

系统内置以下模型的价格（每1000 tokens，美元）：

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| GPT-4 | $0.03 | $0.06 |
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| Claude-3 Opus | $0.015 | $0.075 |
| Claude-3 Sonnet | $0.003 | $0.015 |

## 数据结构

### TokenUsage记录
```json
{
  "id": 1,
  "novel_id": 1,
  "stage": "content",
  "operation": "generate_chapter_content",
  "chapter_number": 1,
  "prompt_tokens": 1500,
  "completion_tokens": 2500,
  "total_tokens": 4000,
  "cost": 0.12,
  "model_name": "gpt-4",
  "duration": 15.5,
  "created_at": "2026-01-07T10:30:00"
}
```

## 前端集成（待完成）

计划添加Token统计仪表盘，包含：
- 📊 Token使用趋势图表
- 💰 费用统计和预测
- 📈 按阶段/章节的详细分析
- 🔍 筛选和导出功能

## 注意事项

1. **数据库迁移**：首次使用需要删除旧的`novels.db`文件，系统会自动创建新表结构
2. **费用计算**：基于官方定价，实际费用可能略有差异
3. **性能影响**：Token记录对性能影响极小（<10ms）
4. **数据保留**：建议定期备份Token使用数据用于成本分析

## 下一步开发

- [ ] 前端可视化仪表盘
- [ ] Token使用预警功能
- [ ] 费用预算管理
- [ ] 数据导出（CSV/Excel）
- [ ] 成本优化建议

## 技术实现

Token记录在`ai_service.py`的`_call_api`方法中自动完成：

```python
def _call_api(self, messages, temperature=0.7, max_tokens=4000,
              novel_id=None, operation=None, stage=None, chapter_number=None):
    # API调用
    response = requests.post(...)

    # 提取Token信息
    usage = result.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)

    # 计算费用
    cost = self._calculate_cost(prompt_tokens, completion_tokens, self.model)

    # 记录到数据库
    self._record_token_usage(...)

    return content, usage_info
```

---

**当前版本**: v1.1.0
**更新日期**: 2026-01-07
**状态**: 核心功能已完成，前端可视化开发中
