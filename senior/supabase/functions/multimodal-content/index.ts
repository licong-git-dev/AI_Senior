import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface MultimodalRequest {
  adviceText: string;
  userPreferences: {
    contentType: 'text' | 'image' | 'audio' | 'video' | 'interactive';
    accessibilityNeeds: string[];
    preferredFormat: string;
    voice?: string;
  };
  contentTypes: string[];
  interventionId?: string;
}

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
  }

  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const requestData: MultimodalRequest = await req.json();
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    );

    const content: any = {
      images: [],
      audio: null,
      video: null,
      interactive: null,
      formatted: []
    };

    // 并行生成各种类型的内容
    const promises = [];

    // 生成图像内容
    if (requestData.contentTypes.includes('image')) {
      promises.push(generateImages(requestData.adviceText, requestData.userPreferences));
    }

    // 生成语音内容
    if (requestData.contentTypes.includes('audio')) {
      promises.push(generateAudio(requestData.adviceText, requestData.userPreferences));
    }

    // 生成视频内容
    if (requestData.contentTypes.includes('video')) {
      promises.push(generateVideo(requestData.adviceText, requestData.userPreferences));
    }

    // 生成互动内容
    if (requestData.contentTypes.includes('interactive')) {
      promises.push(generateInteractiveContent(requestData.adviceText, requestData.userPreferences));
    }

    // 等待所有内容生成完成
    const results = await Promise.allSettled(promises);
    
    // 处理结果
    let imageIndex = 0;
    let audioIndex = 0;
    let videoIndex = 0;
    let interactiveIndex = 0;

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        const type = requestData.contentTypes[index];
        switch (type) {
          case 'image':
            content.images = result.value;
            break;
          case 'audio':
            content.audio = result.value;
            break;
          case 'video':
            content.video = result.value;
            break;
          case 'interactive':
            content.interactive = result.value;
            break;
        }
      } else {
        console.error(`生成${requestData.contentTypes[index]}内容失败:`, result.reason);
      }
    });

    // 格式化文本内容
    content.formatted = formatTextContent(requestData.adviceText, requestData.userPreferences);

    // 生成内容摘要
    content.summary = generateContentSummary(content, requestData);

    // 如果提供了干预ID，保存生成的内容
    if (requestData.interventionId) {
      await saveGeneratedContent(supabase, requestData.interventionId, content);
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          multimodalContent: content,
          generationMetadata: {
            generatedAt: new Date().toISOString(),
            contentTypes: requestData.contentTypes,
            userPreferences: requestData.userPreferences,
            totalItems: {
              images: content.images.length,
              hasAudio: content.audio !== null,
              hasVideo: content.video !== null,
              hasInteractive: content.interactive !== null
            }
          }
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('多模态内容生成错误:', error);
    
    return new Response(
      JSON.stringify({ 
        error: {
          code: 'MULTIMODAL_GENERATION_ERROR',
          message: error.message || '生成多模态内容时发生未知错误'
        }
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});

// 生成图像内容
async function generateImages(adviceText: string, userPreferences: any) {
  try {
    // 解析文本中的关键概念和建议
    const concepts = extractKeyConcepts(adviceText);
    const visualConcepts = mapConceptsToVisuals(concepts);
    
    const images = [];
    
    for (const concept of visualConcepts) {
      const imagePrompt = generateImagePrompt(concept, userPreferences);
      
      try {
        // 这里可以集成图像生成API
        // 目前返回模拟的图像URL结构
        const imageData = {
          id: `img_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          concept: concept.title,
          description: concept.description,
          url: `/generated-images/${concept.id}.png`,
          altText: concept.altText,
          prompt: imagePrompt,
          style: userPreferences.preferredFormat === 'cartoon' ? 'cartoon' : 'realistic',
          accessibility: checkAccessibilityRequirements(concept, userPreferences.accessibilityNeeds)
        };
        
        images.push(imageData);
      } catch (error) {
        console.error(`生成图像失败 (${concept.title}):`, error);
        // 继续处理其他图像，不中断流程
      }
    }
    
    return images;
    
  } catch (error) {
    console.error('图像生成处理失败:', error);
    return [];
  }
}

// 生成语音内容
async function generateAudio(adviceText: string, userPreferences: any) {
  try {
    // 提取适合语音播报的关键信息
    const audioContent = prepareAudioContent(adviceText, userPreferences);
    
    // 生成语音配置
    const voiceConfig = {
      voice: userPreferences.voice || 'female_mature', // 默认使用成熟女声
      speed: userPreferences.accessibilityNeeds.includes('slow_speech') ? 0.8 : 1.0,
      pitch: userPreferences.accessibilityNeeds.includes('high_pitch') ? 1.1 : 1.0,
      volume: 0.8
    };
    
    // 这里可以集成语音合成API
    // 目前返回音频文件的结构
    const audioData = {
      id: `audio_${Date.now()}`,
      content: audioContent,
      duration: estimateAudioDuration(audioContent),
      format: 'mp3',
      quality: 'high',
      voiceConfig,
      accessibility: {
        hasSubtitles: true,
        hasSpeedControl: true,
        hasVolumeControl: true
      },
      url: `/generated-audio/${audioData.id}.mp3`
    };
    
    return audioData;
    
  } catch (error) {
    console.error('语音生成失败:', error);
    return null;
  }
}

// 生成视频内容
async function generateVideo(adviceText: string, userPreferences: any) {
  try {
    // 识别适合视频演示的内容
    const videoSegments = identifyVideoContent(adviceText);
    
    if (videoSegments.length === 0) {
      return null;
    }
    
    const videos = [];
    
    for (const segment of videoSegments) {
      const videoData = {
        id: `video_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        title: segment.title,
        description: segment.description,
        content: segment.content,
        duration: segment.estimatedDuration,
        format: 'mp4',
        quality: '720p',
        hasCaptions: true,
        accessibility: {
          hasSubtitles: true,
          hasAudioDescription: userPreferences.accessibilityNeeds.includes('audio_description')
        },
        segments: segment.segments || [],
        url: `/generated-videos/${videoData.id}.mp4`,
        thumbnail: `/generated-videos/${videoData.id}_thumb.jpg`
      };
      
      videos.push(videoData);
    }
    
    return videos;
    
  } catch (error) {
    console.error('视频生成失败:', error);
    return [];
  }
}

// 生成互动内容
async function generateInteractiveContent(adviceText: string, userPreferences: any) {
  try {
    // 提取可互动的元素
    const interactiveElements = extractInteractiveElements(adviceText);
    
    const interactiveContent = {
      id: `interactive_${Date.now()}`,
      type: 'step_by_step_guide',
      elements: interactiveElements,
      navigation: generateNavigation(interactiveElements),
      progress: {
        enabled: true,
        trackingMethod: 'completion_checkbox'
      },
      accessibility: {
        keyboardNavigation: true,
        screenReaderSupport: true,
        highContrast: userPreferences.accessibilityNeeds.includes('high_contrast')
      },
      customization: {
        fontSize: userPreferences.accessibilityNeeds.includes('large_text') ? 'large' : 'normal',
        colorScheme: userPreferences.preferredFormat === 'high_contrast' ? 'high_contrast' : 'default'
      }
    };
    
    return interactiveContent;
    
  } catch (error) {
    console.error('互动内容生成失败:', error);
    return null;
  }
}

// 提取关键概念
function extractKeyConcepts(text: string) {
  const concepts = [];
  
  // 使用正则表达式提取健康相关概念
  const healthPatterns = [
    { pattern: /血压|高血压|低血压/g, category: '血压管理' },
    { pattern: /血糖|糖尿病|胰岛素/g, category: '血糖控制' },
    { pattern: /体重|减肥|增重|BMI/g, category: '体重管理' },
    { pattern: /运动|锻炼|步行|跑步|游泳/g, category: '运动健身' },
    { pattern: /饮食|营养|膳食|蔬菜|水果/g, category: '营养饮食' },
    { pattern: /睡眠|失眠|作息|休息/g, category: '睡眠管理' },
    { pattern: /用药|药物|剂量|服药/g, category: '用药管理' },
    { pattern: /检查|体检|筛查|监测/g, category: '健康检查' }
  ];
  
  healthPatterns.forEach(({ pattern, category }) => {
    const matches = text.match(pattern);
    if (matches && matches.length > 0) {
      concepts.push({
        category,
        mentions: matches.length,
        keywords: matches
      });
    }
  });
  
  return concepts;
}

// 映射概念到可视化
function mapConceptsToVisuals(concepts: any[]) {
  return concepts.map(concept => {
    const visualMap = {
      '血压管理': {
        title: '血压监测图示',
        description: '显示正确的血压测量方法和正常范围',
        visualType: 'infographic',
        id: 'blood_pressure_guide'
      },
      '血糖控制': {
        title: '血糖管理图示',
        description: '血糖监测和饮食控制的视觉指导',
        visualType: 'chart_diagram',
        id: 'blood_sugar_management'
      },
      '体重管理': {
        title: '体重控制图示',
        description: '健康体重范围和减重方法',
        visualType: 'before_after',
        id: 'weight_management'
      },
      '运动健身': {
        title: '运动示范图',
        description: '推荐运动的正确姿势和动作',
        visualType: 'exercise_demonstration',
        id: 'exercise_demo'
      },
      '营养饮食': {
        title: '营养搭配图',
        description: '健康饮食搭配和食物选择',
        visualType: 'food_plate',
        id: 'nutrition_guide'
      },
      '睡眠管理': {
        title: '睡眠优化图示',
        description: '良好睡眠习惯和环境设置',
        visualType: 'lifestyle_guide',
        id: 'sleep_optimization'
      },
      '用药管理': {
        title: '用药提醒图示',
        description: '正确用药时间和注意事项',
        visualType: 'medication_schedule',
        id: 'medication_guide'
      },
      '健康检查': {
        title: '体检项目图示',
        description: '定期体检的重要性和项目',
        visualType: 'checklist_visual',
        id: 'health_checkup'
      }
    };
    
    const visualInfo = visualMap[concept.category] || {
      title: `${concept.category}指导图`,
      description: `${concept.category}相关知识图示`,
      visualType: 'informational',
      id: concept.category.toLowerCase().replace(/\s+/g, '_')
    };
    
    return {
      ...visualInfo,
      category: concept.category,
      relevanceScore: concept.mentions / concepts.reduce((sum, c) => sum + c.mentions, 0)
    };
  });
}

// 生成图像提示词
function generateImagePrompt(concept: any, userPreferences: any) {
  const styleElements = {
    'cartoon': 'friendly cartoon style, bright colors, simple illustrations',
    'realistic': 'realistic style, clear photographs, professional medical imagery',
    'minimalist': 'minimalist design, clean lines, simple colors',
    'high_contrast': 'high contrast design, bold colors, clear visibility'
  };
  
  const basePrompt = `Create a ${styleElements[userPreferences.preferredFormat] || 'realistic'} illustration for ${concept.title}. ${concept.description}`;
  
  const accessibilityElements = [];
  if (userPreferences.accessibilityNeeds.includes('high_contrast')) {
    accessibilityElements.push('ensure high contrast for better visibility');
  }
  if (userPreferences.accessibilityNeeds.includes('large_elements')) {
    accessibilityElements.push('use large, easily distinguishable elements');
  }
  
  return basePrompt + (accessibilityElements.length > 0 ? '. ' + accessibilityElements.join('. ') : '');
}

// 检查无障碍要求
function checkAccessibilityRequirements(concept: any, accessibilityNeeds: string[]) {
  const requirements = {};
  
  if (accessibilityNeeds.includes('high_contrast')) {
    requirements.highContrast = true;
  }
  if (accessibilityNeeds.includes('large_text')) {
    requirements.largeText = true;
  }
  if (accessibilityNeeds.includes('simple_graphics')) {
    requirements.simpleGraphics = true;
  }
  
  return requirements;
}

// 准备音频内容
function prepareAudioContent(adviceText: string, userPreferences: any) {
  // 清理文本，移除markdown格式
  let cleanText = adviceText
    .replace(/#{1,6}\s/g, '') // 移除标题标记
    .replace(/\*\*(.*?)\*\*/g, '$1') // 移除粗体标记
    .replace(/\*(.*?)\*/g, '$1') // 移除斜体标记
    .replace(/\[(.*?)\]\(.*?\)/g, '$1') // 移除链接，保留文本
    .replace(/\n\s*\n/g, '\n\n') // 规范化段落间距
    .trim();

  // 根据无障碍需求调整语速和内容
  if (userPreferences.accessibilityNeeds.includes('slow_speech')) {
    // 在适当位置添加停顿标记
    cleanText = cleanText.replace(/。/g, '。...'); // 在句号后添加停顿
    cleanText = cleanText.replace(/，/g, '，...'); // 在逗号后添加短暂停顿
  }

  return cleanText;
}

// 估算音频时长
function estimateAudioDuration(text: string) {
  // 中文语音平均每分钟200-250字
  const chineseCharsPerMinute = 220;
  const charCount = text.length;
  const durationMinutes = charCount / chineseCharsPerMinute;
  return Math.round(durationMinutes * 60); // 返回秒数
}

// 识别视频内容
function identifyVideoContent(adviceText: string) {
  const segments = [];
  
  // 识别适合视频演示的内容
  const videoKeywords = ['运动', '锻炼', '演示', '步骤', '动作', '姿势', '操作'];
  
  const paragraphs = adviceText.split('\n\n');
  
  paragraphs.forEach((paragraph, index) => {
    const hasVideoKeywords = videoKeywords.some(keyword => paragraph.includes(keyword));
    
    if (hasVideoKeywords) {
      segments.push({
        title: `第${index + 1}部分`,
        description: `视频演示：${paragraph.substring(0, 50)}...`,
        content: paragraph,
        estimatedDuration: Math.max(30, paragraph.length / 20), // 最少30秒
        segments: splitIntoVideoSegments(paragraph)
      });
    }
  });
  
  return segments;
}

// 分割为视频片段
function splitIntoVideoSegments(paragraph: string) {
  // 将内容分割为适合视频演示的片段
  const sentences = paragraph.split(/[。！？]/).filter(s => s.trim().length > 0);
  const segments = [];
  
  for (let i = 0; i < sentences.length; i += 2) {
    segments.push({
      order: i / 2 + 1,
      content: sentences.slice(i, i + 2).join('。') + '。',
      duration: 15 + Math.random() * 10 // 15-25秒
    });
  }
  
  return segments;
}

// 提取互动元素
function extractInteractiveElements(adviceText: string) {
  const elements = [];
  
  // 识别步骤性内容
  const stepPatterns = [
    /\d+[、.]/g, // 数字序号
    /首先|其次|然后|最后/g, // 顺序词
    /步骤[一二三四五六七八九十]/g // 中文步骤
  ];
  
  stepPatterns.forEach(pattern => {
    const matches = adviceText.match(pattern);
    if (matches) {
      elements.push({
        type: 'step_sequence',
        title: '操作步骤',
        elements: matches.map((match, index) => ({
          id: `step_${index + 1}`,
          text: match,
          completed: false
        }))
      });
    }
  });
  
  // 识别检查清单
  const checklistPatterns = [/✓|✅|□|☐/g, /建议.*?进行/g];
  
  checklistPatterns.forEach(pattern => {
    const matches = adviceText.match(pattern);
    if (matches && matches.length > 2) { // 至少3项才认为是清单
      elements.push({
        type: 'checklist',
        title: '执行清单',
        elements: matches.map((match, index) => ({
          id: `item_${index + 1}`,
          text: `执行建议 ${index + 1}`,
          completed: false
        }))
      });
    }
  });
  
  // 识别问卷调查
  if (adviceText.includes('感受') || adviceText.includes('感觉') || adviceText.includes('评估')) {
    elements.push({
      type: 'self_assessment',
      title: '自我评估',
      elements: [
        { id: 'mood', text: '当前心情如何？', type: 'rating' },
        { id: 'energy', text: '精力水平如何？', type: 'rating' },
        { id: 'motivation', text: '执行动力如何？', type: 'rating' }
      ]
    });
  }
  
  return elements;
}

// 生成导航结构
function generateNavigation(elements: any[]) {
  return elements.map((element, index) => ({
    id: `nav_${index + 1}`,
    title: element.title,
    type: element.type,
    order: index + 1
  }));
}

// 格式化文本内容
function formatTextContent(adviceText: string, userPreferences: any) {
  const paragraphs = adviceText.split('\n\n').filter(p => p.trim().length > 0);
  
  return paragraphs.map(paragraph => {
    const lines = paragraph.split('\n');
    const firstLine = lines[0];
    const remainingLines = lines.slice(1).join('\n');
    
    // 判断段落类型
    let type = 'paragraph';
    if (firstLine.startsWith('# ')) {
      type = 'title';
    } else if (firstLine.startsWith('## ')) {
      type = 'section';
    } else if (firstLine.startsWith('### ')) {
      type = 'subsection';
    } else if (/^\d+[、.]/.test(firstLine)) {
      type = 'listitem';
    }
    
    return {
      type,
      content: type === 'title' ? firstLine.replace(/^#+\s/, '') : paragraph,
      formatted: formatForDisplay(firstLine, remainingLines, userPreferences),
      metadata: {
        wordCount: paragraph.length,
        estimatedReadTime: Math.ceil(paragraph.length / 200) // 每分钟200字
      }
    };
  });
}

// 格式化显示
function formatForDisplay(title: string, content: string, userPreferences: any) {
  // 应用无障碍设置
  const accessibilitySettings = {
    fontSize: userPreferences.accessibilityNeeds.includes('large_text') ? 'text-lg' : 'text-base',
    contrast: userPreferences.accessibilityNeeds.includes('high_contrast') ? 'high-contrast' : 'normal',
    spacing: userPreferences.accessibilityNeeds.includes('extra_spacing') ? 'relaxed' : 'normal'
  };
  
  return {
    title,
    content,
    accessibility: accessibilitySettings,
    styling: {
      fontFamily: 'system-ui, sans-serif',
      lineHeight: accessibilitySettings.spacing === 'relaxed' ? '1.75' : '1.5',
      colorScheme: accessibilitySettings.contrast === 'high-contrast' ? 'dark' : 'light'
    }
  };
}

// 生成内容摘要
function generateContentSummary(content: any, request: MultimodalRequest) {
  const summary = {
    totalElements: 0,
    accessibilityFeatures: [],
    recommendedUsage: '',
    estimatedEngagementTime: 0
  };
  
  summary.totalElements = content.images.length + 
    (content.audio ? 1 : 0) + 
    (content.video ? content.video.length : 0) + 
    (content.interactive ? 1 : 0);
  
  // 计算预估使用时间
  let timeEstimate = 0;
  timeEstimate += content.images.length * 30; // 每张图片30秒
  if (content.audio) timeEstimate += content.audio.duration || 120;
  if (content.video) timeEstimate += content.video.reduce((sum: number, v: any) => sum + (v.duration || 60), 0);
  if (content.interactive) timeEstimate += 180; // 互动内容3分钟
  
  summary.estimatedEngagementTime = timeEstimate;
  
  // 推荐使用方式
  if (request.userPreferences.contentType === 'audio') {
    summary.recommendedUsage = '建议在安静环境中使用耳机收听';
  } else if (request.userPreferences.contentType === 'interactive') {
    summary.recommendedUsage = '建议按照步骤顺序进行，配合实际操作';
  } else {
    summary.recommendedUsage = '可按照个人节奏逐步学习相关内容';
  }
  
  return summary;
}

// 保存生成的内容
async function saveGeneratedContent(supabase: any, interventionId: string, content: any) {
  try {
    // 保存多模态内容记录
    const { error } = await supabase
      .from('multimodal_content')
      .insert({
        intervention_id: interventionId,
        content_type: 'comprehensive',
        content_url: null, // 复合内容类型，无单一URL
        content_data: content,
        created_at: new Date().toISOString()
      });

    if (error) {
      console.error('保存多模态内容失败:', error);
    }
  } catch (error) {
    console.error('保存内容时发生错误:', error);
  }
}