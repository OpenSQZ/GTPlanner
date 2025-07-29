"""
GTPlanner Web应用
提供完整的Web界面功能
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('utils')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import logging

# 导入项目模块
from main import GTPlannerSystem
from database_manager import DatabaseManager
from cache_manager import cache_manager, QueryCache
from logging_config import log_config, log_query, log_error, log_performance
from config import config_manager
from performance_monitor import performance_monitor, start_performance_monitoring

# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'gtplanner-secret-key-2024')
CORS(app)

# 全局变量
gtplanner_system = None
db_manager = None
query_cache = None
system_ready = False
initialization_error = None

# 配置日志
logger = logging.getLogger(__name__)


def initialize_system():
    """在后台初始化系统"""
    global gtplanner_system, db_manager, query_cache, system_ready, initialization_error
    
    try:
        logger.info("开始初始化GTPlanner系统...")
        
        # 初始化数据库
        db_manager = DatabaseManager()
        logger.info("数据库初始化完成")
        
        # 初始化GTPlanner系统
        gtplanner_system = GTPlannerSystem()
        logger.info("GTPlanner系统初始化完成")
        
        # 初始化查询缓存
        query_cache = QueryCache()
        logger.info("查询缓存初始化完成")
        
        # 启动性能监控
        start_performance_monitoring()
        logger.info("性能监控启动完成")
        
        system_ready = True
        logger.info("系统初始化完成")
        
    except Exception as e:
        initialization_error = str(e)
        logger.error(f"系统初始化失败: {e}")
        system_ready = False


def get_gtplanner_system():
    """获取GTPlanner系统实例"""
    return gtplanner_system


def get_db_manager():
    """获取数据库管理器实例"""
    return db_manager


def get_query_cache():
    """获取查询缓存实例"""
    return query_cache


# 在后台线程中初始化系统
init_thread = threading.Thread(target=initialize_system, daemon=True)
init_thread.start()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """系统状态API"""
    try:
        if not system_ready:
            return jsonify({
                'status': 'initializing',
                'message': '系统正在初始化...',
                'error': initialization_error
            }), 503
        
        # 获取系统统计信息
        if gtplanner_system:
            # 获取BadCase统计
            total_count = gtplanner_system.badcase_analyzer.get_total_count()
            label_distribution = gtplanner_system.badcase_analyzer.get_label_distribution()
            user_stats = gtplanner_system.badcase_analyzer.get_user_statistics()
            
            badcase_stats = {
                'total_count': total_count,
                'label_distribution': label_distribution,
                'user_stats': user_stats
            }
            
            # 获取RAG统计
            rag_stats = gtplanner_system.rag_engine.get_knowledge_base_stats()
        else:
            badcase_stats = {'total_count': 0, 'label_distribution': {}, 'user_stats': {}}
            rag_stats = {'document_count': 0}
        
        # 获取缓存统计
        cache_stats = cache_manager.get_stats()
        
        # 获取性能统计
        perf_summary = performance_monitor.get_performance_summary()
        
        return jsonify({
            'status': 'ready',
            'system_ready': system_ready,
            'badcase_stats': badcase_stats,
            'rag_stats': rag_stats,
            'cache_stats': cache_stats,
            'performance': perf_summary,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        log_error(e, "api_status")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def api_query():
    """查询API"""
    try:
        if not system_ready:
            return jsonify({
                'error': '系统尚未准备就绪，请稍后再试'
            }), 503
        
        data = request.get_json()
        question = data.get('question', '').strip()
        user_id = data.get('user_id', 'web_user')
        
        if not question:
            return jsonify({
                'error': '问题不能为空'
            }), 400
        
        # 记录开始时间
        start_time = time.time()
        
        # 检查缓存
        cached_answer = query_cache.get_cached_answer(question, [])
        if cached_answer:
            processing_time = time.time() - start_time
            log_query(user_id, question, cached_answer, "满意", processing_time)
            log_performance("cached_query", processing_time)
            
            return jsonify({
                'answer': cached_answer,
                'feedback': '满意',
                'processing_time': processing_time,
                'cached': True,
                'relevant_docs_count': 0
            })
        
        # 处理查询
        result = gtplanner_system.process_user_query(question)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 处理不同类型的返回结果
        if 'stat_type' in result:
            # 统计查询结果
            answer = f"'{result['stat_label']}' 类型的BadCase数量为: {result['stat_count']}"
            if result.get('matched_labels'):
                answer += f"\n匹配的标签: {', '.join(result['matched_labels'])}"
            feedback = '满意'
            relevant_docs = []
        elif 'detail_label' in result:
            # 明细查询结果
            badcases = result.get('badcases', [])
            if badcases:
                answer = f"找到 {len(badcases)} 个'{result['detail_label']}'类型的BadCase:\n"
                for i, bc in enumerate(badcases[:10], 1):  # 只显示前10个
                    answer += f"{i}. {bc.input_prompt[:50]}... -> {bc.feedback_label}\n"
                if len(badcases) > 10:
                    answer += f"... 还有 {len(badcases) - 10} 个BadCase"
            else:
                answer = f"没有找到'{result['detail_label']}'类型的BadCase"
            feedback = '满意'
            relevant_docs = []
        else:
            # 普通RAG查询结果
            answer = result.get('answer', '')
            feedback = result.get('feedback', '满意')
            relevant_docs = result.get('relevant_docs', [])
        
        # 记录查询日志
        log_query(user_id, question, answer, feedback, processing_time)
        log_performance("query_processing", processing_time, {
            'question_length': len(question),
            'answer_length': len(answer),
            'feedback': feedback
        })
        
        # 缓存结果（只缓存满意的结果）
        if feedback == '满意':
            query_cache.cache_answer(question, answer, relevant_docs)
        
        return jsonify({
            'answer': answer,
            'feedback': feedback,
            'processing_time': processing_time,
            'cached': False,
            'relevant_docs_count': len(relevant_docs)
        })
    
    except Exception as e:
        log_error(e, "api_query")
        return jsonify({
            'error': f'查询处理失败: {str(e)}'
        }), 500


@app.route('/api/badcases')
def api_badcases():
    """获取BadCase列表"""
    try:
        if not system_ready:
            return jsonify({'error': '系统尚未准备就绪'}), 503
        
        # 获取查询参数
        user_id = request.args.get('user_id')
        feedback = request.args.get('feedback')
        limit = request.args.get('limit', 50, type=int)
        
        # 获取BadCase列表
        if gtplanner_system:
            all_badcases = gtplanner_system.badcase_analyzer.storage_engine.get_all_badcases()
            
            # 过滤BadCase
            filtered_badcases = []
            for badcase in all_badcases:
                if user_id and badcase.user_id != user_id:
                    continue
                if feedback and badcase.feedback_label != feedback:
                    continue
                filtered_badcases.append(badcase)
            
            # 限制数量
            if limit:
                filtered_badcases = filtered_badcases[:limit]
            
            # 转换为字典格式
            badcase_list = []
            for badcase in filtered_badcases:
                badcase_list.append({
                    'id': badcase.timestamp,  # 使用时间戳作为ID
                    'input_prompt': badcase.input_prompt,
                    'output_result': badcase.output_result,
                    'feedback_label': badcase.feedback_label,
                    'user_id': badcase.user_id,
                    'timestamp': badcase.timestamp
                })
            
            return jsonify({
                'badcases': badcase_list,
                'total': len(badcase_list)
            })
        else:
            return jsonify({
                'badcases': [],
                'total': 0
            })
    
    except Exception as e:
        log_error(e, "api_badcases")
        return jsonify({
            'error': f'获取BadCase失败: {str(e)}'
        }), 500


@app.route('/api/stats')
def api_stats():
    """获取统计信息"""
    try:
        if not system_ready:
            return jsonify({'error': '系统尚未准备就绪'}), 503
        
        # 获取各种统计信息
        badcase_stats = db_manager.get_badcase_stats()
        cache_stats = cache_manager.get_stats()
        perf_summary = performance_monitor.get_performance_summary()
        alerts = performance_monitor.get_alerts()
        
        return jsonify({
            'badcase_stats': badcase_stats,
            'cache_stats': cache_stats,
            'performance': perf_summary,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        log_error(e, "api_stats")
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge')
def api_knowledge():
    """获取知识库信息"""
    try:
        if not system_ready:
            return jsonify({'error': '系统尚未准备就绪'}), 503
        
        documents = db_manager.get_knowledge_documents()
        
        return jsonify({
            'documents': documents,
            'total': len(documents)
        })
    
    except Exception as e:
        log_error(e, "api_knowledge")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
def api_clear_cache():
    """清空缓存"""
    try:
        cache_manager.clear()
        return jsonify({'message': '缓存已清空'})
    
    except Exception as e:
        log_error(e, "api_clear_cache")
        return jsonify({'error': str(e)}), 500


@app.route('/api/system/restart', methods=['POST'])
def api_restart_system():
    """重启系统"""
    try:
        global gtplanner_system, system_ready
        
        # 重新初始化系统
        gtplanner_system = GTPlannerSystem()
        system_ready = True
        
        return jsonify({'message': '系统重启成功'})
    
    except Exception as e:
        log_error(e, "api_restart_system")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def api_health():
    """健康检查"""
    try:
        return jsonify({
            'status': 'healthy',
            'system_ready': system_ready,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': '页面未找到'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    log_error(error, "internal_error")
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 创建必要的目录
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    Path('cache').mkdir(exist_ok=True)
    
    # 启动Web服务器
    host = config_manager.web.host
    port = config_manager.web.port
    debug = config_manager.web.debug
    
    print(f"启动GTPlanner Web服务器...")
    print(f"地址: http://{host}:{port}")
    print(f"调试模式: {debug}")
    
    app.run(host=host, port=port, debug=debug, threaded=True) 