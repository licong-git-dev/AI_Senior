#!/bin/bash
# 养老智能体系统性能监控脚本
# 使用方法: ./performance_monitor.sh [command] [options]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
API_BASE_URL="https://api.eldercare.ai"
MONITORING_DURATION=300  # 5分钟
METRICS_INTERVAL=10      # 10秒间隔
OUTPUT_DIR="./performance_logs"
LOG_FILE="$OUTPUT_DIR/monitor_$(date +%Y%m%d_%H%M%S).log"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 打印日志函数
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查系统要求
check_requirements() {
    info "检查系统要求..."
    
    # 检查必要的工具
    local tools=("curl" "jq" "bc")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "未找到工具: $tool"
            error "请安装: sudo apt-get install $tool"
            exit 1
        fi
    done
    
    # 检查网络连接
    if ! curl -s --max-time 5 "$API_BASE_URL/health" > /dev/null; then
        error "无法连接到API服务器: $API_BASE_URL"
        error "请检查网络连接和服务器状态"
        exit 1
    fi
    
    log "系统检查通过"
}

# API性能测试
test_api_performance() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    local iterations="${4:-100}"
    
    info "开始API性能测试: $endpoint"
    info "请求方法: $method, 迭代次数: $iterations"
    
    local total_time=0
    local success_count=0
    local error_count=0
    local response_times=()
    
    for ((i=1; i<=iterations; i++)); do
        local start_time=$(date +%s.%3N)
        
        if [[ "$method" == "POST" ]] && [[ -n "$data" ]]; then
            response=$(curl -s -w "%{http_code}" -X POST \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_BASE_URL$endpoint" 2>/dev/null)
        else
            response=$(curl -s -w "%{http_code}" "$API_BASE_URL$endpoint" 2>/dev/null)
        fi
        
        local end_time=$(date +%s.%3N)
        local response_time=$(echo "$end_time - $start_time" | bc -l)
        local http_code="${response: -3}"
        
        response_times+=("$response_time")
        total_time=$(echo "$total_time + $response_time" | bc -l)
        
        if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
            ((success_count++))
        else
            ((error_count++))
        fi
        
        # 进度显示
        if ((i % 10 == 0)); then
            echo -ne "${BLUE}进度: $i/$iterations${NC}\r"
        fi
    done
    
    echo
    
    # 计算统计指标
    local avg_time=$(echo "scale=3; $total_time / $iterations" | bc -l)
    local success_rate=$(echo "scale=2; $success_count * 100 / $iterations" | bc -l)
    
    # 计算P95响应时间
    response_times=($(printf '%s\n' "${response_times[@]}" | sort -n))
    local p95_index=$(echo "$iterations * 0.95" | bc | cut -d. -f1)
    local p95_time="${response_times[$p95_index]}"
    
    log "API性能测试完成: $endpoint"
    log "  平均响应时间: ${avg_time}ms"
    log "  P95响应时间: ${p95_time}ms"
    log "  成功率: ${success_rate}%"
    log "  成功次数: $success_count"
    log "  失败次数: $error_count"
    
    # 保存结果到文件
    {
        echo "API: $endpoint"
        echo "方法: $method"
        echo "测试时间: $(date)"
        echo "平均响应时间: ${avg_time}ms"
        echo "P95响应时间: ${p95_time}ms"
        echo "成功率: ${success_rate}%"
        echo "总测试次数: $iterations"
        echo "---"
    } >> "$OUTPUT_DIR/api_performance_results.txt"
}

# 数据库性能测试
test_database_performance() {
    info "开始数据库性能测试..."
    
    # 测试各种查询
    local test_queries=(
        '{"query": "SELECT COUNT(*) FROM users", "name": "用户总数查询"}'
        '{"query": "SELECT * FROM health_data ORDER BY measurement_time DESC LIMIT 10", "name": "最新健康数据"}'
        '{"query": "SELECT u.real_name, COUNT(h.record_id) as health_records FROM users u LEFT JOIN health_data h ON u.user_id = h.user_id GROUP BY u.user_id", "name": "用户健康记录统计"}'
    )
    
    for query_info in "${test_queries[@]}"; do
        local query=$(echo "$query_info" | jq -r '.query')
        local name=$(echo "$query_info" | jq -r '.name')
        
        log "测试查询: $name"
        
        # 这里应该调用实际的数据库查询API
        # 示例：使用SQL查询API
        local response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "{\"sql\": \"$query\"}" \
            "$API_BASE_URL/api/v1/db/query")
        
        local query_time=$(echo "$response" | jq -r '.execution_time // "unknown"')
        local record_count=$(echo "$response" | jq -r '.record_count // "unknown"')
        
        log "  执行时间: ${query_time}ms"
        log "  记录数: $record_count"
        
        {
            echo "查询: $name"
            echo "SQL: $query"
            echo "执行时间: ${query_time}ms"
            echo "记录数: $record_count"
            echo "---"
        } >> "$OUTPUT_DIR/db_performance_results.txt"
    done
}

# 负载测试
run_load_test() {
    local concurrent_users="$1"
    local duration="$2"
    
    info "开始负载测试: 并发用户=$concurrent_users, 持续时间=${duration}s"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration))
    
    # 启动多个并发进程
    local pids=()
    for ((i=1; i<=concurrent_users; i++)); do
        {
            local user_start=$(date +%s)
            local request_count=0
            local error_count=0
            
            while [[ $(date +%s) -lt $end_time ]]; do
                # 模拟用户操作
                curl -s -w "%{http_code}" -o /dev/null \
                    "$API_BASE_URL/api/v1/users/profile" 2>/dev/null
                
                local http_code=$?
                if [[ $http_code -ne 200 ]]; then
                    ((error_count++))
                fi
                
                ((request_count++))
                sleep 1
            done
            
            echo "User $i: Requests=$request_count, Errors=$error_count" >> "$OUTPUT_DIR/load_test_user_stats.txt"
        } &
        
        pids+=($!)
        
        # 控制启动速率，避免同时启动
        sleep 0.1
    done
    
    info "已启动 $concurrent_users 个并发用户进程"
    
    # 等待所有进程完成
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    info "负载测试完成"
    
    # 分析结果
    if [[ -f "$OUTPUT_DIR/load_test_user_stats.txt" ]]; then
        local total_requests=$(grep -o 'Requests=[0-9]*' "$OUTPUT_DIR/load_test_user_stats.txt" | grep -o '[0-9]*' | awk '{sum += $1} END {print sum}')
        local total_errors=$(grep -o 'Errors=[0-9]*' "$OUTPUT_DIR/load_test_user_stats.txt" | grep -o '[0-9]*' | awk '{sum += $1} END {print sum}')
        local error_rate=$(echo "scale=2; $total_errors * 100 / $total_requests" | bc -l)
        
        log "负载测试结果:"
        log "  总请求数: $total_requests"
        log "  总错误数: $total_errors"
        log "  错误率: ${error_rate}%"
    fi
}

# 系统资源监控
monitor_system_resources() {
    info "开始系统资源监控..."
    
    local start_time=$(date +%s)
    local end_time=$((start_time + MONITORING_DURATION))
    
    {
        echo "时间,CPU使用率(%),内存使用率(%),磁盘使用率(%),网络连接数"
        while [[ $(date +%s) -lt $end_time ]]; do
            local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
            local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
            local disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
            local conn_count=$(netstat -tn 2>/dev/null | grep ESTABLISHED | wc -l)
            
            echo "$(date +'%Y-%m-%d %H:%M:%S'),$cpu_usage,$mem_usage,$disk_usage,$conn_count"
            
            sleep $METRICS_INTERVAL
        done
    } > "$OUTPUT_DIR/system_resources.csv"
    
    info "系统资源监控完成，数据保存到: $OUTPUT_DIR/system_resources.csv"
}

# 生成性能报告
generate_performance_report() {
    info "生成性能报告..."
    
    local report_file="$OUTPUT_DIR/performance_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 养老智能体系统性能测试报告

**生成时间**: $(date)  
**测试时长**: ${MONITORING_DURATION}秒  
**监控间隔**: ${METRICS_INTERVAL}秒  

## 测试环境

- **API服务器**: $API_BASE_URL
- **测试日期**: $(date)
- **系统负载**: $(uptime)

## 测试结果摘要

### API性能测试

EOF

    if [[ -f "$OUTPUT_DIR/api_performance_results.txt" ]]; then
        cat "$OUTPUT_DIR/api_performance_results.txt" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

### 数据库性能测试

EOF
    
    if [[ -f "$OUTPUT_DIR/db_performance_results.txt" ]]; then
        cat "$OUTPUT_DIR/db_performance_results.txt" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

### 系统资源使用情况

EOF
    
    if [[ -f "$OUTPUT_DIR/system_resources.csv" ]]; then
        echo "资源监控数据已保存到: system_resources.csv" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

### 负载测试结果

EOF
    
    if [[ -f "$OUTPUT_DIR/load_test_user_stats.txt" ]]; then
        cat "$OUTPUT_DIR/load_test_user_stats.txt" >> "$report_file"
    fi
    
    log "性能报告已生成: $report_file"
}

# 主函数
main() {
    local command="$1"
    
    case "$command" in
        "check")
            check_requirements
            ;;
        "api")
            check_requirements
            test_api_performance "$2" "$3" "$4" "$5"
            ;;
        "database")
            check_requirements
            test_database_performance
            ;;
        "load")
            check_requirements
            run_load_test "${2:-10}" "${3:-60}"
            ;;
        "monitor")
            check_requirements
            monitor_system_resources
            ;;
        "full")
            check_requirements
            info "开始完整性能测试..."
            test_api_performance "/api/v1/users/profile" "GET" "" 50
            test_api_performance "/api/v1/health/data" "GET" "" 50
            test_database_performance
            run_load_test 20 120
            monitor_system_resources
            generate_performance_report
            ;;
        "report")
            generate_performance_report
            ;;
        "help"|"-h"|"--help")
            echo "养老智能体系统性能监控工具"
            echo ""
            echo "使用方法:"
            echo "  $0 check                    - 检查系统要求"
            echo "  $0 api [endpoint] [method] [data] [iterations]  - API性能测试"
            echo "  $0 database                 - 数据库性能测试"
            echo "  $0 load [users] [duration] - 负载测试"
            echo "  $0 monitor                  - 系统资源监控"
            echo "  $0 full                     - 完整性能测试"
            echo "  $0 report                   - 生成性能报告"
            echo "  $0 help                     - 显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 check"
            echo "  $0 api /api/v1/users/profile GET '' 100"
            echo "  $0 api /api/v1/health/data POST '{\"user_id\":123}' 50"
            echo "  $0 load 50 300"
            echo "  $0 full"
            ;;
        *)
            error "未知命令: $command"
            echo "使用 '$0 help' 查看帮助信息"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
