"""
数据库迁移脚本：为 AIConfig 表添加 config_type 字段
"""
import sqlite3
import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate():
    # 数据库文件路径
    db_path = os.path.join('instance', 'novels.db')

    if not os.path.exists(db_path):
        print("数据库文件不存在，无需迁移")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查 config_type 列是否已存在
        cursor.execute("PRAGMA table_info(ai_configs)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'config_type' in columns:
            print("config_type 字段已存在，无需迁移")
        else:
            print("正在添加 config_type 字段...")

            # 添加新列，默认值为 'both'
            cursor.execute("""
                ALTER TABLE ai_configs
                ADD COLUMN config_type VARCHAR(20) DEFAULT 'both'
            """)

            # 更新所有现有记录的 config_type 为 'both'
            cursor.execute("""
                UPDATE ai_configs
                SET config_type = 'both'
                WHERE config_type IS NULL
            """)

            conn.commit()
            print("成功添加 config_type 字段并设置默认值")

            # 显示更新后的记录数
            cursor.execute("SELECT COUNT(*) FROM ai_configs")
            count = cursor.fetchone()[0]
            print(f"已更新 {count} 条配置记录")

    except sqlite3.Error as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("数据库迁移：添加 config_type 字段")
    print("="*60 + "\n")
    migrate()
    print("\n" + "="*60)
    print("迁移完成")
    print("="*60 + "\n")

