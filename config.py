import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///novels.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI模型配置
    AI_API_BASE = os.getenv('AI_API_BASE', 'https://api.openai.com/v1')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4')

    # 小说生成配置
    DEFAULT_CHAPTER_LENGTH = 3000  # 每章默认字数
    MAX_RETRIES = 3  # AI生成失败最大重试次数

    # 导出配置
    EXPORT_DIR = 'exports'

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        os.makedirs(Config.EXPORT_DIR, exist_ok=True)
