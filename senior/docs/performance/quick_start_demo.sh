#!/bin/bash
# 养老智能体系统性能测试快速示例
# 演示如何使用性能优化工具包

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE} 养老智能体系统性能测试快速示例${NC}"
echo -e "${BLUE}============================================${NC}"

# 检查工具是否存在
TOOLS_DIR="./docs/performance"
MONITOR_SCRIPT="$TOOLS_DIR/performance_monitor.sh"
DB_ANALYZER="$TOOLS_DIR/database_performance_analyzer.py"
FRONTEND_TEST="$TOOLS_DIR/frontend_performance_test.js"

echo -e "\n${YELLOW}1. 检查性能测试工具...${NC}"

if [[ -f "$MONITOR_SCRIPT" ]]; then
    echo -e "${GREEN}✅ 性能监控脚本: $MONITOR_SCRIPT${NC}"
else
    echo -e "${RED}❌ 性能监控脚本不存在${NC}"
fi

if [[ -f "$DB_ANALYZER" ]]; then
    echo -e "${GREEN}✅ 数据库分析工具: $DB_ANALYZER${NC}"
else
    echo -e "${RED}❌ 数据库分析工具不存在${NC}"
fi

if [[ -f "$FRONTEND_TEST" ]]; then
    echo -e "${GREEN}✅ 前端性能测试: $FRONTEND_TEST${NC}"
else
    echo -e "${RED}❌ 前端性能测试不存在${NC}"
fi

# 创建日志目录
mkdir -p "$TOOLS_DIR/logs"

echo -e "\n${YELLOW}2. 系统环境检查...${NC}"

# 检查依赖工具
dependencies=("curl" "jq" "bc" "python3")
for dep in "${dependencies[@]}"; do
    if command -v "$dep" &> /dev/null; then
        echo -e "${GREEN}✅ $dep - 已安装${NC}"
    else
        echo -e "${RED}❌ $dep - 未安装${NC}"
        echo -e "   请运行: sudo apt-get install $dep"
    fi
done

echo -e "\n${YELLOW}3. 示例：API性能测试${NC}"

# API测试示例
API_TEST_URL="https://httpbin.org/get"  # 使用示例API
echo -e "${BLUE}测试URL: $API_TEST_URL${NC}"

if command -v "$MONITOR_SCRIPT" &> /dev/null; then
    # 注意：这里使用示例URL，实际使用时替换为真实API
    echo -e "${BLUE}运行命令示例:${NC}"
    echo -e "  $MONITOR_SCRIPT api $API_TEST_URL GET '' 10"
    echo -e "${BLUE}完整测试命令:${NC}"
    echo -e "  $MONITOR_SCRIPT full"
else
    echo -e "${RED}监控脚本不可用${NC}"
fi

echo -e "\n${YELLOW}4. 示例：数据库性能分析${NC}"

# 数据库分析示例
echo -e "${BLUE}数据库分析命令示例:${NC}"
echo -e "${GREEN}MySQL:${NC}"
echo -e "  python3 $DB_ANALYZER --db-type mysql --host localhost --user root --password password --database eldercare_db --output mysql_report.md"
echo -e "${GREEN}PostgreSQL:${NC}"
echo -e "  python3 $DB_ANALYZER --db-type postgresql --host localhost --user postgres --password password --database eldercare_db --output postgres_report.md"
echo -e "${GREEN}SQLite:${NC}"
echo -e "  python3 $DB_ANALYZER --db-type sqlite --database ./eldercare.db --output sqlite_report.md"

echo -e "\n${YELLOW}5. 示例：前端性能测试${NC}"

# 前端测试示例
echo -e "${BLUE}前端性能测试示例代码:${NC}"
cat << 'EOF'
<!-- 在HTML页面中引入 -->
<script src="docs/performance/frontend_performance_test.js"></script>

<script>
// 执行性能测试
runPerformanceTest('https://your-website.com', 10)
  .then(report => {
    console.log('性能测试完成');
    console.log('FCP:', report.coreWebVitals.fcp.value + 'ms');
    console.log('LCP:', report.coreWebVitals.lcp.value + 'ms');
    console.log('FID:', report.coreWebVitals.fid.value + 'ms');
    console.log('CLS:', report.coreWebVitals.cls.value);
  })
  .catch(error => {
    console.error('测试失败:', error);
  });
</script>
EOF

echo -e "\n${YELLOW}6. 常用性能测试场景${NC}"

echo -e "${GREEN}场景1: 系统上线前基准测试${NC}"
cat << 'EOF'
# 1. 环境检查
./performance_monitor.sh check

# 2. API性能测试
./performance_monitor.sh api /api/v1/users/profile GET "" 100
./performance_monitor.sh api /api/v1/health/data POST '{"test":true}' 50

# 3. 数据库性能分析
python3 database_performance_analyzer.py --db-type mysql --output baseline_report.md

# 4. 负载测试
./performance_monitor.sh load 100 300  # 100用户并发，持续5分钟
EOF

echo -e "\n${GREEN}场景2: 生产环境持续监控${NC}"
cat << 'EOF'
# 后台持续监控
nohup ./performance_monitor.sh monitor > monitor.log 2>&1 &

# 定期生成报告
./performance_monitor.sh report

# 异常情况下的快速检测
./performance_monitor.sh load 50 60
EOF

echo -e "\n${GREEN}场景3: 性能问题排查${NC}"
cat << 'EOF'
# 全面性能分析
./performance_monitor.sh full

# 慢查询分析
python3 database_performance_analyzer.py --db-type mysql --output slow_analysis.md

# 前端性能深度分析
# 在浏览器控制台运行测试脚本
EOF

echo -e "\n${YELLOW}7. 性能优化检查清单${NC}"

cat << 'EOF'
数据库优化:
□ 检查并添加缺失的索引
□ 删除未使用的索引
□ 优化慢查询
□ 实施分区策略
□ 调整连接池配置

应用优化:
□ 实施多级缓存
□ 异步处理非关键操作
□ 优化API响应时间
□ 实施负载均衡
□ 添加熔断器

前端优化:
□ 实施代码分割
□ 启用Gzip/Brotli压缩
□ 优化图片和资源加载
□ 改进Core Web Vitals
□ 实施PWA功能

网络优化:
□ 部署CDN
□ 启用HTTP/2
□ 优化DNS解析
□ 实施预加载策略
□ 配置缓存策略
EOF

echo -e "\n${YELLOW}8. 故障排除提示${NC}"

echo -e "${BLUE}常见问题解决方案:${NC}"
cat << 'EOF'
❌ 连接超时 → 增加超时时间，检查网络连接
❌ 数据库连接失败 → 验证连接参数，检查服务状态
❌ 权限错误 → 确保有足够权限访问文件和数据库
❌ 内存不足 → 优化查询，减少并发数
❌ 测试结果异常 → 多次运行验证，检查环境一致性
EOF

echo -e "\n${BLUE}============================================${NC}"
echo -e "${GREEN}性能测试工具包准备就绪！${NC}"
echo -e "${BLUE}详细文档请参考: docs/performance/README.md${NC}"
echo -e "${BLUE}完整报告请查看: docs/performance/performance_optimization_report.md${NC}"
echo -e "${BLUE}============================================${NC}"

# 显示帮助信息
echo -e "\n${YELLOW}快速帮助:${NC}"
echo -e "${GREEN}查看所有可用命令:${NC}"
echo -e "  ./docs/performance/performance_monitor.sh help"
echo -e "${GREEN}查看数据库分析工具帮助:${NC}"
echo -e "  python3 docs/performance/database_performance_analyzer.py --help"
