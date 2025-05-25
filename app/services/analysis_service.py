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
    
    def analyze_content_for_keyword(self, transcript_text: str, keyword: str, video_id: str) -> Dict:
        """특정 키워드에 대해 콘텐츠를 분석합니다."""
        
        if not transcript_text or not transcript_text.strip():
            return None
            
        prompt = f"""
        다음 텍스트에서 '{keyword}' 키워드와 관련된 내용을 분석해주세요.

        텍스트:
        {transcript_text[:3000]}

        다음 형식으로 JSON 응답해주세요:
        {{
            "relevance": 0부터 1 사이의 관련성 점수,
            "sentiment_score": -1부터 1 사이의 감정 점수 (부정적: -1, 중립: 0, 긍정적: 1),
            "importance_score": 0부터 1 사이의 중요도 점수,
            "key_insights": "{keyword}와 관련된 주요 인사이트 (100자 이내)",
            "summary": "키워드 관련 내용 요약 (150자 이내)",
            "entities": [
                "언급된 관련 기업이나 인물들"
            ],
            "context": "키워드가 언급된 맥락"
        }}
        
        만약 키워드와 관련성이 0.3 미만이면 relevance를 0으로 하고 null을 반환하세요.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"당신은 투자 전문 분석가입니다. '{keyword}' 키워드와 관련된 내용만 분석하고, 관련성이 낮으면 정확히 판단해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 추출
            if not content.startswith('{'):
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]
                else:
                    return None
            
            result = json.loads(content)
            
            # 관련성이 낮으면 None 반환
            if result.get('relevance', 0) < 0.3:
                return None
                
            return result
            
        except Exception as e:
            self.logger.error(f"키워드 분석 중 오류 발생: {e}")
            return None
    
    def generate_trend_analysis(self, analyses: List[Dict], keywords: List[str], 
                              date_range: str = "최근 7일") -> Dict:
        """여러 분석 결과를 종합하여 트렌드 분석을 생성합니다."""
        
        if not analyses:
            return {
                "overall_trend": "분석할 데이터가 없습니다",
                "key_themes": [],
                "market_sentiment": "neutral",
                "hot_topics": [],
                "consensus_view": "데이터 부족",
                "contrarian_views": [],
                "risk_factors": [],
                "opportunities": [],
                "summary": "분석할 데이터가 없습니다."
            }
        
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
            self.logger.info(f"트렌드 분석 요청 시작 - {len(analyses)}개 분석, 키워드: {keywords}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 투자 시장 분석 전문가입니다. 여러 소스의 정보를 종합하여 시장 트렌드를 분석합니다. 반드시 유효한 JSON 형식으로만 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            if not response or not response.choices or not response.choices[0].message:
                self.logger.error("OpenAI API에서 빈 응답 수신")
                raise ValueError("OpenAI API 응답이 비어있습니다")
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                self.logger.error("OpenAI API 응답 내용이 비어있음")
                raise ValueError("응답 내용이 비어있습니다")
            
            content = content.strip()
            self.logger.info(f"OpenAI 원본 응답 길이: {len(content)} 문자")
            
            # JSON 부분만 추출 시도
            if not content.startswith('{'):
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]
                    self.logger.info(f"JSON 추출 완료: {len(content)} 문자")
                else:
                    self.logger.error(f"유효한 JSON을 찾을 수 없음: {content[:200]}...")
                    raise ValueError("유효한 JSON을 찾을 수 없습니다")
            
            # JSON 파싱 시도
            try:
                result = json.loads(content)
                self.logger.info("JSON 파싱 성공")
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON 파싱 실패: {e}, 내용: {content[:200]}...")
                raise ValueError(f"JSON 파싱 실패: {e}")
            
            # 필수 필드 검증
            required_fields = ['overall_trend', 'key_themes', 'market_sentiment', 'summary']
            for field in required_fields:
                if field not in result:
                    result[field] = ""
            
            self.logger.info("트렌드 분석 완료")
            return result
            
        except Exception as e:
            self.logger.error(f"트렌드 분석 중 오류 발생: {e}")
            
            # 기본 분석 결과 생성
            sentiment_label = "bullish" if avg_sentiment > 0.1 else "bearish" if avg_sentiment < -0.1 else "neutral"
            
            fallback_result = {
                "overall_trend": f"{date_range} 동안 분석된 {len(analyses)}개 영상을 바탕으로 한 트렌드",
                "key_themes": list(set(keywords)) if keywords else ["투자", "시장 분석"],
                "market_sentiment": sentiment_label,
                "hot_topics": list(set(entities))[:5] if entities else [],
                "consensus_view": f"평균 감정 점수 {avg_sentiment:.2f}를 기반으로 한 시장 전망",
                "contrarian_views": [],
                "risk_factors": [],
                "opportunities": [],
                "summary": f"{date_range} 동안 {len(analyses)}개 영상이 분석되었으며, 평균 감정 점수는 {avg_sentiment:.2f}입니다."
            }
            
            self.logger.info("대체 분석 결과 반환")
            return fallback_result
    
    def generate_daily_report(self, trend_analysis: Dict, top_videos: List[Dict], 
                            date: datetime) -> Dict:
        """일일 투자 인사이트 리포트를 생성합니다."""
        
        if not trend_analysis or not top_videos:
            # 기본 리포트 생성
            return {
                "title": f"{date.strftime('%Y.%m.%d')} 투자 인사이트 리포트",
                "executive_summary": "오늘 분석할 데이터가 부족합니다.",
                "market_highlights": [],
                "key_developments": [],
                "watch_list": [],
                "risk_alert": [],
                "tomorrow_outlook": "추가 데이터 수집 후 분석 예정",
                "action_items": []
            }
        
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
            self.logger.info(f"일일 리포트 생성 시작 - {date.strftime('%Y-%m-%d')}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 투자 리포트 작성 전문가입니다. 일일 투자 브리핑을 작성합니다. 반드시 유효한 JSON 형식으로만 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            if not response or not response.choices or not response.choices[0].message:
                self.logger.error("OpenAI API에서 빈 응답 수신")
                raise ValueError("OpenAI API 응답이 비어있습니다")
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                self.logger.error("OpenAI API 응답 내용이 비어있음")
                raise ValueError("응답 내용이 비어있습니다")
            
            content = content.strip()
            self.logger.info(f"OpenAI 원본 응답 길이: {len(content)} 문자")
            
            # JSON 부분만 추출 시도
            if not content.startswith('{'):
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]
                    self.logger.info(f"JSON 추출 완료: {len(content)} 문자")
                else:
                    self.logger.error(f"유효한 JSON을 찾을 수 없음: {content[:200]}...")
                    raise ValueError("유효한 JSON을 찾을 수 없습니다")
            
            # JSON 파싱 시도
            try:
                result = json.loads(content)
                self.logger.info("JSON 파싱 성공")
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON 파싱 실패: {e}, 내용: {content[:200]}...")
                raise ValueError(f"JSON 파싱 실패: {e}")
            
            # 필수 필드 검증 및 기본값 설정
            required_fields = ['title', 'executive_summary', 'tomorrow_outlook']
            for field in required_fields:
                if field not in result:
                    if field == 'title':
                        result[field] = f"{date.strftime('%Y.%m.%d')} 투자 인사이트 리포트"
                    elif field == 'executive_summary':
                        result[field] = trend_analysis.get('summary', '일일 분석을 완료했습니다.')
                    elif field == 'tomorrow_outlook':
                        result[field] = "지속적인 모니터링이 필요합니다."
            
            # 배열 필드들 기본값 설정
            array_fields = ['market_highlights', 'key_developments', 'watch_list', 'risk_alert', 'action_items']
            for field in array_fields:
                if field not in result or not isinstance(result[field], list):
                    result[field] = []
            
            self.logger.info("일일 리포트 생성 완료")
            return result
            
        except Exception as e:
            self.logger.error(f"일일 리포트 생성 중 오류 발생: {e}")
            
            # 기본 리포트 반환
            fallback_result = {
                "title": f"{date.strftime('%Y.%m.%d')} 투자 인사이트 리포트",
                "executive_summary": trend_analysis.get('summary', '오늘의 투자 분석을 완료했습니다.'),
                "market_highlights": trend_analysis.get('key_themes', [])[:3],
                "key_developments": trend_analysis.get('hot_topics', [])[:2],
                "watch_list": [],
                "risk_alert": trend_analysis.get('risk_factors', [])[:2],
                "tomorrow_outlook": "지속적인 모니터링을 통해 시장 동향을 파악하겠습니다.",
                "action_items": trend_analysis.get('opportunities', [])[:2]
            }
            
            self.logger.info("대체 일일 리포트 반환")
            return fallback_result
    
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