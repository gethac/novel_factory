"""
数据库迁移脚本：为 Novel 表添加 is_paused 字段
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
        # 检查 is_paused 列是否已存在
        cursor.execute("PRAGMA table_info(novels)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_paused' in columns:
            print("is_paused 字段已存在，无需迁移")
        else:
            print("正在添加 is_paused 字段...")

            # 添加新列，默认值为 0 (False)
            cursor.execute("""
                ALTER TABLE novels
                ADD COLUMN is_paused BOOLEAN DEFAULT 0
            """)

            # 更新所有现有记录的 is_paused 为 False
            cursor.execute("""
                UPDATE novels
                SET is_paused = 0
                WHERE is_paused IS NULL
            """)

            conn.commit()
            print("成功添加 is_paused 字段并设置默认值")

            # 显示更新后的记录数
            cursor.execute("SELECT COUNT(*) FROM novels")
            count = cursor.fetchone()[0]
            print(f"已更新 {count} 条小说记录")

    except sqlite3.Error as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("数据库迁移：添加 is_paused 字段")
    print("="*60 + "\n")
    migrate()
    print("\n" + "="*60)
    print("迁移完成")
    print("="*60 + "\n")
