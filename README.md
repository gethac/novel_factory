# 🤖 AI Novel Factory - AI小说自动生产系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**一个完全自动化的AI小说创作工厂 | 从设定到成品，零人工干预**

[功能特点](#-功能特点) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [API文档](#-api文档) • [贡献指南](#-贡献指南)

</div>

---

## 📖 项目简介

AI Novel Factory 是一个基于大语言模型的全自动小说生产系统。只需输入主题和背景，系统将自动完成：

- ✅ 小说设定生成（世界观、人物、冲突）
- ✅ 章节大纲生成（完整故事结构）
- ✅ 章节细纲生成（详细写作指导）
- ✅ 正文内容生成（地道中文表达）
- ✅ AI质量检查（多维度自动审核）
- ✅ 自动重试机制（确保质量）
- ✅ 一键导出下载（TXT格式）

## ✨ 功能特点

### 🎯 完全自动化
- **零人工干预**：输入需求后全程自动化
- **智能生成**：AI驱动的完整创作流程
- **质量把控**：每个环节AI自动检查
- **自动重试**：不合格自动重新生成

### 📝 专业写作
- **去翻译腔**：使用专业中文写作Prompt
- **名词先行**：避免长修饰语堆砌
- **动词主导**：生动的场景描写
- **质量检查**：多维度评分系统

### 🎨 现代化Web界面
- **清爽设计**：白色主题 + 玻璃质感
- **实时可视化**：生成过程全程可见
  - 小说设定实时展示
  - 大纲生成实时预览
  - 章节进度详细追踪
  - 细纲内容即时显示
- **仪表盘**：实时统计和状态监控
- **任务管理**：创建、监控、管理小说
- **Token统计**：详细的费用和使用分析
- **AI配置**：支持多模型灵活切换

### 🔧 技术特性
- **RESTful API**：完整的API接口
- **异步生成**：后台线程处理
- **数据持久化**：SQLite数据库
- **Token追踪**：详细的使用统计和费用计算
- **智能容错**：JSON解析失败自动降级
- **跨平台**：支持Windows/Linux/Mac

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/gethac/novel_factory.git
cd novel_factory
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**

复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的AI API配置：
```env
AI_API_BASE=https://api.openai.com/v1
AI_API_KEY=your_api_key_here
AI_MODEL=gpt-4
```

4. **启动系统**

Windows:
```bash
start.bat
```

Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

或手动启动：
```bash
python app.py
```

5. **访问系统**

打开浏览器访问：**http://localhost:5000**

## 📱 使用指南

### 1. 配置AI模型

首次使用需要配置AI模型：

1. 点击 **"AI配置"** 标签
2. 点击 **"添加新配置"**
3. 填入API信息（地址、密钥、模型名称）
4. 点击 **"激活"** 使用该配置

**支持的AI模型：**
- OpenAI (GPT-4, GPT-3.5)
- Claude (通过兼容API)
- 国内大模型（通义千问、文心一言等）

### 2. 创建小说任务

1. 点击 **"创建小说"** 标签
2. 填写小说信息：
   - **主题**：如"都市修仙"、"科幻冒险"
   - **背景设定**：详细描述世界观
   - **目标字数**：建议30000-100000字
   - **目标章节数**：建议10-30章
3. 点击 **"创建并开始生成"**

### 3. 监控进度

生成过程完全可视化：
- 在 **"仪表盘"** 或 **"小说列表"** 查看状态
- 点击 **"查看进度"** 实时查看生成内容：
  - 📝 **小说设定**：实时显示世界观、人物设定
  - 📋 **故事大纲**：完整章节规划即时预览
  - ✍️ **章节生成**：每章进度、细纲、字数统计
- 系统自动刷新（每3秒）
- 点击 **"查看日志"** 查看详细日志

### 4. Token统计

系统提供详细的Token使用分析：
- **总览统计**：总Token、输入/输出Token、总费用
- **按阶段统计**：设定、大纲、细纲、正文各阶段消耗
- **使用趋势**：按日期查看Token使用趋势
- **详细记录**：每次API调用的完整记录
- **筛选功能**：按时间范围和小说筛选

### 5. 导出下载

小说完成后：
1. 点击 **"导出TXT"** 按钮
2. 点击 **"下载"** 获取文件

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────┐
│              Web 管理界面 (HTML/JS)              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│           Flask API Server (app.py)             │
├─────────────────────────────────────────────────┤
│  • 小说管理 API    • 章节管理 API               │
│  • AI配置 API      • 导出下载 API               │
│  • 统计日志 API                                  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│        核心业务层 (novel_generator.py)          │
├─────────────────────────────────────────────────┤
│  生成设定 → 生成大纲 → 生成细纲 → 生成内容      │
│     ↓          ↓          ↓          ↓          │
│  AI检查    AI检查    AI检查    AI检查           │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│          AI服务层 (ai_service.py)               │
├─────────────────────────────────────────────────┤
│  • 调用大模型API  • 专业写作Prompt              │
│  • 质量检查逻辑   • 日志记录                    │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│         数据持久层 (models.py + SQLite)         │
├─────────────────────────────────────────────────┤
│  Novel | Chapter | GenerationLog | AIConfig     │
└─────────────────────────────────────────────────┘
```

## 📚 API文档

### 小说管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/novels` | 获取所有小说列表 |
| POST | `/api/novels` | 创建新小说任务 |
| GET | `/api/novels/{id}` | 获取小说详情 |
| DELETE | `/api/novels/{id}` | 删除小说 |
| POST | `/api/novels/{id}/start` | 启动生成（异步） |

### 章节管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/novels/{id}/chapters` | 获取章节列表 |
| GET | `/api/chapters/{id}` | 获取章节详情 |

### 导出功能

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/novels/{id}/export` | 导出为TXT |
| GET | `/api/novels/{id}/download` | 下载TXT文件 |

### AI配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai-configs` | 获取所有配置 |
| POST | `/api/ai-configs` | 创建配置 |
| PUT | `/api/ai-configs/{id}` | 更新配置 |
| DELETE | `/api/ai-configs/{id}` | 删除配置 |
| POST | `/api/ai-configs/{id}/activate` | 激活配置 |

### 统计日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats` | 获取统计信息 |
| GET | `/api/novels/{id}/logs` | 获取生成日志 |
| GET | `/api/token-stats` | 获取Token统计 |
| GET | `/api/novels/{id}/token-stats` | 获取单个小说Token统计 |

## 🔍 项目结构

```
novel_factory/
├── app.py                 # Flask主应用
├── models.py              # 数据库模型
├── config.py              # 系统配置
├── ai_service.py          # AI服务层
├── novel_generator.py     # 生成核心逻辑
├── exporter.py            # 导出功能
├── templates/
│   └── index.html        # Web界面
├── static/
│   ├── css/
│   │   ├── main.css      # 主样式
│   │   └── components.css # 组件样式
│   └── js/
│       ├── app.js        # 主应用逻辑
│       ├── novel.js      # 小说管理
│       ├── api.js        # API封装
│       └── modules.js    # 工具模块
├── requirements.txt       # 依赖包
├── .env.example          # 环境变量示例
├── start.bat             # Windows启动脚本
├── start.sh              # Linux/Mac启动脚本
└── README.md             # 项目文档
```

## ❓ 常见问题

<details>
<summary><b>Q: 生成一本小说需要多长时间？</b></summary>

取决于字数和AI模型速度：
- 3万字小说：30-60分钟
- 10万字小说：2-4小时
</details>

<details>
<summary><b>Q: 支持哪些AI模型？</b></summary>

支持所有兼容OpenAI API格式的模型：
- OpenAI GPT-4/GPT-3.5
- Claude (通过代理)
- 国内大模型（通义千问、文心一言等）
</details>

<details>
<summary><b>Q: 生成的小说质量如何？</b></summary>

系统使用专业写作Prompt和多重质量检查，能生成较高质量的网文。但仍建议人工审阅和润色。
</details>

<details>
<summary><b>Q: 生成失败怎么办？</b></summary>

系统会自动重试3次。如果仍失败，请检查：
1. AI API配置是否正确
2. API密钥是否有效
3. 网络连接是否正常
4. 查看日志了解具体错误
</details>

<details>
<summary><b>Q: 如何查看Token使用情况？</b></summary>

点击"Token统计"标签可以查看：
- 总体Token消耗和费用
- 按阶段（设定、大纲、细纲、正文）的详细统计
- 按日期的使用趋势
- 每次API调用的详细记录
</details>

<details>
<summary><b>Q: JSON解析失败怎么办？</b></summary>

系统已内置智能容错机制：
- 自动提取markdown代码块中的JSON
- 解析失败时自动降级为"默认通过"
- 不会因为解析错误而中断生成流程
- 详细错误日志会记录在系统日志中
</details>

<details>
<summary><b>Q: 可以自定义写作风格吗？</b></summary>

可以修改 `ai_service.py` 中的Prompt来调整写作风格。
</details>

## 🛠️ 技术栈

- **后端**: Flask + SQLAlchemy
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **数据库**: SQLite
- **AI接口**: OpenAI API兼容格式
- **UI设计**: 玻璃拟态 (Glassmorphism) + 响应式布局

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

### 代码规范

- 遵循 PEP 8 Python代码规范
- 添加必要的注释和文档
- 确保代码通过测试

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有贡献者
- 感谢开源社区的支持

## 📮 联系方式

- 项目地址: [https://github.com/gethac/novel_factory](https://github.com/gethac/novel_factory)
- 问题反馈: [Issues](https://github.com/gethac/novel_factory/issues)

## ⚠️ 免责声明

1. **API费用**: 使用AI API会产生费用，请注意控制成本。系统提供详细的Token统计帮助您监控费用
2. **生成时间**: 长篇小说生成需要较长时间，请耐心等待。系统提供实时进度可视化
3. **内容质量**: AI生成的内容建议人工审阅和润色
4. **版权问题**: 生成的内容版权归使用者所有

## 🎯 更新日志

### v1.2.0 (2026-01-08)
- ✨ 全新白色主题UI设计，移除紫色配色
- ✨ 增强玻璃质感效果 (Glassmorphism)
- ✨ 实时生成过程可视化
  - 小说设定实时展示
  - 大纲生成实时预览
  - 章节进度详细追踪
  - 细纲内容即时显示
- 🐛 修复JSON解析错误，增加智能容错机制
- 🐛 支持markdown代码块格式的JSON提取
- 📝 清理无用文档，只保留README

### v1.1.0
- ✨ 添加Token使用统计功能
- ✨ 详细的费用分析和趋势图表
- ✨ 按阶段、日期、小说的多维度统计

### v1.0.0
- 🎉 初始版本发布
- ✅ 完整的自动化小说生成流程
- ✅ Web管理界面
- ✅ AI质量检查机制

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by [gethac](https://github.com/gethac)

</div>
