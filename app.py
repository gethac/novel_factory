import threading
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from datetime import datetime
from models import db, Novel, Chapter, GenerationLog, AIConfig
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

    # 如果设置为激活，先取消其他配置的激活状态
    if data.get('is_active', False):
        AIConfig.query.update({'is_active': False})

    config = AIConfig(
        name=data.get('name'),
        api_base=data.get('api_base'),
        api_key=data.get('api_key'),
        model_name=data.get('model_name'),
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

    return jsonify({
        'total_novels': total_novels,
        'completed_novels': completed_novels,
        'generating_novels': generating_novels,
        'failed_novels': failed_novels
    })


# ==================== 初始化数据库 ====================

@app.before_request
def init_db():
    """初始化数据库"""
    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            db.create_all()
            app.db_initialized = True


if __name__ == '__main__':
    port = int(Config.SECRET_KEY) if hasattr(Config, 'FLASK_PORT') else 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
