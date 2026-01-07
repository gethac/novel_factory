import os
from models import Novel, Chapter


class NovelExporter:
    """小说导出器"""

    def __init__(self, export_dir='exports'):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)

    def export_to_txt(self, novel_id: int) -> str:
        """导出小说为TXT格式"""
        novel = Novel.query.get(novel_id)
        if not novel:
            raise ValueError(f"小说ID {novel_id} 不存在")

        if novel.status != 'completed':
            raise ValueError(f"小说尚未完成，当前状态: {novel.status}")

        # 构建文件内容
        content = self._build_txt_content(novel)

        # 生成文件名
        filename = f"{novel.title}_{novel.id}.txt"
        filepath = os.path.join(self.export_dir, filename)

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def _build_txt_content(self, novel: Novel) -> str:
        """构建TXT文件内容"""
        lines = []

        # 标题
        lines.append('=' * 60)
        lines.append(novel.title.center(56))
        lines.append('=' * 60)
        lines.append('')
        lines.append('')

        # 小说设定（可选）
        if novel.settings:
            lines.append('【小说设定】')
            lines.append('')
            lines.append(novel.settings)
            lines.append('')
            lines.append('=' * 60)
            lines.append('')
            lines.append('')

        # 章节内容
        chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.chapter_number).all()

        for chapter in chapters:
            # 章节标题
            lines.append(f"第{chapter.chapter_number}章 {chapter.title}")
            lines.append('')
            lines.append('')

            # 章节内容
            if chapter.content:
                lines.append(chapter.content)
            else:
                lines.append('[本章内容未生成]')

            lines.append('')
            lines.append('')
            lines.append('-' * 60)
            lines.append('')
            lines.append('')

        # 结尾
        lines.append('')
        lines.append('=' * 60)
        lines.append('全文完'.center(56))
        lines.append('=' * 60)

        return '\n'.join(lines)

    def get_export_path(self, novel_id: int) -> str:
        """获取导出文件路径"""
        novel = Novel.query.get(novel_id)
        if not novel:
            return None

        filename = f"{novel.title}_{novel.id}.txt"
        filepath = os.path.join(self.export_dir, filename)

        if os.path.exists(filepath):
            return filepath
        return None
