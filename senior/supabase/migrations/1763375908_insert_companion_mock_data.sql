-- Migration: insert_companion_mock_data
-- Created at: 1763375908

-- 情感陪伴功能Mock数据创建脚本（第1批：认知游戏、内容库、虚拟宠物）

DO $$
DECLARE
  test_user_id UUID := '94547eee-5f39-4f76-a08e-ba4540a101ae';
BEGIN

-- 插入50种认知训练游戏
INSERT INTO cognitive_games (game_name, game_type, difficulty_level, description, game_config, cognitive_area, recommended_duration, instructions) VALUES
('数字记忆挑战', 'memory', 'easy', '记住屏幕上闪现的数字序列', '{"sequence_length": 4, "display_time": 3}', '短期记忆', 5, '仔细观看数字，然后按顺序输入'),
('图片配对游戏', 'memory', 'easy', '翻开卡片找到相同的图片', '{"pairs": 6, "time_limit": 120}', '视觉记忆', 10, '点击卡片翻开，找到所有配对'),
('故事回忆', 'memory', 'medium', '听完故事后回答问题', '{"story_length": "short", "questions": 5}', '语义记忆', 15, '认真听故事，记住关键信息'),
('电话号码记忆', 'memory', 'easy', '记住显示的电话号码', '{"digits": 11, "display_time": 5}', '数字记忆', 5, '记住号码后正确输入'),
('人脸记忆游戏', 'memory', 'medium', '记住看过的人脸', '{"faces": 8, "time_per_face": 3}', '人脸识别记忆', 12, '仔细观察每张脸的特征'),
('找不同', 'attention', 'easy', '在两张图片中找出不同之处', '{"differences": 5, "time_limit": 60}', '视觉注意力', 8, '仔细对比两张图，找出所有不同'),
('快速点击', 'attention', 'medium', '快速点击指定的图标', '{"targets": 20, "time_limit": 30}', '选择性注意力', 5, '看到目标图标就快速点击'),
('声音辨别', 'attention', 'easy', '听声音识别物品', '{"sounds": 10}', '听觉注意力', 10, '仔细听声音，选择对应的物品'),
('颜色追踪', 'attention', 'medium', '追踪移动的彩色球', '{"balls": 3, "speed": "medium"}', '动态注意力', 7, '眼睛跟随彩色球的移动'),
('文字搜索', 'attention', 'easy', '在文字中找到指定的词', '{"words": 5, "text_length": 200}', '阅读注意力', 10, '快速浏览找到目标词语'),
('加减法练习', 'calculation', 'easy', '简单的加减法心算', '{"range": [1, 20], "questions": 10}', '基础运算', 8, '快速心算得出答案'),
('购物找零', 'calculation', 'medium', '模拟购物计算找零', '{"scenarios": 5, "max_amount": 100}', '实用计算', 12, '计算需要找零的金额'),
('时间计算', 'calculation', 'easy', '计算时间间隔', '{"questions": 8}', '时间运算', 10, '计算时间差或到达时间'),
('乘法口诀', 'calculation', 'easy', '九九乘法表练习', '{"range": [1, 9], "questions": 15}', '乘法运算', 10, '快速回答乘法问题'),
('数独入门', 'calculation', 'medium', '4x4简化数独游戏', '{"grid_size": 4}', '逻辑推理', 15, '填入1-4，每行每列不重复'),
('位置记忆', 'memory', 'easy', '记住物品的位置', '{"items": 6, "grid": "3x3"}', '空间记忆', 8, '记住每个物品在哪个格子里'),
('顺序记忆', 'memory', 'medium', '按顺序点击亮起的方块', '{"sequence_length": 5}', '序列记忆', 10, '记住方块亮起的顺序'),
('词语记忆', 'memory', 'easy', '记住一组相关词语', '{"words": 8, "time": 15}', '词汇记忆', 10, '仔细记住所有词语'),
('音乐记忆', 'memory', 'medium', '记住旋律并识别', '{"melodies": 5}', '听觉记忆', 12, '仔细听旋律，找出重复的'),
('路线记忆', 'memory', 'hard', '记住地图上的路线', '{"steps": 8, "landmarks": 5}', '导航记忆', 15, '记住从起点到终点的路线'),
('颜色文字冲突', 'attention', 'hard', '说出字的颜色而非字义', '{"items": 20}', '抑制控制', 10, '快速说出文字的颜色'),
('符号匹配', 'attention', 'medium', '找到相同的符号', '{"symbols": 12}', '视觉搜索', 8, '快速找到匹配的符号'),
('数字划消', 'attention', 'easy', '划掉所有指定数字', '{"target": 7, "grid": "10x10"}', '持续注意力', 10, '找到并划掉所有目标数字'),
('节奏记忆', 'attention', 'medium', '跟随节奏拍打', '{"patterns": 5}', '节奏感知', 8, '听节奏后准确复制'),
('分类游戏', 'attention', 'easy', '快速分类物品', '{"categories": 3, "items": 15}', '认知灵活性', 10, '将物品放入正确的类别'),
('连续加法', 'calculation', 'medium', '连续加一个数字', '{"start": 7, "add": 8, "steps": 10}', '心算能力', 8, '从7开始，连续加8'),
('分数比较', 'calculation', 'hard', '比较分数大小', '{"questions": 10}', '分数运算', 12, '判断哪个分数更大'),
('货币换算', 'calculation', 'medium', '不同货币换算', '{"questions": 10}', '单位换算', 10, '计算不同货币的等值'),
('百分比计算', 'calculation', 'hard', '简单百分比问题', '{"questions": 8}', '百分比运算', 12, '计算折扣或增长百分比'),
('估算练习', 'calculation', 'medium', '快速估算结果', '{"questions": 10}', '估算能力', 10, '不用精确计算，快速估算'),
('反应速度测试', 'attention', 'easy', '测试反应时间', '{"trials": 10}', '反应速度', 5, '看到信号立即点击'),
('记忆算术', 'calculation', 'hard', '记住数字后计算', '{"numbers": 4}', '工作记忆+计算', 10, '记住数字后求和'),
('视觉扫描', 'attention', 'medium', '快速扫描找目标', '{"targets": 3, "distractors": 20}', '视觉搜索', 8, '在众多干扰中找到目标'),
('逻辑推理', 'calculation', 'hard', '根据线索推理答案', '{"clues": 4, "options": 4}', '逻辑思维', 15, '分析线索找出正确答案'),
('图形推理', 'calculation', 'medium', '找出图形规律', '{"patterns": 5}', '模式识别', 12, '观察图形找出规律'),
('连连看', 'attention', 'easy', '消除相同图案', '{"pairs": 8}', '视觉搜索', 12, '连接相同图案消除'),
('拼图游戏', 'memory', 'medium', '完成图片拼图', '{"pieces": 9}', '空间认知', 15, '拖动拼图块完成图片'),
('汉字组词', 'memory', 'medium', '用汉字组成词语', '{"characters": 12, "words": 6}', '语言能力', 10, '选择汉字组成正确词语'),
('成语接龙', 'memory', 'hard', '根据成语接龙', '{"starting": "一心一意"}', '成语记忆', 12, '说出首字相同的成语'),
('古诗填空', 'memory', 'medium', '填写古诗缺失的字', '{"poems": 5, "blanks": 2}', '古诗记忆', 10, '回忆古诗填入正确的字'),
('超市购物', 'calculation', 'easy', '模拟超市购物结账', '{"items": 5, "budget": 100}', '实用计算', 10, '计算总价和找零'),
('日期计算', 'calculation', 'medium', '计算日期相关问题', '{"questions": 8}', '日期运算', 10, '计算日期间隔或未来日期'),
('菜谱记忆', 'memory', 'medium', '记住菜谱的步骤', '{"dishes": 3, "steps": 5}', '程序记忆', 12, '记住做菜的顺序'),
('亲友生日', 'memory', 'easy', '记住家人朋友生日', '{"people": 8}', '日期记忆', 10, '记住每个人的生日'),
('药物管理', 'attention', 'medium', '记住吃药时间和剂量', '{"medications": 4}', '时间管理', 10, '正确安排服药时间'),
('猜谜语', 'calculation', 'medium', '根据提示猜谜底', '{"riddles": 10}', '联想思维', 12, '仔细思考谜语的答案'),
('脑筋急转弯', 'calculation', 'hard', '创意思维题', '{"questions": 8}', '创造性思维', 10, '换个角度思考问题'),
('找规律', 'calculation', 'medium', '数字或图形找规律', '{"sequences": 10}', '归纳推理', 10, '观察找出数列规律'),
('迷宫寻路', 'attention', 'medium', '在迷宫中找到出口', '{"size": "medium"}', '空间规划', 12, '找到从入口到出口的路径'),
('七巧板', 'memory', 'hard', '用七巧板拼图', '{"patterns": 5}', '空间想象', 20, '用7块板拼出指定图形');

-- 插入虚拟宠物
INSERT INTO virtual_pets (user_id, pet_type, pet_name, appearance_config, personality_traits, mood_state, growth_level, bond_strength) VALUES
(test_user_id, 'cat', '咪咪', '{"color": "橘色", "size": "中等", "features": ["圆圆的眼睛", "柔软的毛发"]}', '{"friendly": 0.9, "playful": 0.8, "gentle": 0.9}', 'happy', 5, 75),
(test_user_id, 'dog', '旺财', '{"breed": "金毛", "color": "金黄色", "size": "大型"}', '{"loyal": 1.0, "energetic": 0.9, "protective": 0.8}', 'excited', 7, 85),
(test_user_id, 'bird', '小黄', '{"species": "金丝雀", "color": "黄色", "size": "小巧"}', '{"cheerful": 0.9, "musical": 0.8, "social": 0.7}', 'joyful', 3, 60),
(test_user_id, 'fish', '金鱼', '{"type": "金鱼", "color": "红白相间", "fins": "飘逸"}', '{"calm": 1.0, "elegant": 0.8, "peaceful": 0.9}', 'peaceful', 4, 55),
(test_user_id, 'hamster', '豆豆', '{"color": "棕色", "size": "迷你", "features": ["圆鼓鼓的腮帮"]}', '{"cute": 1.0, "curious": 0.8, "timid": 0.6}', 'curious', 2, 50),
(test_user_id, 'rabbit', '雪球', '{"breed": "垂耳兔", "color": "纯白", "size": "中等"}', '{"gentle": 0.9, "shy": 0.7, "adorable": 1.0}', 'content', 6, 70),
(test_user_id, 'parrot', '彩虹', '{"species": "鹦鹉", "color": "五彩斑斓", "size": "中等"}', '{"talkative": 0.9, "smart": 0.9, "playful": 0.8}', 'chatty', 8, 80),
(test_user_id, 'turtle', '小龟', '{"species": "巴西龟", "shell": "绿色硬壳", "size": "小型"}', '{"patient": 1.0, "wise": 0.8, "steady": 0.9}', 'relaxed', 10, 90),
(test_user_id, 'cat', '虎妞', '{"color": "虎斑", "size": "中等", "features": ["炯炯有神的眼睛"]}', '{"independent": 0.8, "smart": 0.9, "curious": 0.8}', 'content', 5, 65),
(test_user_id, 'dog', '豆豆', '{"breed": "泰迪", "color": "棕色", "size": "小型"}', '{"affectionate": 0.9, "playful": 0.9, "sweet": 1.0}', 'cheerful', 4, 72);

END $$;;