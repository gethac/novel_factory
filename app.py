import threading
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, Novel, Chapter, GenerationLog, AIConfig, TokenUsage
from novel_generator import NovelGenerator
from exporter import NovelExporter
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

CORS(app)
db.init_app(app)

# 初始化服务
novel_generator = NovelGenerator()
exporter = NovelExporter(Config.EXPORT_DIR)


# ==================== 前端页面 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


# ==================== 小说管理 API ====================

@app.route('/api/novels', methods=['GET'])
def get_novels():
    """获取所有小说列表"""
    novels = Novel.query.order_by(Novel.created_at.desc()).all()
    return jsonify([novel.to_dict() for novel in novels])


@app.route('/api/novels/<int:novel_id>', methods=['GET'])
def get_novel(novel_id):
    """获取单个小说详情"""
    novel = Novel.query.get_or_404(novel_id)
    return jsonify(novel.to_dict())


@app.route('/api/novels', methods=['POST'])
def create_novel():
    """创建新小说任务"""
    data = request.json

    novel = Novel(
        title=data.get('title', '未命名小说'),
        theme=data.get('theme', ''),
        background=data.get('background', ''),
        target_words=data.get('target_words', 30000),
        target_chapters=data.get('target_chapters', 10),
        status='pending'
    )

    db.session.add(novel)
    db.session.commit()

    return jsonify(novel.to_dict()), 201


@app.route('/api/novels/<int:novel_id>/start', methods=['POST'])
def start_generation(novel_id):
    """启动小说生成（异步）"""
    novel = Novel.query.get_or_404(novel_id)

    if novel.status == 'generating':
        return jsonify({'error': '小说正在生成中'}), 400

    # 在后台线程中生成小说
    def generate():
        with app.app_context():
            novel_generator.generate_novel(novel_id)

    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()

    return jsonify({'message': '小说生成已启动', 'novel_id': novel_id})


@app.route('/api/novels/<int:novel_id>/pause', methods=['POST'])
def pause_generation(novel_id):
    """暂停小说生成"""
    novel = Novel.query.get_or_404(novel_id)

    if novel.status != 'generating':
        return jsonify({'error': '小说未在生成中'}), 400

    novel.is_paused = True
    db.session.commit()

    return jsonify({'message': '已发送暂停信号，生成将在当前步骤完成后暂停'})


@app.route('/api/novels/<int:novel_id>/resume', methods=['POST'])
def resume_generation(novel_id):
    """恢复小说生成"""
    novel = Novel.query.get_or_404(novel_id)

    if novel.status not in ['paused', 'generating']:
        return jsonify({'error': '小说未处于暂停状态'}), 400

    novel.is_paused = False
    novel.status = 'generating'
    db.session.commit()

    # 在后台线程中继续生成
    def generate():
        with app.app_context():
            novel_generator.generate_novel(novel_id)

    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()

    return jsonify({'message': '小说生成已恢复'})


@app.route('/api/novels/<int:novel_id>/regenerate/<content_type>', methods=['POST'])
def regenerate_content(novel_id, content_type):
    """重新生成指定内容

    content_type: settings, outline, chapter_outline, chapter_content
    """
    novel = Novel.query.get_or_404(novel_id)
    data = request.json or {}
    custom_prompt = data.get('custom_prompt', '')
    chapter_id = data.get('chapter_id')

    try:
        if content_type == 'settings':
            # 重新生成小说设定
            if custom_prompt:
                # 使用自定义提示词
                result = novel_generator.ai_service.generate_settings_with_custom_prompt(
                    theme=novel.theme,
                    background=novel.background,
                    target_words=novel.target_words,
                    target_chapters=novel.target_chapters,
                    custom_prompt=custom_prompt,
                    novel_id=novel.id
                )
            else:
                # 使用默认提示词
                result = novel_generator.ai_service.generate_settings(
                    theme=novel.theme,
                    background=novel.background,
                    target_words=novel.target_words,
                    target_chapters=novel.target_chapters,
                    novel_id=novel.id
                )

            if result:
                novel.settings = result
                db.session.commit()
                return jsonify({'message': '设定重新生成成功', 'content': result})
            else:
                return jsonify({'error': '设定生成失败'}), 500

        elif content_type == 'outline':
            # 重新生成大纲
            if not novel.settings:
                return jsonify({'error': '请先生成小说设定'}), 400

            if custom_prompt:
                result = novel_generator.ai_service.generate_outline_with_custom_prompt(
                    settings=novel.settings,
                    target_chapters=novel.target_chapters,
                    custom_prompt=custom_prompt,
                    novel_id=novel.id
                )
            else:
                result = novel_generator.ai_service.generate_outline(
                    settings=novel.settings,
                    target_chapters=novel.target_chapters,
                    novel_id=novel.id
                )

            if result:
                novel.outline = result
                db.session.commit()
                return jsonify({'message': '大纲重新生成成功', 'content': result})
            else:
                return jsonify({'error': '大纲生成失败'}), 500

        elif content_type == 'chapter_outline':
            # 重新生成章节细纲
            if not chapter_id:
                return jsonify({'error': '缺少章节ID'}), 400

            chapter = Chapter.query.get_or_404(chapter_id)
            if chapter.novel_id != novel_id:
                return jsonify({'error': '章节不属于该小说'}), 400

            chapter_info = novel_generator._get_chapter_info_from_outline(novel.outline, chapter.chapter_number)
            words_per_chapter = novel.target_words // novel.target_chapters

            if custom_prompt:
                result = novel_generator.ai_service.generate_detailed_outline_with_custom_prompt(
                    chapter_info=chapter_info,
                    settings=novel.settings,
                    outline=novel.outline,
                    chapter_number=chapter.chapter_number,
                    target_words=words_per_chapter,
                    custom_prompt=custom_prompt,
                    novel_id=novel.id
                )
            else:
                result = novel_generator.ai_service.generate_detailed_outline(
                    chapter_info=chapter_info,
                    settings=novel.settings,
                    outline=novel.outline,
                    chapter_number=chapter.chapter_number,
                    target_words=words_per_chapter,
                    novel_id=novel.id
                )

            if result:
                chapter.detailed_outline = result
                db.session.commit()
                return jsonify({'message': f'第{chapter.chapter_number}章细纲重新生成成功', 'content': result})
            else:
                return jsonify({'error': '细纲生成失败'}), 500

        elif content_type == 'chapter_content':
            # 重新生成章节内容
            if not chapter_id:
                return jsonify({'error': '缺少章节ID'}), 400

            chapter = Chapter.query.get_or_404(chapter_id)
            if chapter.novel_id != novel_id:
                return jsonify({'error': '章节不属于该小说'}), 400

            if not chapter.detailed_outline:
                return jsonify({'error': '请先生成章节细纲'}), 400

            words_per_chapter = novel.target_words // novel.target_chapters

            if custom_prompt:
                result = novel_generator.ai_service.generate_chapter_content_with_custom_prompt(
                    detailed_outline=chapter.detailed_outline,
                    settings=novel.settings,
                    chapter_title=chapter.title,
                    target_words=words_per_chapter,
                    custom_prompt=custom_prompt,
                    novel_id=novel.id,
                    chapter_number=chapter.chapter_number
                )
            else:
                result = novel_generator.ai_service.generate_chapter_content(
                    detailed_outline=chapter.detailed_outline,
                    settings=novel.settings,
                    chapter_title=chapter.title,
                    target_words=words_per_chapter,
                    novel_id=novel.id,
                    chapter_number=chapter.chapter_number
                )

            if result:
                chapter.content = result
                chapter.word_count = len(result)
                db.session.commit()
                return jsonify({'message': f'第{chapter.chapter_number}章内容重新生成成功', 'content': result})
            else:
                return jsonify({'error': '内容生成失败'}), 500
        else:
            return jsonify({'error': '不支持的内容类型'}), 400

    except Exception as e:
        return jsonify({'error': f'重新生成失败: {str(e)}'}), 500


@app.route('/api/novels/<int:novel_id>', methods=['DELETE'])
def delete_novel(novel_id):
    """删除小说"""
    novel = Novel.query.get_or_404(novel_id)
    db.session.delete(novel)
    db.session.commit()
    return jsonify({'message': '删除成功'})


# ==================== 章节管理 API ====================

@app.route('/api/novels/<int:novel_id>/chapters', methods=['GET'])
def get_chapters(novel_id):
    """获取小说的所有章节"""
    chapters = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.chapter_number).all()
    return jsonify([chapter.to_dict() for chapter in chapters])


@app.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    """获取单个章节详情"""
    chapter = Chapter.query.get_or_404(chapter_id)
    return jsonify(chapter.to_dict())


# ==================== 日志 API ====================

@app.route('/api/novels/<int:novel_id>/logs', methods=['GET'])
def get_logs(novel_id):
    """获取小说生成日志"""
    limit = request.args.get('limit', 100, type=int)
    logs = GenerationLog.query.filter_by(novel_id=novel_id).order_by(
        GenerationLog.created_at.desc()
    ).limit(limit).all()
    return jsonify([log.to_dict() for log in logs])


# ==================== 导出 API ====================

@app.route('/api/novels/<int:novel_id>/export', methods=['POST'])
def export_novel(novel_id):
    """导出小说为TXT"""
    try:
        filepath = exporter.export_to_txt(novel_id)
        return jsonify({
            'message': '导出成功',
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/novels/<int:novel_id>/download', methods=['GET'])
def download_novel(novel_id):
    """下载小说TXT文件"""
    filepath = exporter.get_export_path(novel_id)
    if not filepath:
        return jsonify({'error': '文件不存在，请先导出'}), 404

    return send_file(filepath, as_attachment=True)


# ==================== AI配置 API ====================

@app.route('/api/ai-configs', methods=['GET'])
def get_ai_configs():
    """获取所有AI配置"""
    configs = AIConfig.query.order_by(AIConfig.created_at.desc()).all()
    return jsonify([config.to_dict() for config in configs])


@app.route('/api/ai-configs', methods=['POST'])
def create_ai_config():
    """创建AI配置"""
    data = request.json

    # 检查配置名称是否已存在
    existing_config = AIConfig.query.filter_by(name=data.get('name')).first()
    if existing_config:
        return jsonify({'error': '配置名称已存在，请使用其他名称'}), 400

    # 如果设置为激活，先取消其他配置的激活状态
    if data.get('is_active', False):
        AIConfig.query.update({'is_active': False})

    config = AIConfig(
        name=data.get('name'),
        api_base=data.get('api_base'),
        api_key=data.get('api_key'),
        model_name=data.get('model_name'),
        config_type=data.get('config_type', 'both'),
        is_active=data.get('is_active', False)
    )

    db.session.add(config)
    db.session.commit()

    return jsonify(config.to_dict()), 201


@app.route('/api/ai-configs/<int:config_id>', methods=['PUT'])
def update_ai_config(config_id):
    """更新AI配置"""
    config = AIConfig.query.get_or_404(config_id)
    data = request.json

    # 如果设置为激活，先取消其他配置的激活状态
    if data.get('is_active', False):
        AIConfig.query.filter(AIConfig.id != config_id).update({'is_active': False})

    if 'name' in data:
        config.name = data['name']
    if 'api_base' in data:
        config.api_base = data['api_base']
    if 'api_key' in data:
        config.api_key = data['api_key']
    if 'model_name' in data:
        config.model_name = data['model_name']
    if 'config_type' in data:
        config.config_type = data['config_type']
    if 'is_active' in data:
        config.is_active = data['is_active']

    db.session.commit()
    return jsonify(config.to_dict())


@app.route('/api/ai-configs/<int:config_id>', methods=['DELETE'])
def delete_ai_config(config_id):
    """删除AI配置"""
    config = AIConfig.query.get_or_404(config_id)
    db.session.delete(config)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/ai-configs/<int:config_id>/activate', methods=['POST'])
def activate_ai_config(config_id):
    """激活指定的AI配置"""
    # 取消所有配置的激活状态
    AIConfig.query.update({'is_active': False})

    # 激活指定配置
    config = AIConfig.query.get_or_404(config_id)
    config.is_active = True
    db.session.commit()

    return jsonify(config.to_dict())


# ==================== 统计 API ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    total_novels = Novel.query.count()
    completed_novels = Novel.query.filter_by(status='completed').count()
    generating_novels = Novel.query.filter_by(status='generating').count()
    failed_novels = Novel.query.filter_by(status='failed').count()

    # Token统计
    total_tokens = db.session.query(func.sum(Novel.total_tokens)).scalar() or 0
    total_cost = db.session.query(func.sum(Novel.total_cost)).scalar() or 0.0

    return jsonify({
        'total_novels': total_novels,
        'completed_novels': completed_novels,
        'generating_novels': generating_novels,
        'failed_novels': failed_novels,
        'total_tokens': total_tokens,
        'total_cost': total_cost
    })


@app.route('/api/token-stats', methods=['GET'])
def get_token_stats():
    """获取Token使用统计"""
    # 获取查询参数
    days = request.args.get('days', 7, type=int)
    novel_id = request.args.get('novel_id', type=int)

    # 基础查询
    query = TokenUsage.query

    # 按小说筛选
    if novel_id:
        query = query.filter_by(novel_id=novel_id)

    # 按时间筛选
    if days > 0:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(TokenUsage.created_at >= start_date)

    # 获取所有记录
    usages = query.order_by(TokenUsage.created_at.desc()).all()

    # 按阶段统计
    stage_stats = db.session.query(
        TokenUsage.stage,
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.cost).label('total_cost'),
        func.count(TokenUsage.id).label('count')
    ).group_by(TokenUsage.stage)

    if novel_id:
        stage_stats = stage_stats.filter_by(novel_id=novel_id)
    if days > 0:
        start_date = datetime.utcnow() - timedelta(days=days)
        stage_stats = stage_stats.filter(TokenUsage.created_at >= start_date)

    stage_stats = stage_stats.all()

    # 按日期统计
    daily_stats = db.session.query(
        func.date(TokenUsage.created_at).label('date'),
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.cost).label('total_cost')
    ).group_by(func.date(TokenUsage.created_at))

    if novel_id:
        daily_stats = daily_stats.filter_by(novel_id=novel_id)
    if days > 0:
        start_date = datetime.utcnow() - timedelta(days=days)
        daily_stats = daily_stats.filter(TokenUsage.created_at >= start_date)

    daily_stats = daily_stats.order_by(func.date(TokenUsage.created_at)).all()

    return jsonify({
        'usages': [usage.to_dict() for usage in usages],
        'stage_stats': [
            {
                'stage': stat.stage,
                'total_tokens': stat.total_tokens,
                'total_cost': float(stat.total_cost),
                'count': stat.count
            }
            for stat in stage_stats
        ],
        'daily_stats': [
            {
                'date': str(stat.date) if stat.date else '',
                'total_tokens': stat.total_tokens,
                'total_cost': float(stat.total_cost)
            }
            for stat in daily_stats
        ]
    })


@app.route('/api/novels/<int:novel_id>/token-stats', methods=['GET'])
def get_novel_token_stats(novel_id):
    """获取单个小说的Token统计"""
    novel = Novel.query.get_or_404(novel_id)

    # 按阶段统计
    stage_stats = db.session.query(
        TokenUsage.stage,
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.prompt_tokens).label('prompt_tokens'),
        func.sum(TokenUsage.completion_tokens).label('completion_tokens'),
        func.sum(TokenUsage.cost).label('total_cost'),
        func.count(TokenUsage.id).label('count'),
        func.avg(TokenUsage.duration).label('avg_duration')
    ).filter_by(novel_id=novel_id).group_by(TokenUsage.stage).all()

    # 按章节统计
    chapter_stats = db.session.query(
        TokenUsage.chapter_number,
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.cost).label('total_cost')
    ).filter_by(novel_id=novel_id).filter(
        TokenUsage.chapter_number.isnot(None)
    ).group_by(TokenUsage.chapter_number).order_by(TokenUsage.chapter_number).all()

    # 按操作类型统计
    operation_stats = db.session.query(
        TokenUsage.operation,
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.cost).label('total_cost'),
        func.count(TokenUsage.id).label('count')
    ).filter_by(novel_id=novel_id).group_by(TokenUsage.operation).all()

    return jsonify({
        'novel': novel.to_dict(),
        'stage_stats': [
            {
                'stage': stat.stage,
                'total_tokens': stat.total_tokens,
                'prompt_tokens': stat.prompt_tokens,
                'completion_tokens': stat.completion_tokens,
                'total_cost': float(stat.total_cost),
                'count': stat.count,
                'avg_duration': float(stat.avg_duration) if stat.avg_duration else 0
            }
            for stat in stage_stats
        ],
        'chapter_stats': [
            {
                'chapter_number': stat.chapter_number,
                'total_tokens': stat.total_tokens,
                'total_cost': float(stat.total_cost)
            }
            for stat in chapter_stats
        ],
        'operation_stats': [
            {
                'operation': stat.operation,
                'total_tokens': stat.total_tokens,
                'total_cost': float(stat.total_cost),
                'count': stat.count
            }
            for stat in operation_stats
        ]
    })


# ==================== 初始化数据库 ====================

@app.before_request
def init_db():
    """初始化数据库"""
    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            db.create_all()
            app.db_initialized = True


# ==================== 恢复未完成的小说生成 ====================

def resume_unfinished_novels():
    """启动时恢复所有未完成的小说生成任务"""
    with app.app_context():
        # 查找所有状态为 'generating' 的小说
        unfinished_novels = Novel.query.filter_by(status='generating').all()

        if unfinished_novels:
            print(f"\n{'='*60}")
            print(f"🔄 发现 {len(unfinished_novels)} 个未完成的小说任务，正在恢复...")
            print(f"{'='*60}\n")

            for novel in unfinished_novels:
                print(f"📚 恢复小说: {novel.title or '未命名小说'} (ID: {novel.id})")
                print(f"   当前阶段: {novel.current_stage}")
                print(f"   创建时间: {novel.created_at}")

                # 在后台线程中继续生成
                def generate(novel_id=novel.id):
                    with app.app_context():
                        try:
                            novel_generator.generate_novel(novel_id)
                            print(f"✅ 小说 ID:{novel_id} 生成完成")
                        except Exception as e:
                            print(f"❌ 小说 ID:{novel_id} 生成失败: {str(e)}")

                thread = threading.Thread(target=generate)
                thread.daemon = True
                thread.start()

            print(f"\n{'='*60}")
            print(f"✅ 所有未完成任务已启动恢复")
            print(f"{'='*60}\n")
        else:
            print("\n✓ 没有未完成的小说任务\n")


if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        db.create_all()

    # 恢复未完成的小说生成任务
    resume_unfinished_novels()

    # 启动Flask应用
    port = int(Config.SECRET_KEY) if hasattr(Config, 'FLASK_PORT') else 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
