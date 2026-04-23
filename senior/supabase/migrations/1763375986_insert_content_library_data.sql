-- Migration: insert_content_library_data
-- Created at: 1763375986

-- 内容库Mock数据（新闻、音乐、视频、文学）

INSERT INTO content_library (content_type, title, description, content_url, category, tags, target_age_group, emotional_tone, duration_minutes, rating) VALUES
-- 健康养生新闻
('news', '秋季养生：老年人如何预防感冒', '专家建议老年人秋季要注意保暖，多喝温水，适当运动增强体质', 'https://example.com/news/1', '健康养生', ARRAY['养生', '健康', '秋季'], '60+', 'informative', 5, 4.5),
('news', '晨练的最佳时间：不是越早越好', '研究表明，老年人晨练不宜过早，最好在太阳升起后进行', 'https://example.com/news/2', '健康养生', ARRAY['运动', '晨练', '健康'], '60+', 'informative', 3, 4.3),
('news', '老年人膳食指南：每天应该吃什么', '营养专家推荐老年人的一日三餐科学搭配方案', 'https://example.com/news/3', '健康养生', ARRAY['饮食', '营养', '健康'], '60+', 'informative', 8, 4.6),
('news', '走路是最好的运动：每天走多少步合适', '医生建议老年人每天步行6000-8000步最为适宜', 'https://example.com/news/4', '健康养生', ARRAY['运动', '步行', '健康'], '60+', 'encouraging', 5, 4.4),
('news', '老年人睡眠质量改善小贴士', '良好的睡眠对健康至关重要，分享改善睡眠的实用方法', 'https://example.com/news/5', '健康养生', ARRAY['睡眠', '健康', '养生'], '60+', 'comforting', 6, 4.5),
-- 政策福利新闻
('news', '2025年养老金上调方案公布', '今年养老金上调幅度为3.8%，惠及1.3亿退休人员', 'https://example.com/news/6', '政策福利', ARRAY['养老金', '政策', '福利'], '60+', 'uplifting', 5, 4.7),
('news', '老年人免费体检项目增加', '各地社区医院为老年人提供更多免费体检项目', 'https://example.com/news/7', '政策福利', ARRAY['体检', '福利', '健康'], '60+', 'uplifting', 4, 4.5),
('news', '社区养老服务中心正式启用', '为老年人提供日间照料、康复训练等服务', 'https://example.com/news/8', '政策福利', ARRAY['社区', '养老', '服务'], '60+', 'uplifting', 6, 4.6),
('news', '老年人乘坐公交地铁优惠政策', '65岁以上老人可免费乘坐公共交通', 'https://example.com/news/9', '政策福利', ARRAY['交通', '优惠', '政策'], '60+', 'uplifting', 3, 4.4),
('news', '老年大学秋季招生开始', '各类兴趣课程丰富多彩，欢迎老年朋友报名', 'https://example.com/news/10', '政策福利', ARRAY['教育', '学习', '兴趣'], '60+', 'inspiring', 5, 4.5),
-- 社会新闻
('news', '社区举办重阳节庆祝活动', '丰富多彩的文艺表演和互动游戏温暖人心', 'https://example.com/news/11', '社会新闻', ARRAY['节日', '社区', '活动'], '60+', 'joyful', 4, 4.6),
('news', '志愿者为独居老人送温暖', '大学生志愿者定期看望独居老人，提供生活帮助', 'https://example.com/news/12', '社会新闻', ARRAY['志愿者', '关爱', '温暖'], '60+', 'comforting', 5, 4.7),
('news', '社区开设智能手机培训班', '帮助老年人学会使用智能手机和微信', 'https://example.com/news/13', '社会新闻', ARRAY['科技', '学习', '培训'], '60+', 'encouraging', 6, 4.5),
('news', '公园新增适老化健身器材', '更安全、更人性化的设计受到老年人欢迎', 'https://example.com/news/14', '社会新闻', ARRAY['健身', '公园', '设施'], '60+', 'uplifting', 4, 4.4),
('news', '老年人防诈骗讲座进社区', '警察叔叔教老年人识别常见骗局', 'https://example.com/news/15', '社会新闻', ARRAY['安全', '防骗', '教育'], '60+', 'informative', 7, 4.6),
-- 音乐内容
('music', '我的祖国', '经典爱国歌曲，旋律优美动听', 'https://example.com/music/1.mp3', '红色经典', ARRAY['爱国', '经典', '民歌'], '60+', 'inspiring', 4, 4.8),
('music', '在那桃花盛开的地方', '著名军旅歌曲，充满青春回忆', 'https://example.com/music/2.mp3', '红色经典', ARRAY['军旅', '经典', '回忆'], '60+', 'nostalgic', 3, 4.7),
('music', '草原上升起不落的太阳', '悠扬的草原歌曲，心旷神怡', 'https://example.com/music/3.mp3', '民歌经典', ARRAY['草原', '民歌', '经典'], '60+', 'peaceful', 4, 4.6),
('music', '月亮代表我的心', '邓丽君经典情歌，温柔动人', 'https://example.com/music/4.mp3', '流行老歌', ARRAY['情歌', '经典', '邓丽君'], '60+', 'romantic', 3, 4.9),
('music', '茉莉花', '中国经典民歌，优美动听', 'https://example.com/music/5.mp3', '民歌经典', ARRAY['民歌', '传统', '优美'], '60+', 'peaceful', 3, 4.7),
('music', '敢问路在何方', '西游记主题曲，激昂有力', 'https://example.com/music/6.mp3', '影视金曲', ARRAY['电视剧', '经典', '励志'], '60+', 'energetic', 4, 4.8),
('music', '我和我的祖国', '深情的爱国歌曲，感人至深', 'https://example.com/music/7.mp3', '红色经典', ARRAY['爱国', '深情', '经典'], '60+', 'inspiring', 4, 4.9),
('music', '小城故事', '邓丽君演唱，温馨动人', 'https://example.com/music/8.mp3', '流行老歌', ARRAY['邓丽君', '温馨', '怀旧'], '60+', 'comforting', 3, 4.7),
('music', '好人一生平安', '渴望主题曲，祝福歌曲', 'https://example.com/music/9.mp3', '影视金曲', ARRAY['电视剧', '祝福', '温暖'], '60+', 'comforting', 3, 4.6),
('music', '梁祝', '小提琴协奏曲，凄美动人', 'https://example.com/music/10.mp3', '器乐名曲', ARRAY['小提琴', '古典', '名曲'], '60+', 'melancholic', 26, 4.9),
-- 视频内容
('video', '八段锦健身操完整教学', '适合老年人的传统养生功法，简单易学', 'https://example.com/video/1.mp4', '健康养生', ARRAY['健身', '养生', '教学'], '60+', 'encouraging', 15, 4.7),
('video', '太极拳24式入门教程', '太极拳初学者教程，动作详细讲解', 'https://example.com/video/2.mp4', '健康养生', ARRAY['太极', '运动', '教学'], '60+', 'peaceful', 30, 4.8),
('video', '老年人科学饮食讲座', '营养专家讲解老年人饮食注意事项', 'https://example.com/video/3.mp4', '健康养生', ARRAY['饮食', '营养', '讲座'], '60+', 'informative', 45, 4.6),
('video', '京剧名段欣赏：贵妃醉酒', '梅派经典剧目，艺术价值极高', 'https://example.com/video/4.mp4', '戏曲欣赏', ARRAY['京剧', '经典', '艺术'], '60+', 'cultural', 20, 4.8),
('video', '舌尖上的中国：传统美食', '纪录片展现中国传统美食文化', 'https://example.com/video/5.mp4', '纪录片', ARRAY['美食', '文化', '传统'], '60+', 'nostalgic', 50, 4.9),
('video', '养生按摩手法教学', '简单实用的日常保健按摩方法', 'https://example.com/video/6.mp4', '健康养生', ARRAY['按摩', '保健', '教学'], '60+', 'comforting', 20, 4.5),
('video', '书法入门：楷书基础', '书法大师教授楷书基本笔画', 'https://example.com/video/7.mp4', '文化艺术', ARRAY['书法', '艺术', '教学'], '60+', 'cultural', 35, 4.6),
('video', '老年人防跌倒指南', '专业康复师讲解如何预防跌倒', 'https://example.com/video/8.mp4', '健康养生', ARRAY['安全', '预防', '健康'], '60+', 'informative', 25, 4.7),
('video', '园艺种植小技巧', '在家种植花草蔬菜的实用方法', 'https://example.com/video/9.mp4', '生活技能', ARRAY['园艺', '种植', '生活'], '60+', 'peaceful', 18, 4.5),
('video', '中国古典园林赏析', '欣赏苏州园林的独特魅力', 'https://example.com/video/10.mp4', '纪录片', ARRAY['园林', '文化', '艺术'], '60+', 'peaceful', 40, 4.7),
-- 文学内容
('literature', '静夜思', '李白的经典诗作，思乡之情跃然纸上', NULL, '古诗词', ARRAY['李白', '唐诗', '思乡'], '60+', 'nostalgic', 2, 4.9),
('literature', '登鹳雀楼', '王之涣的名篇，境界开阔', NULL, '古诗词', ARRAY['王之涣', '唐诗', '励志'], '60+', 'inspiring', 2, 4.8),
('literature', '人生感悟：活到老学到老', '关于终身学习的人生智慧分享', NULL, '人生感悟', ARRAY['学习', '智慧', '人生'], '60+', 'inspiring', 5, 4.6),
('literature', '养生之道：顺应自然', '传统养生理念，强调与自然和谐相处', NULL, '养生文章', ARRAY['养生', '健康', '传统'], '60+', 'peaceful', 8, 4.7),
('literature', '回忆录：那些年的故事', '普通人讲述自己的青春岁月', NULL, '回忆录', ARRAY['回忆', '故事', '怀旧'], '60+', 'nostalgic', 15, 4.5),
('literature', '春江花月夜', '张若虚的千古绝唱，意境优美', NULL, '古诗词', ARRAY['张若虚', '唐诗', '月夜'], '60+', 'peaceful', 5, 4.9),
('literature', '水调歌头·明月几时有', '苏轼的中秋名作，豁达洒脱', NULL, '古诗词', ARRAY['苏轼', '宋词', '中秋'], '60+', 'nostalgic', 3, 4.8),
('literature', '长寿秘诀：心态最重要', '专家谈长寿的心理因素', NULL, '养生文章', ARRAY['长寿', '心态', '健康'], '60+', 'encouraging', 10, 4.6),
('literature', '茶道文化：品茶品人生', '介绍中国茶文化的深厚底蕴', NULL, '文化艺术', ARRAY['茶道', '文化', '传统'], '60+', 'peaceful', 12, 4.7),
('literature', '孝道故事：二十四孝', '传统孝道文化故事集锦', NULL, '传统故事', ARRAY['孝道', '传统', '美德'], '60+', 'inspiring', 20, 4.5);;