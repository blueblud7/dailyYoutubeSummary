import os
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('config.env')

class AnalysisService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
    def analyze_transcript(self, transcript_text: str, video_title: str, 
                          channel_name: str, keywords: List[str] = None) -> Dict:
        """자막을 분석하여 투자 인사이트를 추출합니다."""
        
        keywords_str = ", ".join(keywords) if keywords else "투자, 주식, 부동산, 경제, 금리"
        
        prompt = f"""
        다음은 투자 관련 유튜브 비디오의 자막입니다. 이 내용을 분석하여 투자 인사이트를 제공해주세요.

        비디오 제목: {video_title}
        채널명: {channel_name}
        관련 키워드: {keywords_str}
        
        자막 내용:
        {transcript_text[:4000]}  # 토큰 제한 고려
        
        다음 형식으로 JSON 응답해주세요:
        {{
            "summary": "비디오의 핵심 내용 요약 (200자 이내)",
            "key_insights": [
                "주요 인사이트 1",
                "주요 인사이트 2",
                "주요 인사이트 3"
            ],
            "sentiment_score": -1부터 1 사이의 시장 전망 점수 (부정적: -1, 중립: 0, 긍정적: 1),
            "importance_score": 0부터 1 사이의 중요도 점수,
            "mentioned_entities": [
                "언급된 기업, 인물, 경제지표 등"
            ],
            "investment_themes": [
                "투자 테마나 섹터"
            ],
            "market_outlook": "시장 전망에 대한 설명",
            "actionable_insights": [
                "실행 가능한 투자 조언이나 주의사항"
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 투자 전문가입니다. 유튜브 콘텐츠를 분석하여 투자 인사이트를 제공하는 역할을 합니다. 반드시 유효한 JSON 형식으로만 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            # JSON 형식이 아닌 경우를 위한 처리
            if not content.startswith('{'):
                # JSON 부분만 추출 시도
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]
                else:
                    raise ValueError("유효한 JSON을 찾을 수 없습니다")
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            self.logger.error(f"자막 분석 중 오류 발생: {e}")
            return {
                "summary": "분석 실패",
                "key_insights": [],
                "sentiment_score": 0,
                "importance_score": 0,
                "mentioned_entities": [],
                "investment_themes": [],
                "market_outlook": "분석 불가",
                "actionable_insights": []
            }
    
    def generate_trend_analysis(self, analyses: List[Dict], keywords: List[str], 
                              date_range: str = "최근 7일") -> Dict:
        """여러 분석 결과를 종합하여 트렌드 분석을 생성합니다."""
        
        # 분석 데이터 요약
        summaries = [analysis.get('summary', '') for analysis in analyses]
        insights = []
        for analysis in analyses:
            insights.extend(analysis.get('key_insights', []))
        
        entities = []
        for analysis in analyses:
            entities.extend(analysis.get('mentioned_entities', []))
        
        avg_sentiment = sum([analysis.get('sentiment_score', 0) for analysis in analyses]) / len(analyses) if analyses else 0
        
        prompt = f"""
        {date_range} 동안의 투자 관련 유튜브 콘텐츠 분석 결과를 종합하여 트렌드 리포트를 작성해주세요.

        분석 대상 키워드: {', '.join(keywords)}
        총 분석 영상 수: {len(analyses)}
        평균 시장 감정 점수: {avg_sentiment:.2f}
        
        주요 요약들:
        {' '.join(summaries[:10])}
        
        주요 인사이트들:
        {' '.join(insights[:20])}
        
        언급된 주요 엔티티들:
        {' '.join(set(entities))}
        
        다음 형식으로 JSON 응답해주세요:
        {{
            "overall_trend": "전체적인 시장 트렌드 설명",
            "key_themes": [
                "주요 투자 테마 1",
                "주요 투자 테마 2",
                "주요 투자 테마 3"
            ],
            "market_sentiment": "bullish/bearish/neutral",
            "hot_topics": [
                "뜨거운 이슈들"
            ],
            "consensus_view": "전문가들의 합의된 견해",
            "contrarian_views": [
                "소수 의견이나 반대 견해들"
            ],
            "risk_factors": [
                "주요 리스크 요인들"
            ],
            "opportunities": [
                "투자 기회들"
            ],
            "summary": "종합 요약 (300자 이내)"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 투자 시장 분석 전문가입니다. 여러 소스의 정보를 종합하여 시장 트렌드를 분석합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            self.logger.error(f"트렌드 분석 중 오류 발생: {e}")
            return {
                "overall_trend": "분석 실패",
                "key_themes": [],
                "market_sentiment": "neutral",
                "hot_topics": [],
                "consensus_view": "분석 불가",
                "contrarian_views": [],
                "risk_factors": [],
                "opportunities": [],
                "summary": "분석에 실패했습니다."
            }
    
    def generate_daily_report(self, trend_analysis: Dict, top_videos: List[Dict], 
                            date: datetime) -> Dict:
        """일일 투자 인사이트 리포트를 생성합니다."""
        
        video_titles = [video.get('title', '') for video in top_videos[:5]]
        
        prompt = f"""
        {date.strftime('%Y년 %m월 %d일')} 투자 인사이트 일일 리포트를 작성해주세요.

        시장 트렌드 분석:
        - 전체 트렌드: {trend_analysis.get('overall_trend', '')}
        - 시장 감정: {trend_analysis.get('market_sentiment', '')}
        - 주요 테마: {', '.join(trend_analysis.get('key_themes', []))}
        - 핫 토픽: {', '.join(trend_analysis.get('hot_topics', []))}
        
        주요 영상들:
        {chr(10).join([f"- {title}" for title in video_titles])}
        
        다음 형식으로 JSON 응답해주세요:
        {{
            "title": "일일 리포트 제목",
            "executive_summary": "경영진 요약 (150자 이내)",
            "market_highlights": [
                "시장 하이라이트 1",
                "시장 하이라이트 2",
                "시장 하이라이트 3"
            ],
            "key_developments": [
                "주요 동향 1",
                "주요 동향 2"
            ],
            "watch_list": [
                "주목할 종목이나 섹터들"
            ],
            "risk_alert": [
                "위험 요소들"
            ],
            "tomorrow_outlook": "내일 전망",
            "action_items": [
                "투자자가 취해야 할 행동들"
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 투자 리포트 작성 전문가입니다. 일일 투자 브리핑을 작성합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            self.logger.error(f"일일 리포트 생성 중 오류 발생: {e}")
            return {
                "title": f"{date.strftime('%Y.%m.%d')} 투자 인사이트 리포트",
                "executive_summary": "리포트 생성에 실패했습니다.",
                "market_highlights": [],
                "key_developments": [],
                "watch_list": [],
                "risk_alert": [],
                "tomorrow_outlook": "분석 불가",
                "action_items": []
            }
    
    def compare_perspectives(self, topic: str, analyses_by_channel: Dict[str, List[Dict]]) -> Dict:
        """특정 주제에 대한 각 채널/인물의 관점을 비교합니다."""
        
        channel_summaries = {}
        for channel, analyses in analyses_by_channel.items():
            if analyses:
                summaries = [analysis.get('summary', '') for analysis in analyses]
                insights = []
                for analysis in analyses:
                    insights.extend(analysis.get('key_insights', []))
                
                channel_summaries[channel] = {
                    'summaries': summaries,
                    'insights': insights[:5],  # 상위 5개 인사이트
                    'sentiment': sum([a.get('sentiment_score', 0) for a in analyses]) / len(analyses)
                }
        
        prompt = f"""
        "{topic}" 주제에 대한 각 채널/전문가들의 관점을 비교 분석해주세요.

        채널별 분석:
        """
        
        for channel, data in channel_summaries.items():
            prompt += f"""
        
        [{channel}]
        - 평균 시장 감정: {data['sentiment']:.2f}
        - 주요 인사이트: {', '.join(data['insights'])}
        """
        
        prompt += f"""
        
        다음 형식으로 JSON 응답해주세요:
        {{
            "topic": "{topic}",
            "consensus_areas": [
                "의견이 일치하는 영역들"
            ],
            "divergent_views": [
                {{
                    "channel": "채널명",
                    "position": "해당 채널의 관점",
                    "reasoning": "근거"
                }}
            ],
            "sentiment_spectrum": {{
                "most_bullish": "가장 긍정적인 채널",
                "most_bearish": "가장 부정적인 채널",
                "most_neutral": "가장 중립적인 채널"
            }},
            "key_disagreements": [
                "주요 의견 충돌 지점들"
            ],
            "investment_implications": "투자에 미치는 함의",
            "recommended_approach": "추천되는 접근 방식"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 다양한 투자 전문가들의 의견을 비교 분석하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            self.logger.error(f"관점 비교 분석 중 오류 발생: {e}")
            return {
                "topic": topic,
                "consensus_areas": [],
                "divergent_views": [],
                "sentiment_spectrum": {},
                "key_disagreements": [],
                "investment_implications": "분석 실패",
                "recommended_approach": "추가 분석 필요"
            } 