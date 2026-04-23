import { useState } from 'react';
import { supabase } from '../../lib/supabase';

interface EscortRatingProps {
  orderId: string;
  workerId: string;
  workerName: string;
  onComplete?: () => void;
  onCancel?: () => void;
}

interface RatingScores {
  overall: number;
  attitude: number;
  professionalism: number;
  punctuality: number;
}

export default function EscortRating({ orderId, workerId, workerName, onComplete, onCancel }: EscortRatingProps) {
  const [scores, setScores] = useState<RatingScores>({
    overall: 0,
    attitude: 0,
    professionalism: 0,
    punctuality: 0
  });
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [hoveredStar, setHoveredStar] = useState<{ category: keyof RatingScores; value: number } | null>(null);

  const ratingCategories = [
    { key: 'overall' as keyof RatingScores, label: '综合评分', icon: '⭐' },
    { key: 'attitude' as keyof RatingScores, label: '服务态度', icon: '😊' },
    { key: 'professionalism' as keyof RatingScores, label: '专业能力', icon: '💼' },
    { key: 'punctuality' as keyof RatingScores, label: '准时性', icon: '⏰' }
  ];

  const handleStarClick = (category: keyof RatingScores, value: number) => {
    setScores(prev => ({ ...prev, [category]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 验证评分
    if (scores.overall === 0) {
      alert('请至少给出综合评分');
      return;
    }

    setLoading(true);

    try {
      // 计算平均分（如果分项评分都有的话）
      const hasDetailedScores = scores.attitude > 0 && scores.professionalism > 0 && scores.punctuality > 0;
      const finalScore = hasDetailedScores 
        ? (scores.overall + scores.attitude + scores.professionalism + scores.punctuality) / 4
        : scores.overall;

      // 更新陪诊师评分
      const { data: currentWorker, error: fetchError } = await supabase
        .from('escort_workers')
        .select('rating, total_reviews')
        .eq('id', workerId)
        .single();

      if (fetchError) throw fetchError;

      const currentRating = currentWorker.rating || 0;
      const currentReviews = currentWorker.total_reviews || 0;
      const newRating = ((currentRating * currentReviews) + finalScore) / (currentReviews + 1);

      const { error: updateError } = await supabase
        .from('escort_workers')
        .update({
          rating: Number(newRating.toFixed(2)),
          total_reviews: currentReviews + 1
        })
        .eq('id', workerId);

      if (updateError) throw updateError;

      // 更新订单评价状态
      const { error: orderError } = await supabase
        .from('service_orders')
        .update({
          rating_score: finalScore,
          rating_comment: comment,
          rating_details: {
            overall: scores.overall,
            attitude: scores.attitude,
            professionalism: scores.professionalism,
            punctuality: scores.punctuality
          }
        })
        .eq('id', orderId);

      if (orderError) throw orderError;

      alert('评价提交成功！感谢您的反馈');
      onComplete?.();
    } catch (error: any) {
      console.error('提交评价失败:', error);
      alert('提交评价失败：' + (error.message || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (category: keyof RatingScores) => {
    const currentScore = scores[category];
    const displayScore = hoveredStar?.category === category ? hoveredStar.value : currentScore;

    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => handleStarClick(category, star)}
            onMouseEnter={() => setHoveredStar({ category, value: star })}
            onMouseLeave={() => setHoveredStar(null)}
            className="focus:outline-none transition-transform hover:scale-110"
          >
            <svg
              className={`w-8 h-8 transition-colors ${
                star <= displayScore
                  ? 'text-yellow-400 fill-current'
                  : 'text-gray-300 fill-current'
              }`}
              viewBox="0 0 24 24"
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </button>
        ))}
        <span className="ml-2 text-sm text-gray-600 self-center">
          {displayScore > 0 ? `${displayScore}.0 分` : '未评分'}
        </span>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl max-w-2xl mx-auto">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">服务评价</h2>
            <p className="text-gray-600 mt-1">为陪诊师 <span className="font-semibold text-indigo-600">{workerName}</span> 的服务打分</p>
          </div>
          <div className="text-4xl">⭐</div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6">
        <div className="space-y-6">
          {/* 评分区域 */}
          {ratingCategories.map(({ key, label, icon }) => (
            <div key={key} className="bg-gradient-to-r from-gray-50 to-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{icon}</span>
                  <label className="text-lg font-semibold text-gray-700">
                    {label}
                    {key === 'overall' && <span className="text-red-500 ml-1">*</span>}
                  </label>
                </div>
              </div>
              {renderStars(key)}
            </div>
          ))}

          {/* 文字评价 */}
          <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-4 border border-indigo-200">
            <label className="block text-lg font-semibold text-gray-700 mb-3">
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
                文字评价
              </span>
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              placeholder="请分享您对本次服务的感受和建议（选填）&#10;例如：陪诊师非常专业，态度亲切，帮助我顺利完成了就医流程..."
            />
            <div className="mt-2 text-sm text-gray-500">
              {comment.length}/500 字
            </div>
          </div>

          {/* 评价说明 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex gap-3">
              <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div className="text-sm text-yellow-800">
                <p className="font-medium mb-1">评价说明：</p>
                <ul className="list-disc list-inside space-y-1 text-yellow-700">
                  <li>综合评分为必填项，分项评分为选填</li>
                  <li>您的真实评价将帮助我们改进服务质量</li>
                  <li>评价提交后将更新陪诊师的总体评分</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* 按钮组 */}
        <div className="flex gap-4 mt-8">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium text-gray-700"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading || scores.overall === 0}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-lg hover:from-indigo-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-lg"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                提交中...
              </span>
            ) : (
              '提交评价'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
