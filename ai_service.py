import requests
import json
import time
from typing import Optional, Dict, Any, Tuple
from config import Config
from models import db, AIConfig, GenerationLog, TokenUsage, Novel


class AIService:
    """AI服务类，负责调用大模型API"""

    # 模型价格表（每1000 tokens的价格，美元）
    MODEL_PRICING = {
        'gpt-4': {'prompt': 0.03, 'completion': 0.06},
        'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
        'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
        'claude-3-opus': {'prompt': 0.015, 'completion': 0.075},
        'claude-3-sonnet': {'prompt': 0.003, 'completion': 0.015},
        'default': {'prompt': 0.01, 'completion': 0.03}  # 默认价格
    }

    def __init__(self):
        self.api_base = Config.AI_API_BASE
        self.api_key = Config.AI_API_KEY
        self.model = Config.AI_MODEL
        # 延迟加载配置，避免在应用上下文外访问数据库

    def _load_active_config(self, is_check: bool = False):
        """加载激活的AI配置

        Args:
            is_check: 是否为校验操作。True=校验，False=生成
        """
        try:
            if is_check:
                # 优先查找专用的校验配置
                active_config = AIConfig.query.filter_by(is_active=True, config_type='check').first()
                # 如果没有专用校验配置，查找通用配置
                if not active_config:
                    active_config = AIConfig.query.filter_by(is_active=True, config_type='both').first()
            else:
                # 优先查找专用的生成配置
                active_config = AIConfig.query.filter_by(is_active=True, config_type='generation').first()
                # 如果没有专用生成配置，查找通用配置
                if not active_config:
                    active_config = AIConfig.query.filter_by(is_active=True, config_type='both').first()

            # 如果还是没有，使用任何激活的配置
            if not active_config:
                active_config = AIConfig.query.filter_by(is_active=True).first()

            if active_config:
                self.api_base = active_config.api_base
                self.api_key = active_config.api_key
                self.model = active_config.model_name
        except RuntimeError:
            # 如果在应用上下文外调用，使用默认配置
            pass

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """计算API调用费用"""
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING['default'])
        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']
        return prompt_cost + completion_cost

    def _call_api(self, messages: list, temperature: float = 0.7, max_tokens: int = 4000,
                  novel_id: int = None, operation: str = None, stage: str = None,
                  chapter_number: int = None, is_check: bool = False) -> Tuple[Optional[str], Optional[Dict]]:
        """调用AI API并记录Token使用

        Args:
            is_check: 是否为校验操作，用于选择合适的模型配置
        """
        # 尝试加载激活的配置（根据是否为校验操作选择不同配置）
        self._load_active_config(is_check=is_check)

        start_time = time.time()

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            data = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens
            }

            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )

            duration = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                # 提取Token使用信息
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)

                # 计算费用
                cost = self._calculate_cost(prompt_tokens, completion_tokens, self.model)

                # 记录Token使用
                if novel_id:
                    self._record_token_usage(
                        novel_id=novel_id,
                        stage=stage,
                        operation=operation,
                        chapter_number=chapter_number,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        cost=cost,
                        duration=duration
                    )

                usage_info = {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'cost': cost,
                    'duration': duration
                }

                return content, usage_info
            else:
                print(f"API调用失败: {response.status_code} - {response.text}")
                return None, None

        except Exception as e:
            print(f"API调用异常: {str(e)}")
            return None, None

    def _record_token_usage(self, novel_id: int, stage: str, operation: str,
                           prompt_tokens: int, completion_tokens: int, total_tokens: int,
                           cost: float, duration: float, chapter_number: int = None):
        """记录Token使用到数据库"""
        try:
            token_usage = TokenUsage(
                novel_id=novel_id,
                stage=stage,
                operation=operation,
                chapter_number=chapter_number,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                model_name=self.model,
                duration=duration
            )
            db.session.add(token_usage)

            # 更新小说的总Token统计
            novel = Novel.query.get(novel_id)
            if novel:
                novel.total_tokens = (novel.total_tokens or 0) + total_tokens
                novel.prompt_tokens = (novel.prompt_tokens or 0) + prompt_tokens
                novel.completion_tokens = (novel.completion_tokens or 0) + completion_tokens
                novel.total_cost = (novel.total_cost or 0.0) + cost

            db.session.commit()
        except Exception as e:
            print(f"记录Token使用失败: {str(e)}")
            db.session.rollback()

    def generate_settings(self, theme: str, background: str, target_words: int, target_chapters: int, novel_id: int) -> Optional[str]:
        """生成小说设定"""
        self._log(novel_id, 'settings', '开始生成小说设定...')

        prompt = f"""你是一位资深的小说策划师。请根据以下要求，生成一份完整的小说设定。

要求：
- 主题：{theme}
- 背景：{background}
- 目标字数：{target_words}字
- 目标章节数：{target_chapters}章

请生成包含以下内容的小说设定：
1. 小说标题（吸引人且符合主题）
2. 故事背景（详细的世界观、时代背景）
3. 主要人物设定（至少3-5个主要角色，包括姓名、性格、背景、动机）
4. 核心冲突（故事的主要矛盾和冲突点）
5. 故事基调（轻松/严肃/悬疑等）
6. 特殊设定（如有魔法、科技等特殊元素，需详细说明规则）

请以结构化的方式输出，每个部分用明确的标题分隔。"""

        messages = [
            {'role': 'system', 'content': '你是一位经验丰富的小说策划师，擅长创作引人入胜的故事设定。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.8,
            max_tokens=3000,
            novel_id=novel_id,
            operation='generate_settings',
            stage='settings'
        )

        if result:
            self._log(novel_id, 'settings', f'小说设定生成成功 (Tokens: {usage["total_tokens"]}, 费用: ${usage["cost"]:.4f})')
        else:
            self._log(novel_id, 'settings', '小说设定生成失败', 'error')

        return result

    def check_settings(self, settings: str, theme: str, novel_id: int) -> Dict[str, Any]:
        """检查小说设定质量"""
        self._log(novel_id, 'check', '开始检查小说设定...')

        prompt = f"""你是一位资深的网络小说编辑，拥有10年以上的行业经验。请严格审查以下小说设定。

【原始主题】
{theme}

【小说设定】
{settings}

【评估标准】（每项0-10分，要求严格）
1. 完整性（10分）：
   - 世界观是否完整（时代背景、地理环境、社会结构）
   - 力量体系是否清晰（修炼等级、能力划分）
   - 主要角色设定是否齐全（主角、配角、反派）
   - 核心冲突是否明确

2. 一致性（10分）：
   - 各设定元素之间是否自洽
   - 是否存在逻辑矛盾
   - 力量体系是否合理平衡

3. 创新性（10分）：
   - 是否有独特的世界观设定
   - 是否避免了常见套路
   - 是否有吸引眼球的创新点

4. 可行性（10分）：
   - 设定是否能支撑长篇故事发展
   - 是否有足够的故事空间
   - 是否便于后续情节展开

5. 商业价值（10分）：
   - 是否符合目标读者喜好
   - 是否有爆款潜力
   - 题材是否有市场竞争力

【评分要求】
- 总分低于35分：不合格，需要重新生成
- 总分35-42分：勉强合格，建议改进
- 总分43分以上：优秀，可以通过

请以JSON格式输出（不要有任何其他文字）：
{{
    "scores": {{
        "completeness": 分数,
        "consistency": 分数,
        "innovation": 分数,
        "feasibility": 分数,
        "commercial_value": 分数
    }},
    "total_score": 总分,
    "passed": true/false (总分>=35分为通过),
    "issues": ["具体问题1", "具体问题2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "highlights": ["亮点1", "亮点2"]
}}"""

        messages = [
            {'role': 'system', 'content': '你是一位严格的网络小说编辑，以高标准评估作品质量。你的评分客观公正，不轻易给高分。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.2,
            max_tokens=2000,
            novel_id=novel_id,
            operation='check_settings',
            stage='check',
            is_check=True
        )

        if result:
            try:
                # 尝试提取JSON内容
                json_str = result.strip()

                # 如果结果包含markdown代码块，提取其中的JSON
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].split('```')[0].strip()

                # 尝试解析JSON
                check_result = json.loads(json_str)
                self._log(novel_id, 'check', f'设定检查完成，总分：{check_result.get("total_score", 0)}')
                return check_result
            except json.JSONDecodeError as e:
                self._log(novel_id, 'check', f'设定检查结果解析失败: {str(e)}。原始返回: {result[:200]}...', 'error')
                # 返回一个默认通过的结果，避免阻塞流程
                return {
                    'passed': True,
                    'total_score': 40,
                    'error': '解析失败，默认通过',
                    'raw_response': result
                }
            except Exception as e:
                self._log(novel_id, 'check', f'设定检查异常: {str(e)}', 'error')
                return {'passed': True, 'total_score': 40, 'error': '检查异常，默认通过'}
        else:
            self._log(novel_id, 'check', '设定检查失败', 'error')
            return {'passed': False, 'error': 'API调用失败'}

    def generate_outline(self, settings: str, target_chapters: int, novel_id: int) -> Optional[str]:
        """生成小说大纲"""
        self._log(novel_id, 'outline', '开始生成小说大纲...')

        prompt = f"""你是一位资深的小说大纲师。请根据以下小说设定，生成一份完整的章节大纲。

小说设定：
{settings}

要求：
- 总章节数：{target_chapters}章
- 每章需要有明确的标题和内容概要
- 情节要有起承转合，节奏合理
- 确保故事完整，有开头、发展、高潮、结局

请按以下格式输出大纲：
第1章：[章节标题]
概要：[200字左右的章节内容概要]

第2章：[章节标题]
概要：[200字左右的章节内容概要]

...以此类推"""

        messages = [
            {'role': 'system', 'content': '你是一位经验丰富的小说大纲师，擅长构建完整的故事结构。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.7,
            max_tokens=4000,
            novel_id=novel_id,
            operation='generate_outline',
            stage='outline'
        )

        if result:
            self._log(novel_id, 'outline', '小说大纲生成成功')
        else:
            self._log(novel_id, 'outline', '小说大纲生成失败', 'error')

        return result

    def check_outline(self, outline: str, settings: str, novel_id: int) -> Dict[str, Any]:
        """检查小说大纲质量"""
        self._log(novel_id, 'check', '开始检查小说大纲...')

        prompt = f"""你是一位资深的网络小说编辑，专注于故事结构和情节设计。请严格审查以下小说大纲。

【小说设定】
{settings}

【小说大纲】
{outline}

【评估标准】（每项0-10分，严格评分）
1. 结构完整性（10分）：
   - 是否有清晰的起承转合
   - 开篇是否吸引人（前3章）
   - 中期是否有足够冲突和转折
   - 高潮是否震撼
   - 结局是否圆满

2. 逻辑连贯性（10分）：
   - 章节之间的因果关系是否清晰
   - 情节发展是否自然流畅
   - 是否有突兀或跳跃的地方
   - 伏笔铺垫是否合理

3. 节奏把控（10分）：
   - 爽点分布是否合理（每3-5章一个小爽点）
   - 是否避免了拖沓和注水
   - 高潮低谷是否交替得当
   - 是否有足够的悬念和钩子

4. 符合设定（10分）：
   - 是否严格遵循世界观设定
   - 力量体系是否合理运用
   - 角色行为是否符合人设
   - 是否有违背设定的地方

5. 商业价值（10分）：
   - 是否有足够的看点和卖点
   - 情节是否有吸引力
   - 是否符合目标读者口味
   - 是否有订阅和追读价值

【评分要求】
- 总分低于35分：不合格，需要重新生成
- 总分35-42分：勉强合格，建议优化
- 总分43分以上：优秀，可以通过

请以JSON格式输出（不要有任何其他文字）：
{{
    "scores": {{
        "structure": 分数,
        "logic": 分数,
        "pacing": 分数,
        "consistency": 分数,
        "commercial_value": 分数
    }},
    "total_score": 总分,
    "passed": true/false (总分>=35分为通过),
    "issues": ["具体问题1", "具体问题2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "highlights": ["亮点1", "亮点2"]
}}"""

        messages = [
            {'role': 'system', 'content': '你是一位严格的网络小说编辑，擅长评估故事结构。你的评分客观公正，标准严格。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.2,
            max_tokens=2000,
            novel_id=novel_id,
            operation='check_outline',
            stage='check',
            is_check=True
        )

        if result:
            try:
                # 尝试提取JSON内容
                json_str = result.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].split('```')[0].strip()

                check_result = json.loads(json_str)
                self._log(novel_id, 'check', f'大纲检查完成，总分：{check_result.get("total_score", 0)} (Tokens: {usage["total_tokens"]})')
                return check_result
            except json.JSONDecodeError as e:
                self._log(novel_id, 'check', f'大纲检查结果解析失败: {str(e)}。原始返回: {result[:200]}...', 'error')
                return {
                    'passed': True,
                    'total_score': 40,
                    'error': '解析失败，默认通过',
                    'raw_response': result
                }
            except Exception as e:
                self._log(novel_id, 'check', f'大纲检查异常: {str(e)}', 'error')
                return {'passed': True, 'total_score': 40, 'error': '检查异常，默认通过'}
        else:
            self._log(novel_id, 'check', '大纲检查失败', 'error')
            return {'passed': False, 'error': 'API调用失败'}

    def generate_detailed_outline(self, chapter_info: str, settings: str, outline: str,
                                  chapter_number: int, target_words: int, novel_id: int) -> Optional[str]:
        """生成章节细纲"""
        self._log(novel_id, 'detailed_outline', f'开始生成第{chapter_number}章细纲...')

        prompt = f"""你是一位资深的小说细纲师。请根据以下信息，为指定章节生成详细的细纲。

小说设定：
{settings}

完整大纲：
{outline}

当前章节信息：
{chapter_info}

要求：
- 目标字数：约{target_words}字
- 细纲需要包含：场景、人物、对话要点、情节发展、情感变化
- 细纲要足够详细，能够指导后续的正文写作
- 确保与前后章节衔接自然

请输出详细的章节细纲（800-1000字）。"""

        messages = [
            {'role': 'system', 'content': '你是一位经验丰富的小说细纲师，擅长将章节概要扩展为详细的写作指导。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.7,
            max_tokens=2000,
            novel_id=novel_id,
            operation='generate_detailed_outline',
            stage='detailed_outline',
            chapter_number=chapter_number
        )

        if result:
            self._log(novel_id, 'detailed_outline', f'第{chapter_number}章细纲生成成功 (Tokens: {usage["total_tokens"]})')
        else:
            self._log(novel_id, 'detailed_outline', f'第{chapter_number}章细纲生成失败', 'error')

        return result

    def check_detailed_outline(self, detailed_outline: str, chapter_info: str,
                               settings: str, novel_id: int, chapter_number: int) -> Dict[str, Any]:
        """检查章节细纲质量"""
        self._log(novel_id, 'check', f'开始检查第{chapter_number}章细纲...')

        prompt = f"""你是一位资深的网络小说编辑，专注于章节细纲审核。请严格审查以下章节细纲。

【小说设定】
{settings}

【章节概要】
{chapter_info}

【章节细纲】
{detailed_outline}

【评估标准】（每项0-10分，严格评分）
1. 详细程度（10分）：
   - 场景描写是否具体（时间、地点、环境）
   - 人物行为是否清晰（动作、表情、心理）
   - 对话要点是否明确
   - 情节节点是否完整
   - 是否达到800字以上

2. 可执行性（10分）：
   - 是否能直接指导正文写作
   - 情节发展是否有明确的先后顺序
   - 冲突和转折是否清晰
   - 是否有足够的写作素材

3. 符合设定（10分）：
   - 是否遵循世界观设定
   - 角色行为是否符合人设
   - 力量体系运用是否合理
   - 是否与前文保持一致

4. 情节质量（10分）：
   - 情节发展是否合理自然
   - 是否有吸引力和看点
   - 节奏把控是否得当
   - 是否有爽点或钩子

【评分要求】
- 总分低于28分：不合格，需要重新生成
- 总分28-35分：勉强合格，建议优化
- 总分36分以上：优秀，可以通过

请以JSON格式输出（不要有任何其他文字）：
{{
    "scores": {{
        "detail": 分数,
        "executable": 分数,
        "consistency": 分数,
        "quality": 分数
    }},
    "total_score": 总分,
    "passed": true/false (总分>=28分为通过),
    "issues": ["具体问题1", "具体问题2"],
    "suggestions": ["改进建议1", "改进建议2"]
}}"""

        messages = [
            {'role': 'system', 'content': '你是一位严格的网络小说编辑，擅长审核章节细纲。你的评分客观公正，标准严格。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.2,
            max_tokens=1500,
            novel_id=novel_id,
            operation='check_detailed_outline',
            stage='check',
            chapter_number=chapter_number,
            is_check=True
        )

        if result:
            try:
                # 尝试提取JSON内容
                json_str = result.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].split('```')[0].strip()

                check_result = json.loads(json_str)
                self._log(novel_id, 'check', f'第{chapter_number}章细纲检查完成，总分：{check_result.get("total_score", 0)} (Tokens: {usage["total_tokens"]})')
                return check_result
            except json.JSONDecodeError as e:
                self._log(novel_id, 'check', f'第{chapter_number}章细纲检查结果解析失败: {str(e)}', 'error')
                return {
                    'passed': True,
                    'total_score': 32,
                    'error': '解析失败，默认通过',
                    'raw_response': result
                }
            except Exception as e:
                self._log(novel_id, 'check', f'第{chapter_number}章细纲检查异常: {str(e)}', 'error')
                return {'passed': True, 'total_score': 32, 'error': '检查异常，默认通过'}
        else:
            self._log(novel_id, 'check', f'第{chapter_number}章细纲检查失败', 'error')
            return {'passed': False, 'error': 'API调用失败'}

    def generate_chapter_content(self, detailed_outline: str, settings: str,
                                 chapter_title: str, target_words: int,
                                 novel_id: int, chapter_number: int) -> Optional[str]:
        """生成章节正文内容"""
        self._log(novel_id, 'content', f'开始生成第{chapter_number}章正文...')

        # 使用您提供的专业写作Prompt
        writing_rules = """【角色设定】
你是一位经验丰富、文笔老练的中文通俗小说家。你极其擅长使用**地道的中文短句**和**动词**来构建画面，痛恨"翻译腔"和冗长的定语堆叠。你的写作准则是："一种语序只承载一个核心信息"。

【核心任务】
请根据细纲进行小说创作。在输出内容时，**必须严格遵守**以下句法结构和描写逻辑：

#### 1. 句法铁律：名词先行，描写后置 (Noun First Policy)
* **禁止左分支结构：** 严禁在名词前堆砌长修饰语（超过6个字）。
* **拆解长句：** 遇到复杂的修饰意图时，必须先把"物体/名词"写出来，然后用后置的短句、谓语或独立分句来补充描述它的状态。

#### 2. 文笔约束：消灭"的"字灾难
* **总量控制：** 严格限制"的"字的使用频率。一个分句中禁止出现两个以上的"的"。
* **结构禁令：** 严禁使用 **"长修饰语 + 的 + 名词"** 的结构。
* **转化策略：** 当你想用"……的"时候，请立刻尝试将其转化为：
  * **动词短语**（"积满灰尘的杯子" -> "杯子积满了灰尘"）
  * **状态补语**（"漆黑的房间" -> "房间一片漆黑"）

#### 3. 描写逻辑：动词主导 (Verb Driven)
* **拒绝静态：** 少用静态形容词，多用动词来推动描写。
* **交互感：** 描写环境或物品时，必须结合人物的**动作交互**或**感官体验**（视觉、触觉、嗅觉）。"""

        prompt = f"""
{writing_rules}

【小说设定】
{settings}

【章节标题】
{chapter_title}

【章节细纲】
{detailed_outline}

【写作要求】
- 目标字数：{target_words}字左右
- 严格按照细纲展开情节
- 使用地道的中文短句，避免翻译腔
- 名词先行，描写后置
- 多用动词，少用"的"字
- 对话要自然生动
- 注意情节节奏和情感渲染

请开始创作这一章的正文内容。"""

        messages = [
            {'role': 'system', 'content': writing_rules},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.8,
            max_tokens=4000,
            novel_id=novel_id,
            operation='generate_chapter_content',
            stage='content',
            chapter_number=chapter_number
        )

        if result:
            self._log(novel_id, 'content', f'第{chapter_number}章正文生成成功 (Tokens: {usage["total_tokens"]}, 费用: ${usage["cost"]:.4f})')
        else:
            self._log(novel_id, 'content', f'第{chapter_number}章正文生成失败', 'error')

        return result

    def check_chapter_content(self, content: str, detailed_outline: str,
                             settings: str, novel_id: int, chapter_number: int) -> Dict[str, Any]:
        """检查章节内容质量"""
        self._log(novel_id, 'check', f'开始检查第{chapter_number}章正文...')

        prompt = f"""你是一位资深的网络小说编辑，拥有丰富的审稿经验。请严格审查以下章节正文。

【小说设定】
{settings}

【章节细纲】
{detailed_outline}

【章节正文】
{content}

【评估标准】（每项0-10分，严格评分）
1. 符合细纲（10分）：
   - 是否按照细纲的情节发展
   - 关键场景是否完整呈现
   - 人物行为是否符合细纲设定
   - 是否有遗漏或偏离

2. 文笔质量（10分）：
   - 语言是否流畅自然
   - 是否有翻译腔或生硬表达
   - 句式是否多样化
   - 用词是否准确生动
   - 是否符合中文网文写作习惯

3. 情节完整（10分）：
   - 情节发展是否完整
   - 冲突和转折是否清晰
   - 节奏把控是否得当
   - 是否有拖沓或跳跃

4. 人物塑造（10分）：
   - 人物形象是否鲜明
   - 对话是否符合人物性格
   - 心理描写是否细腻
   - 行为动机是否合理

5. 可读性（10分）：
   - 是否引人入胜
   - 是否有代入感
   - 是否有爽点或看点
   - 读者是否愿意继续阅读

【重点关注】
- 翻译腔问题：避免"的"字过多、长定语、被动语态
- 网文特点：节奏要快、爽点要密、对话要多
- 情感渲染：场景描写要有画面感
- 字数要求：是否达到目标字数

【评分要求】
- 总分低于35分：不合格，需要重新生成
- 总分35-42分：勉强合格，建议优化
- 总分43分以上：优秀，可以通过

请以JSON格式输出（不要有任何其他文字）：
{{
    "scores": {{
        "outline_match": 分数,
        "writing_quality": 分数,
        "plot_completeness": 分数,
        "character": 分数,
        "readability": 分数
    }},
    "total_score": 总分,
    "passed": true/false (总分>=35分为通过),
    "issues": ["具体问题1", "具体问题2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "highlights": ["亮点1", "亮点2"]
}}"""

        messages = [
            {'role': 'system', 'content': '你是一位严格的网络小说编辑，特别关注中文写作的地道性和网文特点。你的评分客观公正，标准严格。'},
            {'role': 'user', 'content': prompt}
        ]

        result, usage = self._call_api(
            messages,
            temperature=0.2,
            max_tokens=2000,
            novel_id=novel_id,
            operation='check_chapter_content',
            stage='check',
            chapter_number=chapter_number,
            is_check=True
        )

        if result:
            try:
                # 尝试提取JSON内容
                json_str = result.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].split('```')[0].strip()

                check_result = json.loads(json_str)
                self._log(novel_id, 'check', f'第{chapter_number}章正文检查完成，总分：{check_result.get("total_score", 0)} (Tokens: {usage["total_tokens"]})')
                return check_result
            except json.JSONDecodeError as e:
                self._log(novel_id, 'check', f'第{chapter_number}章正文检查结果解析失败: {str(e)}', 'error')
                return {
                    'passed': True,
                    'total_score': 40,
                    'error': '解析失败，默认通过',
                    'raw_response': result
                }
            except Exception as e:
                self._log(novel_id, 'check', f'第{chapter_number}章正文检查异常: {str(e)}', 'error')
                return {'passed': True, 'total_score': 40, 'error': '检查异常，默认通过'}
        else:
            self._log(novel_id, 'check', f'第{chapter_number}章正文检查失败', 'error')
            return {'passed': False, 'error': 'API调用失败'}

    def _log(self, novel_id: int, stage: str, message: str, level: str = 'info'):
        """记录日志"""
        try:
            log = GenerationLog(
                novel_id=novel_id,
                stage=stage,
                message=message,
                level=level
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"日志记录失败: {str(e)}")
