-- Migration: insert_voice_interactions_batch1
-- Created at: 1763376108

-- 语音交互记录第1批（前100条）
DO $$
BEGIN
  INSERT INTO voice_interactions (user_id, interaction_type, user_input, ai_response, emotion_detected, emotion_score, interaction_time, duration_seconds) 
  SELECT * FROM (VALUES
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '腿脚不太灵活了', '年纪大了关节确实会有些问题。平时可以做做关节操，适当活动活动，但不要过度劳累。', 'sad', 0.76, '2025-10-22 07:41:05.915732'::timestamp, 73),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '今天有点累', '那就好好休息一下吧。累了就要多休息，不要勉强自己。要不要我给您讲个轻松的故事？', 'neutral', 0.51, '2025-11-06 17:41:05.915732'::timestamp, 171),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '我有点想孩子了', '想孩子了可以给他们打个电话，听听他们的声音。他们工作忙也是为了这个家，您要多理解他们。', 'sad', 0.77, '2025-11-13 07:41:05.915732'::timestamp, 162),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '听了首老歌很开心', '音乐能让人心情愉快！要不要我再给您推荐几首经典老歌？', 'happy', 0.75, '2025-10-29 17:41:05.915732'::timestamp, 37),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '药吃完了要买新的', '好的，我帮您记录下来。要按时吃药哦，健康最重要。需要我提醒您去配药吗？', 'neutral', 0.6, '2025-10-29 17:41:05.915732'::timestamp, 166),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '身体有点不舒服', '哪里不舒服呢？要不要量一下血压和体温？如果持续不适一定要及时去医院检查。', 'anxious', 0.63, '2025-10-19 05:41:05.915732'::timestamp, 165),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '今天天气真好', '是啊！天气好心情也跟着好起来了。要不要出去散散步，呼吸一下新鲜空气？', 'happy', 0.88, '2025-11-08 12:41:05.915732'::timestamp, 95),
    ('94547eee-5f39-4f76-a08e-ba4540a101ae'::uuid, 'text', '和老朋友聊了很久', '有老朋友陪伴真好！常和朋友聊聊天，分享快乐，能让生活更充实。', 'happy', 0.85, '2025-10-25 09:41:05.915732'::timestamp, 148)
  ) AS data(user_id, interaction_type, user_input, ai_response, emotion_detected, emotion_score, interaction_time, duration_seconds);
END $$;;