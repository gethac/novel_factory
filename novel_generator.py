import time
from datetime import datetime
from models import db, Novel, Chapter
from ai_service import AIService
from config import Config


class NovelGenerator:
    """小说生成器 - 完全自动化的小说生产流程"""

    def __init__(self):
        self.ai_service = AIService()
        self.max_retries = Config.MAX_RETRIES

    def _check_if_paused(self, novel: Novel) -> bool:
        """检查是否被暂停"""
        # 刷新数据库状态
        db.session.refresh(novel)
        if novel.is_paused:
            novel.status = 'paused'
            db.session.commit()
            print(f"小说 ID:{novel.id} 已暂停")
            return True
        return False

    def generate_novel(self, novel_id: int):
        """完整的小说生成流程"""
        novel = Novel.query.get(novel_id)
        if not novel:
            return False

        try:
            # 更新状态
            novel.status = 'generating'
            novel.is_paused = False
            db.session.commit()

            # 步骤1: 生成并检查小说设定
            if self._check_if_paused(novel):
                return False
            if not self._generate_and_check_settings(novel):
                novel.status = 'failed'
                db.session.commit()
                return False

            # 步骤2: 生成并检查大纲
            if self._check_if_paused(novel):
                return False
            if not self._generate_and_check_outline(novel):
                novel.status = 'failed'
                db.session.commit()
                return False

            # 步骤3: 为每章生成细纲和内容
            if self._check_if_paused(novel):
                return False
            if not self._generate_chapters(novel):
                novel.status = 'failed'
                db.session.commit()
                return False

            # 完成
            novel.status = 'completed'
            novel.completed_at = datetime.utcnow()
            db.session.commit()

            return True

        except Exception as e:
            print(f"小说生成异常: {str(e)}")
            novel.status = 'failed'
            db.session.commit()
            return False

    def _generate_and_check_settings(self, novel: Novel) -> bool:
        """生成并检查小说设定"""
        novel.current_stage = 'settings'
        db.session.commit()

        for attempt in range(self.max_retries):
            # 生成设定
            settings = self.ai_service.generate_settings(
                theme=novel.theme,
                background=novel.background,
                target_words=novel.target_words,
                target_chapters=novel.target_chapters,
                novel_id=novel.id
            )

            if not settings:
                continue

            novel.settings = settings
            db.session.commit()

            # AI检查设定
            check_result = self.ai_service.check_settings(
                settings=settings,
                theme=novel.theme,
                novel_id=novel.id
            )

            novel.settings_check = str(check_result)
            db.session.commit()

            # 如果通过检查，返回成功
            if check_result.get('passed', False):
                return True

            # 如果未通过，记录问题并重试
            print(f"设定检查未通过 (尝试 {attempt + 1}/{self.max_retries})")
            time.sleep(2)

        return False

    def _generate_and_check_outline(self, novel: Novel) -> bool:
        """生成并检查大纲"""
        novel.current_stage = 'outline'
        db.session.commit()

        for attempt in range(self.max_retries):
            # 生成大纲
            outline = self.ai_service.generate_outline(
                settings=novel.settings,
                target_chapters=novel.target_chapters,
                novel_id=novel.id
            )

            if not outline:
                continue

            novel.outline = outline
            db.session.commit()

            # AI检查大纲
            check_result = self.ai_service.check_outline(
                outline=outline,
                settings=novel.settings,
                novel_id=novel.id
            )

            novel.outline_check = str(check_result)
            db.session.commit()

            if check_result.get('passed', False):
                return True

            print(f"大纲检查未通过 (尝试 {attempt + 1}/{self.max_retries})")
            time.sleep(2)

        return False

    def _generate_chapters(self, novel: Novel) -> bool:
        """生成所有章节"""
        novel.current_stage = 'content'
        db.session.commit()

        # 解析大纲，创建章节记录
        chapters = self._parse_outline_and_create_chapters(novel)

        if not chapters:
            return False

        # 为每章生成内容
        for chapter in chapters:
            # 检查是否暂停
            if self._check_if_paused(novel):
                return False
            if not self._generate_chapter(novel, chapter):
                return False

        return True

    def _parse_outline_and_create_chapters(self, novel: Novel):
        """解析大纲并创建章节记录"""
        outline_lines = novel.outline.split('\n')
        chapters = []
        current_chapter = None
        chapter_number = 0

        for line in outline_lines:
            line = line.strip()
            if not line:
                continue

            # 检测章节标题
            if line.startswith('第') and '章' in line:
                if current_chapter:
                    chapters.append(current_chapter)

                chapter_number += 1
                # 提取标题
                title = line.split('：', 1)[-1] if '：' in line else line
                current_chapter = {
                    'number': chapter_number,
                    'title': title,
                    'outline': line + '\n'
                }
            elif current_chapter:
                current_chapter['outline'] += line + '\n'

        if current_chapter:
            chapters.append(current_chapter)

        # 创建数据库记录
        chapter_objects = []
        for ch in chapters:
            chapter = Chapter(
                novel_id=novel.id,
                chapter_number=ch['number'],
                title=ch['title'],
                status='pending'
            )
            db.session.add(chapter)
            chapter_objects.append(chapter)

        db.session.commit()
        return chapter_objects

    def _generate_chapter(self, novel: Novel, chapter: Chapter) -> bool:
        """生成单个章节的细纲和内容"""
        chapter.status = 'generating'
        db.session.commit()

        # 获取章节信息
        chapter_info = self._get_chapter_info_from_outline(novel.outline, chapter.chapter_number)

        # 步骤1: 生成并检查细纲
        if not self._generate_and_check_detailed_outline(novel, chapter, chapter_info):
            chapter.status = 'failed'
            db.session.commit()
            return False

        # 步骤2: 生成并检查正文
        if not self._generate_and_check_content(novel, chapter):
            chapter.status = 'failed'
            db.session.commit()
            return False

        chapter.status = 'completed'
        db.session.commit()
        return True

    def _generate_and_check_detailed_outline(self, novel: Novel, chapter: Chapter, chapter_info: str) -> bool:
        """生成并检查章节细纲"""
        words_per_chapter = novel.target_words // novel.target_chapters

        for attempt in range(self.max_retries):
            # 生成细纲
            detailed_outline = self.ai_service.generate_detailed_outline(
                chapter_info=chapter_info,
                settings=novel.settings,
                outline=novel.outline,
                chapter_number=chapter.chapter_number,
                target_words=words_per_chapter,
                novel_id=novel.id
            )

            if not detailed_outline:
                continue

            chapter.detailed_outline = detailed_outline
            db.session.commit()

            # AI检查细纲
            check_result = self.ai_service.check_detailed_outline(
                detailed_outline=detailed_outline,
                chapter_info=chapter_info,
                settings=novel.settings,
                novel_id=novel.id,
                chapter_number=chapter.chapter_number
            )

            chapter.detailed_outline_check = str(check_result)
            db.session.commit()

            if check_result.get('passed', False):
                return True

            print(f"第{chapter.chapter_number}章细纲检查未通过 (尝试 {attempt + 1}/{self.max_retries})")
            time.sleep(2)

        return False

    def _generate_and_check_content(self, novel: Novel, chapter: Chapter) -> bool:
        """生成并检查章节内容"""
        words_per_chapter = novel.target_words // novel.target_chapters

        for attempt in range(self.max_retries):
            # 生成正文
            content = self.ai_service.generate_chapter_content(
                detailed_outline=chapter.detailed_outline,
                settings=novel.settings,
                chapter_title=chapter.title,
                target_words=words_per_chapter,
                novel_id=novel.id,
                chapter_number=chapter.chapter_number
            )

            if not content:
                continue

            chapter.content = content
            chapter.word_count = len(content)
            db.session.commit()

            # AI检查内容
            check_result = self.ai_service.check_chapter_content(
                content=content,
                detailed_outline=chapter.detailed_outline,
                settings=novel.settings,
                novel_id=novel.id,
                chapter_number=chapter.chapter_number
            )

            chapter.content_check = str(check_result)
            db.session.commit()

            if check_result.get('passed', False):
                return True

            print(f"第{chapter.chapter_number}章内容检查未通过 (尝试 {attempt + 1}/{self.max_retries})")
            time.sleep(2)

        return False

    def _get_chapter_info_from_outline(self, outline: str, chapter_number: int) -> str:
        """从大纲中提取指定章节的信息"""
        lines = outline.split('\n')
        chapter_lines = []
        capturing = False

        for line in lines:
            if f'第{chapter_number}章' in line:
                capturing = True
                chapter_lines.append(line)
            elif capturing:
                if line.strip().startswith('第') and '章' in line:
                    break
                chapter_lines.append(line)

        return '\n'.join(chapter_lines)
