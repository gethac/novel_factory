from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Novel(db.Model):
    """小说主表"""
    __tablename__ = 'novels'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    theme = db.Column(db.Text)  # 主题
    background = db.Column(db.Text)  # 背景设定
    target_words = db.Column(db.Integer)  # 目标字数
    target_chapters = db.Column(db.Integer)  # 目标章节数

    # 生成状态
    status = db.Column(db.String(50), default='pending')  # pending, generating, completed, failed
    current_stage = db.Column(db.String(50))  # settings, outline, detailed_outline, content, export

    # 生成内容
    settings = db.Column(db.Text)  # AI生成的小说设定
    settings_check = db.Column(db.Text)  # AI检查结果
    outline = db.Column(db.Text)  # 大纲
    outline_check = db.Column(db.Text)  # 大纲检查结果

    # Token消耗统计
    total_tokens = db.Column(db.Integer, default=0)  # 总Token消耗
    prompt_tokens = db.Column(db.Integer, default=0)  # 输入Token
    completion_tokens = db.Column(db.Integer, default=0)  # 输出Token
    total_cost = db.Column(db.Float, default=0.0)  # 总费用（美元）

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # 关联
    chapters = db.relationship('Chapter', backref='novel', lazy='dynamic', cascade='all, delete-orphan')
    logs = db.relationship('GenerationLog', backref='novel', lazy='dynamic', cascade='all, delete-orphan')
    token_usages = db.relationship('TokenUsage', backref='novel', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'theme': self.theme,
            'background': self.background,
            'target_words': self.target_words,
            'target_chapters': self.target_chapters,
            'status': self.status,
            'current_stage': self.current_stage,
            'settings': self.settings,
            'settings_check': self.settings_check,
            'outline': self.outline,
            'outline_check': self.outline_check,
            'total_tokens': self.total_tokens,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_cost': self.total_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'chapter_count': self.chapters.count()
        }


class Chapter(db.Model):
    """章节表"""
    __tablename__ = 'chapters'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))

    # 细纲和内容
    detailed_outline = db.Column(db.Text)  # 细纲
    detailed_outline_check = db.Column(db.Text)  # 细纲检查
    content = db.Column(db.Text)  # 章节内容
    content_check = db.Column(db.Text)  # 内容检查

    word_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='pending')  # pending, generating, completed, failed

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'novel_id': self.novel_id,
            'chapter_number': self.chapter_number,
            'title': self.title,
            'detailed_outline': self.detailed_outline,
            'detailed_outline_check': self.detailed_outline_check,
            'content': self.content,
            'content_check': self.content_check,
            'word_count': self.word_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class GenerationLog(db.Model):
    """生成日志表"""
    __tablename__ = 'generation_logs'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id'), nullable=False)
    stage = db.Column(db.String(50))  # settings, outline, detailed_outline, content, check
    message = db.Column(db.Text)
    level = db.Column(db.String(20), default='info')  # info, warning, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'novel_id': self.novel_id,
            'stage': self.stage,
            'message': self.message,
            'level': self.level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AIConfig(db.Model):
    """AI配置表"""
    __tablename__ = 'ai_configs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    api_base = db.Column(db.String(500))
    api_key = db.Column(db.String(500))
    model_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=False)
    config_type = db.Column(db.String(20), default='generation')  # generation, check, both
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'api_base': self.api_base,
            'api_key': '***' if self.api_key else None,  # 隐藏API密钥
            'model_name': self.model_name,
            'is_active': self.is_active,
            'config_type': self.config_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TokenUsage(db.Model):
    """Token使用记录表"""
    __tablename__ = 'token_usages'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id'), nullable=False)
    stage = db.Column(db.String(50))  # settings, outline, detailed_outline, content, check
    operation = db.Column(db.String(100))  # 具体操作：generate_settings, check_settings等
    chapter_number = db.Column(db.Integer)  # 章节号（如果适用）

    # Token统计
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)

    # 费用统计
    cost = db.Column(db.Float, default=0.0)  # 本次调用费用

    # 模型信息
    model_name = db.Column(db.String(100))

    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Float)  # 调用耗时（秒）

    def to_dict(self):
        return {
            'id': self.id,
            'novel_id': self.novel_id,
            'stage': self.stage,
            'operation': self.operation,
            'chapter_number': self.chapter_number,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'cost': self.cost,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'duration': self.duration
        }
