#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能优化工具
用于分析数据库性能、生成优化建议、执行优化操作
"""

import os
import sys
import time
import json
import psycopg2
import sqlite3
import mysql.connector
from datetime import datetime
import argparse
from typing import Dict, List, Any, Optional
import concurrent.futures
import statistics

class DatabasePerformanceAnalyzer:
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化数据库性能分析器
        
        Args:
            db_config: 数据库配置信息
                {
                    'type': 'mysql' | 'postgresql' | 'sqlite',
                    'host': 'localhost',
                    'port': 3306,
                    'user': 'username',
                    'password': 'password',
                    'database': 'database_name'
                }
        """
        self.db_config = db_config
        self.db_type = db_config.get('type', 'mysql').lower()
        self.connection = None
        self.analysis_results = {
            'database_info': {},
            'table_analysis': {},
            'index_analysis': {},
            'query_performance': {},
            'optimization_suggestions': [],
            'execution_plan_analysis': []
        }
    
    def connect(self):
        """连接数据库"""
        try:
            if self.db_type == 'mysql':
                self.connection = mysql.connector.connect(
                    host=self.db_config.get('host', 'localhost'),
                    port=self.db_config.get('port', 3306),
                    user=self.db_config.get('user'),
                    password=self.db_config.get('password'),
                    database=self.db_config.get('database')
                )
            elif self.db_type == 'postgresql':
                import psycopg2.extras
                self.connection = psycopg2.connect(
                    host=self.db_config.get('host', 'localhost'),
                    port=self.db_config.get('port', 5432),
                    user=self.db_config.get('user'),
                    password=self.db_config.get('password'),
                    database=self.db_config.get('database')
                )
            elif self.db_type == 'sqlite':
                self.connection = sqlite3.connect(self.db_config.get('database'))
            else:
                raise ValueError(f"不支持的数据库类型: {self.db_type}")
            
            print(f"✅ 成功连接到{self.db_type}数据库")
            
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            print("🔌 数据库连接已断开")
    
    def analyze_database(self) -> Dict[str, Any]:
        """执行完整的数据库分析"""
        print("🔍 开始数据库性能分析...")
        
        try:
            # 基础信息分析
            self._analyze_database_info()
            
            # 表分析
            self._analyze_tables()
            
            # 索引分析
            self._analyze_indexes()
            
            # 查询性能分析
            self._analyze_query_performance()
            
            # 生成优化建议
            self._generate_optimization_suggestions()
            
            print("✅ 数据库分析完成")
            return self.analysis_results
            
        except Exception as e:
            print(f"❌ 数据库分析失败: {e}")
            raise
    
    def _analyze_database_info(self):
        """分析数据库基础信息"""
        print("📊 分析数据库基础信息...")
        
        cursor = self.connection.cursor()
        
        if self.db_type == 'mysql':
            # MySQL数据库信息
            cursor.execute("SHOW VARIABLES LIKE 'version'")
            version_info = dict(cursor.fetchall())
            
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            threads_info = dict(cursor.fetchall())
            
            cursor.execute("SHOW STATUS LIKE 'Questions'")
            questions_info = dict(cursor.fetchall())
            
            self.analysis_results['database_info'] = {
                'type': 'MySQL',
                'version': version_info.get('Variable_value', 'Unknown'),
                'current_connections': threads_info.get('Variable_value', 0),
                'total_queries': questions_info.get('Variable_value', 0),
                'analysis_time': datetime.now().isoformat()
            }
            
        elif self.db_type == 'postgresql':
            # PostgreSQL数据库信息
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]
            
            self.analysis_results['database_info'] = {
                'type': 'PostgreSQL',
                'version': version,
                'current_connections': connections,
                'analysis_time': datetime.now().isoformat()
            }
        
        cursor.close()
    
    def _analyze_tables(self):
        """分析表结构和大表"""
        print("📋 分析表结构...")
        
        cursor = self.connection.cursor()
        
        if self.db_type == 'mysql':
            cursor.execute("""
                SELECT 
                    table_name,
                    table_rows,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    engine,
                    table_collation
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY (data_length + index_length) DESC
            """, (self.db_config.get('database'),))
            
        elif self.db_type == 'postgresql':
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins + n_tup_upd + n_tup_del as total_changes,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                    pg_size_bytes(pg_total_relation_size(schemaname||'.'||tablename))/1024/1024 as size_mb
                FROM pg_stat_user_tables 
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
        
        tables = cursor.fetchall()
        
        table_analysis = {}
        for table in tables:
            if self.db_type == 'mysql':
                name, rows, size_mb, engine, collation = table
                table_analysis[name] = {
                    'rows': rows,
                    'size_mb': size_mb,
                    'engine': engine,
                    'collation': collation,
                    'status': 'large' if size_mb > 100 else 'normal'
                }
            elif self.db_type == 'postgresql':
                schema, name, changes, size_pretty, size_mb = table
                table_analysis[name] = {
                    'schema': schema,
                    'changes': changes,
                    'size_pretty': size_pretty,
                    'size_mb': size_mb,
                    'status': 'large' if size_mb > 100 else 'normal'
                }
        
        self.analysis_results['table_analysis'] = table_analysis
        
        # 识别大表
        large_tables = [name for name, info in table_analysis.items() 
                       if info['status'] == 'large']
        
        if large_tables:
            print(f"⚠️ 发现 {len(large_tables)} 个大表需要优化: {', '.join(large_tables)}")
        
        cursor.close()
    
    def _analyze_indexes(self):
        """分析索引使用情况"""
        print("🔍 分析索引使用情况...")
        
        cursor = self.connection.cursor()
        
        if self.db_type == 'mysql':
            cursor.execute("""
                SELECT 
                    table_schema,
                    table_name,
                    index_name,
                    non_unique,
                    column_name,
                    seq_in_index,
                    cardinality,
                    sub_part,
                    packed,
                    null_value,
                    index_type
                FROM information_schema.statistics
                WHERE table_schema = %s
                ORDER BY table_name, index_name, seq_in_index
            """, (self.db_config.get('database'),))
            
            indexes = cursor.fetchall()
            
            # 分析索引使用统计
            cursor.execute("""
                SELECT 
                    object_schema,
                    object_name,
                    index_name,
                    count_fetch,
                    count_insert,
                    count_update,
                    count_delete
                FROM performance_schema.table_io_waits_summary_by_index_usage
                WHERE object_schema = %s
            """, (self.db_config.get('database'),))
            
            index_usage = cursor.fetchall()
        
        elif self.db_type == 'postgresql':
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            indexes = cursor.fetchall()
            
            # 获取索引使用统计
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
            """)
            
            index_usage = cursor.fetchall()
        
        # 处理索引分析结果
        self._process_index_analysis(indexes, index_usage)
        
        cursor.close()
    
    def _process_index_analysis(self, indexes, index_usage):
        """处理索引分析结果"""
        index_analysis = {}
        
        for index in indexes:
            if self.db_type == 'mysql':
                schema, table, name, non_unique, column, seq, cardinality, sub_part, packed, null_value, index_type = index
                key = f"{table}.{name}"
                
                # 查找使用统计
                usage = next((u for u in index_usage if u[1] == table and u[2] == name), None)
                
                index_analysis[key] = {
                    'table': table,
                    'name': name,
                    'type': 'UNIQUE' if non_unique == 0 else 'INDEX',
                    'columns': [column],
                    'cardinality': cardinality,
                    'index_type': index_type,
                    'usage_stats': {
                        'fetch_count': usage[3] if usage else 0,
                        'insert_count': usage[4] if usage else 0,
                        'update_count': usage[5] if usage else 0,
                        'delete_count': usage[6] if usage else 0
                    } if usage else None
                }
                
            elif self.db_type == 'postgresql':
                schema, table, name, definition = index
                key = f"{table}.{name}"
                
                # 查找使用统计
                usage = next((u for u in index_usage if u[1] == table and u[2] == name), None)
                
                index_analysis[key] = {
                    'table': table,
                    'name': name,
                    'definition': definition,
                    'usage_stats': {
                        'scan_count': usage[3] if usage else 0,
                        'tuples_read': usage[4] if usage else 0,
                        'tuples_fetch': usage[5] if usage else 0
                    } if usage else None
                }
        
        self.analysis_results['index_analysis'] = index_analysis
        
        # 识别未使用的索引
        unused_indexes = []
        for key, info in index_analysis.items():
            usage = info.get('usage_stats', {})
            if self.db_type == 'mysql':
                total_usage = usage.get('fetch_count', 0) + usage.get('insert_count', 0) + \
                            usage.get('update_count', 0) + usage.get('delete_count', 0)
            else:  # postgresql
                total_usage = usage.get('scan_count', 0)
            
            if total_usage == 0:
                unused_indexes.append(key)
        
        if unused_indexes:
            print(f"⚠️ 发现 {len(unused_indexes)} 个未使用的索引")
            for idx in unused_indexes[:5]:  # 只显示前5个
                print(f"   - {idx}")
    
    def _analyze_query_performance(self):
        """分析查询性能"""
        print("⚡ 分析查询性能...")
        
        # 模拟慢查询测试
        test_queries = self._get_test_queries()
        query_results = []
        
        for query_info in test_queries:
            query = query_info['query']
            description = query_info['description']
            
            try:
                start_time = time.time()
                
                cursor = self.connection.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                # 获取执行计划
                explain_query = f"EXPLAIN {query}"
                cursor.execute(explain_query)
                explain_results = cursor.fetchall()
                
                query_results.append({
                    'description': description,
                    'execution_time_ms': round(execution_time, 2),
                    'result_count': len(results),
                    'explain_plan': explain_results,
                    'status': 'success'
                })
                
                cursor.close()
                
            except Exception as e:
                query_results.append({
                    'description': description,
                    'execution_time_ms': None,
                    'result_count': 0,
                    'explain_plan': [],
                    'status': 'error',
                    'error': str(e)
                })
        
        self.analysis_results['query_performance'] = query_results
        
        # 分析慢查询
        slow_queries = [q for q in query_results if q.get('execution_time_ms', 0) > 1000]
        if slow_queries:
            print(f"⚠️ 发现 {len(slow_queries)} 个慢查询")
    
    def _get_test_queries(self) -> List[Dict[str, str]]:
        """获取测试查询列表"""
        if self.db_type == 'mysql':
            return [
                {
                    'description': '用户总数统计',
                    'query': 'SELECT COUNT(*) as total_users FROM users'
                },
                {
                    'description': '最新健康数据',
                    'query': 'SELECT * FROM health_data ORDER BY created_at DESC LIMIT 10'
                },
                {
                    'description': '用户健康记录统计',
                    'query': '''
                        SELECT u.real_name, COUNT(h.record_id) as health_records 
                        FROM users u 
                        LEFT JOIN health_data h ON u.user_id = h.user_id 
                        GROUP BY u.user_id, u.real_name 
                        LIMIT 20
                    '''
                }
            ]
        elif self.db_type == 'postgresql':
            return [
                {
                    'description': '用户总数统计',
                    'query': 'SELECT COUNT(*) as total_users FROM profiles'
                },
                {
                    'description': '最新健康数据',
                    'query': 'SELECT * FROM health_data ORDER BY created_at DESC LIMIT 10'
                }
            ]
        else:
            return []
    
    def _generate_optimization_suggestions(self):
        """生成优化建议"""
        print("💡 生成优化建议...")
        
        suggestions = []
        
        # 基于表分析的优化建议
        for table_name, info in self.analysis_results['table_analysis'].items():
            if info['status'] == 'large':
                suggestions.append({
                    'type': 'table_optimization',
                    'priority': 'high',
                    'target': table_name,
                    'issue': f"表 {table_name} 过大 ({info['size_mb']}MB)",
                    'suggestions': [
                        f"考虑对 {table_name} 进行分区",
                        "清理历史数据",
                        "添加适当的索引",
                        "考虑数据归档策略"
                    ]
                })
        
        # 基于索引分析的优化建议
        for index_name, info in self.analysis_results['index_analysis'].items():
            usage = info.get('usage_stats', {})
            if usage:
                if self.db_type == 'mysql':
                    total_usage = usage.get('fetch_count', 0) + usage.get('insert_count', 0)
                else:
                    total_usage = usage.get('scan_count', 0)
                
                if total_usage == 0:
                    suggestions.append({
                        'type': 'index_optimization',
                        'priority': 'medium',
                        'target': index_name,
                        'issue': f"索引 {index_name} 未被使用",
                        'suggestions': [
                            "删除未使用的索引以减少写入开销",
                            "检查查询是否需要此索引",
                            "考虑合并相关索引"
                        ]
                    })
        
        # 基于查询性能的优化建议
        for query_result in self.analysis_results['query_performance']:
            if query_result.get('execution_time_ms', 0) > 1000:
                suggestions.append({
                    'type': 'query_optimization',
                    'priority': 'high',
                    'target': query_result['description'],
                    'issue': f"查询执行时间过长 ({query_result['execution_time_ms']}ms)",
                    'suggestions': [
                        "添加适当的索引",
                        "优化查询逻辑",
                        "考虑查询结果缓存",
                        "使用分页避免大量数据传输"
                    ]
                })
        
        self.analysis_results['optimization_suggestions'] = suggestions
        
        print(f"💡 生成了 {len(suggestions)} 条优化建议")
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """生成详细的性能分析报告"""
        print("📄 生成性能分析报告...")
        
        report = {
            'database_info': self.analysis_results['database_info'],
            'summary': {
                'total_tables': len(self.analysis_results['table_analysis']),
                'total_indexes': len(self.analysis_results['index_analysis']),
                'large_tables': len([t for t in self.analysis_results['table_analysis'].values() if t['status'] == 'large']),
                'slow_queries': len([q for q in self.analysis_results['query_performance'] if q.get('execution_time_ms', 0) > 1000]),
                'optimization_suggestions': len(self.analysis_results['optimization_suggestions'])
            },
            'table_analysis': self.analysis_results['table_analysis'],
            'index_analysis': self.analysis_results['index_analysis'],
            'query_performance': self.analysis_results['query_performance'],
            'optimization_suggestions': self.analysis_results['optimization_suggestions'],
            'generated_at': datetime.now().isoformat()
        }
        
        # 生成Markdown格式报告
        markdown_report = self._generate_markdown_report(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            print(f"📄 报告已保存到: {output_file}")
        else:
            print("📄 报告内容:")
            print("=" * 60)
            print(markdown_report)
        
        return markdown_report
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        md_content = f"""# 数据库性能分析报告

## 1. 数据库概况

- **数据库类型**: {report['database_info']['type']}
- **数据库版本**: {report['database_info']['version']}
- **当前连接数**: {report['database_info']['current_connections']}
- **分析时间**: {report['generated_at']}

## 2. 分析摘要

| 指标 | 数值 |
|------|------|
| 总表数 | {report['summary']['total_tables']} |
| 总索引数 | {report['summary']['total_indexes']} |
| 大表数量 | {report['summary']['large_tables']} |
| 慢查询数量 | {report['summary']['slow_queries']} |
| 优化建议数 | {report['summary']['optimization_suggestions']} |

## 3. 表结构分析

"""
        
        if report['table_analysis']:
            md_content += "| 表名 | 大小(MB) | 行数 | 状态 | 引擎 |\n"
            md_content += "|------|----------|------|------|------|\n"
            
            for table_name, info in report['table_analysis'].items():
                size = info.get('size_mb', 0)
                rows = info.get('rows', 0) or info.get('changes', 0)
                status = info['status']
                engine = info.get('engine', info.get('schema', 'Unknown'))
                
                status_emoji = "🔴" if status == "large" else "🟢"
                md_content += f"| {table_name} | {size} | {rows} | {status_emoji} {status} | {engine} |\n"
        else:
            md_content += "暂无表数据\n"
        
        md_content += "\n## 4. 索引分析\n\n"
        
        if report['index_analysis']:
            for index_name, info in report['index_analysis'].items():
                md_content += f"### {index_name}\n"
                md_content += f"- 表名: {info['table']}\n"
                md_content += f"- 类型: {info.get('type', info.get('definition', 'Unknown'))}\n"
                
                if info.get('usage_stats'):
                    usage = info['usage_stats']
                    md_content += f"- 使用统计: {usage}\n"
                else:
                    md_content += "- 使用统计: 无数据\n"
                
                md_content += "\n"
        else:
            md_content += "暂无索引数据\n"
        
        md_content += "## 5. 查询性能分析\n\n"
        
        if report['query_performance']:
            md_content += "| 查询描述 | 执行时间(ms) | 结果数 | 状态 |\n"
            md_content += "|----------|--------------|--------|------|\n"
            
            for query in report['query_performance']:
                desc = query['description']
                exec_time = query.get('execution_time_ms', 0)
                result_count = query['result_count']
                status = query['status']
                
                if exec_time > 1000:
                    status_emoji = "🔴"
                    status_text = f"{status} (慢查询)"
                else:
                    status_emoji = "🟢"
                    status_text = status
                
                md_content += f"| {desc} | {exec_time} | {result_count} | {status_emoji} {status_text} |\n"
        else:
            md_content += "暂无查询性能数据\n"
        
        md_content += "\n## 6. 优化建议\n\n"
        
        if report['optimization_suggestions']:
            for i, suggestion in enumerate(report['optimization_suggestions'], 1):
                priority_emoji = "🔴" if suggestion['priority'] == 'high' else "🟡" if suggestion['priority'] == 'medium' else "🟢"
                md_content += f"### 建议 {i}: {priority_emoji} {suggestion['type']}\n"
                md_content += f"**目标**: {suggestion['target']}\n"
                md_content += f"**问题**: {suggestion['issue']}\n"
                md_content += "**建议操作**:\n"
                for suggestion_item in suggestion['suggestions']:
                    md_content += f"- {suggestion_item}\n"
                md_content += "\n"
        else:
            md_content += "暂无优化建议\n"
        
        md_content += """
## 7. 性能监控建议

### 持续监控指标
1. **查询响应时间**: 监控关键查询的执行时间
2. **索引使用率**: 定期检查索引的使用情况
3. **表大小增长**: 监控大表的增长速度
4. **连接池使用**: 监控数据库连接池的使用情况

### 定期维护任务
1. **索引重建**: 定期重建碎片化的索引
2. **统计信息更新**: 更新表和索引的统计信息
3. **慢查询日志分析**: 分析并优化慢查询
4. **数据归档**: 定期归档历史数据

## 8. 下一步行动计划

1. **立即执行**: 实施高优先级的优化建议
2. **短期目标**: 完成所有索引优化和查询优化
3. **长期规划**: 建立完善的监控和维护流程
"""
        
        return md_content


def main():
    parser = argparse.ArgumentParser(description='数据库性能分析工具')
    parser.add_argument('--db-type', choices=['mysql', 'postgresql', 'sqlite'], 
                       default='mysql', help='数据库类型')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', type=int, help='数据库端口')
    parser.add_argument('--user', required=True, help='数据库用户')
    parser.add_argument('--password', required=True, help='数据库密码')
    parser.add_argument('--database', required=True, help='数据库名')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    parser.add_argument('--generate-sql', action='store_true', 
                       help='生成优化SQL脚本')
    
    args = parser.parse_args()
    
    # 构建数据库配置
    db_config = {
        'type': args.db_type,
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password,
        'database': args.database
    }
    
    # 创建分析器并执行分析
    analyzer = DatabasePerformanceAnalyzer(db_config)
    
    try:
        analyzer.connect()
        results = analyzer.analyze_database()
        
        # 生成报告
        output_file = args.output or f"db_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        analyzer.generate_report(output_file)
        
        # 生成优化SQL脚本
        if args.generate_sql:
            sql_file = f"optimization_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            generate_optimization_sql(results, sql_file)
        
        print("✅ 数据库性能分析完成")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        sys.exit(1)
        
    finally:
        analyzer.disconnect()


def generate_optimization_sql(results: Dict[str, Any], output_file: str):
    """生成优化SQL脚本"""
    print("🔧 生成优化SQL脚本...")
    
    sql_content = ["-- 数据库优化脚本", f"-- 生成时间: {datetime.now().isoformat()}", ""]
    
    # 基于建议生成SQL
    for suggestion in results.get('optimization_suggestions', []):
        sql_content.append(f"-- {suggestion['issue']}")
        
        if suggestion['type'] == 'index_optimization' and '未使用' in suggestion['issue']:
            # 生成删除未使用索引的SQL
            if '.' in suggestion['target']:
                table_name, index_name = suggestion['target'].split('.', 1)
                if results['database_info']['type'] == 'MySQL':
                    sql_content.append(f"DROP INDEX `{index_name}` ON `{table_name}`;")
                elif results['database_info']['type'] == 'PostgreSQL':
                    sql_content.append(f"DROP INDEX IF EXISTS {index_name};")
        
        sql_content.append("")
    
    # 添加监控相关SQL
    sql_content.extend([
        "-- 监控查询",
        "-- 查看当前活动连接",
        "SHOW PROCESSLIST;" if results['database_info']['type'] == 'MySQL' else "SELECT * FROM pg_stat_activity;",
        "",
        "-- 查看表大小",
        "SELECT table_name, ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY size_mb DESC;"
        if results['database_info']['type'] == 'MySQL' 
        else "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_stat_user_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;",
        ""
    ])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_content))
    
    print(f"🔧 优化SQL脚本已保存到: {output_file}")


if __name__ == '__main__':
    main()
