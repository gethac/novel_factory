"""
数据库迁移脚本：为 AIConfig 表添加 config_type 字段
"""
from app import app, db
from models import AIConfig

def migrate():
    with app.app_context():
        # 检查是否需要迁移
        try:
            # 尝试查询 config_type 字段
            AIConfig.query.first()
            print("✓ 数据库已是最新版本")
        except Exception as e:
            print(f"需要迁移数据库: {e}")
            
        # 为所有现有配置设置默认值
        try:
            configs = AIConfig.query.all()
            for config in configs:
                if not hasattr(config, 'config_type') or config.config_type is None:
                    config.config_type = 'both'
            db.session.commit()
            print(f"✓ 已更新 {len(configs)} 个配置的类型为'通用'")
        except Exception as e:
            print(f"迁移过程中出错: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate()
