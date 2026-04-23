/**
 * 前端性能测试工具
 * 用于测试网页加载性能、Core Web Vitals等指标
 */

class FrontendPerformanceTester {
    constructor(options = {}) {
        this.options = {
            url: options.url || window.location.href,
            iterations: options.iterations || 5,
            thresholds: {
                // Core Web Vitals阈值
                fcp: 1000,    // First Contentful Paint < 1s
                lcp: 2500,    // Largest Contentful Paint < 2.5s
                fid: 100,     // First Input Delay < 100ms
                cls: 0.1,     // Cumulative Layout Shift < 0.1
                
                // 其他性能指标
                ttfb: 200,    // Time to First Byte < 200ms
                domReady: 1000, // DOM Ready < 1s
                loadComplete: 3000 // Load Complete < 3s
            },
            ...options
        };
        
        this.results = {
            coreWebVitals: {},
            navigationTimings: [],
            resourceTimings: [],
            customMetrics: [],
            summary: {}
        };
        
        this.testFrames = [];
    }

    /**
     * 执行完整性能测试
     */
    async runFullTest() {
        console.log('🚀 开始前端性能测试...');
        
        try {
            // 测试导航性能
            await this.testNavigationPerformance();
            
            // 测试Core Web Vitals
            await this.testCoreWebVitals();
            
            // 测试资源加载
            await this.testResourceLoading();
            
            // 测试交互性能
            await this.testInteractionPerformance();
            
            // 生成报告
            this.generateReport();
            
            console.log('✅ 前端性能测试完成');
            
        } catch (error) {
            console.error('❌ 性能测试失败:', error);
            throw error;
        }
    }

    /**
     * 测试导航性能
     */
    async testNavigationPerformance() {
        console.log('📊 测试导航性能...');
        
        const timings = [];
        
        for (let i = 0; i < this.options.iterations; i++) {
            const frame = await this.createTestFrame();
            this.testFrames.push(frame);
            
            // 等待页面加载完成
            await new Promise((resolve) => {
                frame.onload = resolve;
                frame.src = this.options.url;
            });
            
            // 获取性能数据
            const perfData = frame.contentWindow.performance.getEntriesByType('navigation')[0];
            timings.push(this.extractNavigationTiming(perfData));
            
            console.log(`  进度: ${i + 1}/${this.options.iterations}`);
        }
        
        this.results.navigationTimings = timings;
        this.calculateNavigationSummary();
    }

    /**
     * 测试Core Web Vitals
     */
    async testCoreWebVitals() {
        console.log('📈 测试Core Web Vitals...');
        
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                this.processWebVital(entry);
            }
        });
        
        // 监听各种性能指标
        observer.observe({ type: 'paint', buffered: true });
        observer.observe({ type: 'largest-contentful-paint', buffered: true });
        observer.observe({ type: 'first-input', buffered: true });
        observer.observe({ type: 'layout-shift', buffered: true });
        
        // 等待测量完成
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        observer.disconnect();
    }

    /**
     * 测试资源加载性能
     */
    async testResourceLoading() {
        console.log('📦 测试资源加载性能...');
        
        const resourceTypes = ['script', 'stylesheet', 'image', 'font'];
        const resourceTimings = {};
        
        for (const type of resourceTypes) {
            const resources = this.getResourcesByType(type);
            const timings = resources.map(resource => ({
                name: resource.name,
                size: resource.transferSize || 0,
                duration: resource.duration,
                decodedBodySize: resource.decodedBodySize || 0
            }));
            
            resourceTimings[type] = timings;
        }
        
        this.results.resourceTimings = resourceTimings;
    }

    /**
     * 测试交互性能
     */
    async testInteractionPerformance() {
        console.log('👆 测试交互性能...');
        
        const frame = this.testFrames[0]; // 使用第一个测试帧
        
        if (!frame) {
            throw new Error('没有可用的测试帧');
        }
        
        const document = frame.contentDocument;
        const window = frame.contentWindow;
        
        // 测试各种交互操作
        const interactions = [
            { action: 'click', selector: 'button, a, [role="button"]' },
            { action: 'scroll', selector: 'body' },
            { action: 'hover', selector: 'a, button' }
        ];
        
        const interactionResults = [];
        
        for (const interaction of interactions) {
            const element = document.querySelector(interaction.selector);
            if (element) {
                const start = performance.now();
                
                if (interaction.action === 'click') {
                    element.click();
                } else if (interaction.action === 'scroll') {
                    window.scrollTo(0, document.body.scrollHeight / 2);
                } else if (interaction.action === 'hover') {
                    // 模拟hover效果
                    const event = new window.MouseEvent('mouseenter', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(event);
                }
                
                const duration = performance.now() - start;
                interactionResults.push({
                    action: interaction.action,
                    selector: interaction.selector,
                    duration: duration
                });
            }
        }
        
        this.results.interactionResults = interactionResults;
    }

    /**
     * 提取导航时间线数据
     */
    extractNavigationTiming(perfEntry) {
        const timing = perfEntry;
        
        return {
            // DNS查询时间
            dnsTime: timing.domainLookupEnd - timing.domainLookupStart,
            
            // TCP连接时间
            tcpTime: timing.connectEnd - timing.connectStart,
            
            // 请求响应时间
            requestTime: timing.responseStart - timing.requestStart,
            
            // 响应下载时间
            downloadTime: timing.responseEnd - timing.responseStart,
            
            // DOM处理时间
            domProcessingTime: timing.domContentLoadedEventEnd - timing.responseEnd,
            
            // 首字节时间 (TTFB)
            ttfb: timing.responseStart - timing.navigationStart,
            
            // DOM加载完成时间
            domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
            
            // 完全加载时间
            loadComplete: timing.loadEventEnd - timing.navigationStart,
            
            // 重定向时间
            redirectTime: timing.redirectEnd - timing.redirectStart
        };
    }

    /**
     * 处理Web Vitals数据
     */
    processWebVital(entry) {
        switch (entry.entryType) {
            case 'paint':
                if (entry.name === 'first-contentful-paint') {
                    this.results.coreWebVitals.fcp = entry.startTime;
                }
                break;
                
            case 'largest-contentful-paint':
                this.results.coreWebVitals.lcp = entry.startTime;
                break;
                
            case 'first-input':
                this.results.coreWebVitals.fid = entry.processingStart - entry.startTime;
                break;
                
            case 'layout-shift':
                if (!entry.hadRecentInput) {
                    this.results.coreWebVitals.cls = (this.results.coreWebVitals.cls || 0) + entry.value;
                }
                break;
        }
    }

    /**
     * 按类型获取资源
     */
    getResourcesByType(type) {
        const resourceMap = {
            script: 'script',
            stylesheet: 'link',
            image: 'img',
            font: 'font'
        };
        
        const restype = resourceMap[type];
        if (!restype) return [];
        
        return performance.getEntriesByType('resource')
            .filter(resource => resource.initiatorType === restype);
    }

    /**
     * 计算导航性能总结
     */
    calculateNavigationSummary() {
        const timings = this.results.navigationTimings;
        
        if (timings.length === 0) return;
        
        const keys = Object.keys(timings[0]);
        const summary = {};
        
        for (const key of keys) {
            const values = timings.map(t => t[key]).filter(v => v != null);
            if (values.length > 0) {
                summary[key] = {
                    avg: values.reduce((a, b) => a + b, 0) / values.length,
                    min: Math.min(...values),
                    max: Math.max(...values),
                    p95: this.percentile(values, 95)
                };
            }
        }
        
        this.results.summary.navigation = summary;
    }

    /**
     * 计算百分位数
     */
    percentile(values, p) {
        const sorted = [...values].sort((a, b) => a - b);
        const index = Math.ceil((p / 100) * sorted.length) - 1;
        return sorted[index];
    }

    /**
     * 创建测试iframe
     */
    createTestFrame() {
        const frame = document.createElement('iframe');
        frame.style.cssText = `
            position: absolute;
            top: -9999px;
            left: -9999px;
            width: 800px;
            height: 600px;
            border: none;
        `;
        
        document.body.appendChild(frame);
        return frame;
    }

    /**
     * 评估性能等级
     */
    evaluatePerformance(metric, value) {
        const threshold = this.options.thresholds[metric];
        if (!threshold) return 'unknown';
        
        if (metric === 'cls') {
            // CLS值越小越好
            if (value <= threshold * 0.5) return 'good';
            if (value <= threshold) return 'needs-improvement';
            return 'poor';
        } else {
            // 其他指标值越小越好
            if (value <= threshold * 0.5) return 'good';
            if (value <= threshold) return 'needs-improvement';
            return 'poor';
        }
    }

    /**
     * 生成性能报告
     */
    generateReport() {
        console.log('📋 生成性能报告...');
        
        const report = {
            testInfo: {
                url: this.options.url,
                timestamp: new Date().toISOString(),
                iterations: this.options.iterations,
                userAgent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            },
            
            coreWebVitals: {
                fcp: {
                    value: this.results.coreWebVitals.fcp || 0,
                    rating: this.evaluatePerformance('fcp', this.results.coreWebVitals.fcp || 0),
                    threshold: this.options.thresholds.fcp
                },
                lcp: {
                    value: this.results.coreWebVitals.lcp || 0,
                    rating: this.evaluatePerformance('lcp', this.results.coreWebVitals.lcp || 0),
                    threshold: this.options.thresholds.lcp
                },
                fid: {
                    value: this.results.coreWebVitals.fid || 0,
                    rating: this.evaluatePerformance('fid', this.results.coreWebVitals.fid || 0),
                    threshold: this.options.thresholds.fid
                },
                cls: {
                    value: this.results.coreWebVitals.cls || 0,
                    rating: this.evaluatePerformance('cls', this.results.coreWebVitals.cls || 0),
                    threshold: this.options.thresholds.cls
                }
            },
            
            navigationSummary: this.results.summary.navigation,
            
            resourceAnalysis: this.analyzeResourceTimings(),
            
            recommendations: this.generateRecommendations()
        };
        
        this.displayReport(report);
        this.saveReport(report);
        
        return report;
    }

    /**
     * 分析资源时间线
     */
    analyzeResourceTimings() {
        const analysis = {};
        
        for (const [type, resources] of Object.entries(this.results.resourceTimings)) {
            if (resources.length === 0) continue;
            
            const durations = resources.map(r => r.duration);
            const sizes = resources.map(r => r.size);
            
            analysis[type] = {
                count: resources.length,
                totalSize: sizes.reduce((a, b) => a + b, 0),
                avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
                slowestResource: resources.reduce((prev, current) => 
                    (prev.duration > current.duration) ? prev : current
                )
            };
        }
        
        return analysis;
    }

    /**
     * 生成优化建议
     */
    generateRecommendations() {
        const recommendations = [];
        const vitals = this.results.coreWebVitals;
        
        // 基于Core Web Vitals的推荐
        if (vitals.fcp > this.options.thresholds.fcp) {
            recommendations.push({
                metric: 'FCP',
                issue: '首次内容绘制时间过长',
                suggestions: [
                    '优化关键CSS内联',
                    '压缩和合并CSS文件',
                    '使用CDN加速静态资源',
                    '优化服务器响应时间'
                ]
            });
        }
        
        if (vitals.lcp > this.options.thresholds.lcp) {
            recommendations.push({
                metric: 'LCP',
                issue: '最大内容绘制时间过长',
                suggestions: [
                    '优化最大元素的加载',
                    '使用懒加载非关键内容',
                    '预加载重要资源',
                    '压缩和优化图片'
                ]
            });
        }
        
        if (vitals.fid > this.options.thresholds.fid) {
            recommendations.push({
                metric: 'FID',
                issue: '首次输入延迟过长',
                suggestions: [
                    '减少JavaScript执行时间',
                    '分割大型JavaScript包',
                    '使用Web Workers处理重任务',
                    '优化事件处理器'
                ]
            });
        }
        
        if (vitals.cls > this.options.thresholds.cls) {
            recommendations.push({
                metric: 'CLS',
                issue: '累积布局偏移过大',
                suggestions: [
                    '为所有图片和广告预留空间',
                    '避免在现有内容上方插入内容',
                    '使用transform动画',
                    '固定高度和宽度'
                ]
            });
        }
        
        return recommendations;
    }

    /**
     * 显示性能报告
     */
    displayReport(report) {
        console.log('='.repeat(60));
        console.log('🚀 前端性能测试报告');
        console.log('='.repeat(60));
        
        console.log('\n📊 Core Web Vitals:');
        for (const [metric, data] of Object.entries(report.coreWebVitals)) {
            const rating = this.getRatingEmoji(data.rating);
            console.log(`  ${metric}: ${Math.round(data.value)}ms ${rating} (阈值: ${data.threshold}ms)`);
        }
        
        console.log('\n📈 导航性能摘要:');
        if (report.navigationSummary) {
            for (const [metric, data] of Object.entries(report.navigationSummary)) {
                console.log(`  ${metric}: ${Math.round(data.avg)}ms (P95: ${Math.round(data.p95)}ms)`);
            }
        }
        
        console.log('\n💡 优化建议:');
        if (report.recommendations.length > 0) {
            report.recommendations.forEach(rec => {
                console.log(`  ${rec.metric}: ${rec.issue}`);
                rec.suggestions.forEach(suggestion => {
                    console.log(`    - ${suggestion}`);
                });
            });
        } else {
            console.log('  🎉 性能表现良好，暂无需要优化的问题');
        }
        
        console.log('\n' + '='.repeat(60));
    }

    /**
     * 获取评级表情符号
     */
    getRatingEmoji(rating) {
        switch (rating) {
            case 'good': return '✅';
            case 'needs-improvement': return '⚠️';
            case 'poor': return '❌';
            default: return '❓';
        }
    }

    /**
     * 保存报告到文件
     */
    saveReport(report) {
        const jsonReport = JSON.stringify(report, null, 2);
        
        // 创建下载链接
        const blob = new Blob([jsonReport], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance_report_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        console.log('📄 报告已下载');
    }

    /**
     * 清理测试资源
     */
    cleanup() {
        this.testFrames.forEach(frame => {
            if (frame.parentNode) {
                frame.parentNode.removeChild(frame);
            }
        });
        this.testFrames = [];
    }
}

// 使用示例
/**
 * 执行性能测试的函数
 */
async function runPerformanceTest(url = null, iterations = 5) {
    const tester = new FrontendPerformanceTester({
        url: url || window.location.href,
        iterations: iterations
    });
    
    try {
        const report = await tester.runFullTest();
        return report;
    } catch (error) {
        console.error('性能测试失败:', error);
        throw error;
    } finally {
        tester.cleanup();
    }
}

// 导出到全局作用域
window.PerformanceTester = FrontendPerformanceTester;
window.runPerformanceTest = runPerformanceTest;

// 自动执行测试（如果在浏览器中直接加载）
if (typeof window !== 'undefined' && window.location === window.parent) {
    // 只有在主页面中才自动执行，避免在iframe中重复执行
    console.log('🚀 前端性能测试工具已加载');
    console.log('使用 runPerformanceTest(url, iterations) 开始测试');
}
