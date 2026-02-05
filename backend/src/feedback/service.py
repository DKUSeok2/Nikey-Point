"""LLM 피드백 생성 서비스 (Phase 1)"""
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class FeedbackService:
    """GPT-4o-mini 를 사용한 러닝 피드백 생성"""
    
    def __init__(self):
        from ..core.config import settings
        
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
    
    def generate_feedback(
        self,
        overstride: float,
        tilt: float,
        vertical: float,
        user_height: float
    ) -> str:
        """
        3가지 지표를 기반으로 LLM 피드백 생성
        
        Args:
            overstride: 과보폭 측정값
            tilt: 상체 기울기 측정값 (도)
            vertical: 수직 진동 측정값
            user_height: 사용자 키 (cm)
            
        Returns:
            LLM이 생성한 피드백 텍스트
        """
        
        if not self.client:
            return self._generate_fallback_feedback(overstride, tilt, vertical)
        
        try:
            prompt = self._build_prompt(overstride, tilt, vertical, user_height)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 친절한 러닝 전문 코치입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM 피드백 생성 실패: {e}")
            return self._generate_fallback_feedback(overstride, tilt, vertical)
    
    def _build_prompt(
        self,
        overstride: float,
        tilt: float,
        vertical: float,
        user_height: float
    ) -> str:
        """프롬프트 구성"""
        
        from ..analysis.metrics_config import METRICS_REFERENCE, get_status
        
        overstride_ref = METRICS_REFERENCE['overstride']
        tilt_ref = METRICS_REFERENCE['tilt']
        vertical_ref = METRICS_REFERENCE['vertical']
        
        return f"""
당신은 전문 러닝 코치입니다. 다음 러닝 분석 결과를 바탕으로 피드백을 제공해주세요.

[사용자 정보]
- 키: {user_height}cm

[분석 결과 vs 정상 범위]

1. 과보폭 (Overstride)
   - 측정값: {overstride:.3f}
   - 정상 범위: {overstride_ref['normal_range'][0]:.3f} ~ {overstride_ref['normal_range'][1]:.3f}
   - 상태: {get_status(overstride, 'overstride')}
   - 의미: 착지 시 발이 골반보다 앞으로 나가는 정도

2. 상체 기울기 (Tilt)
   - 측정값: {tilt:.1f}°
   - 정상 범위: {tilt_ref['normal_range'][0]:.1f}° ~ {tilt_ref['normal_range'][1]:.1f}°
   - 이상적: {tilt_ref['ideal']:.1f}° (프로 러너 평균)
   - 상태: {get_status(tilt, 'tilt')}
   - 의미: 상체가 수직에서 얼마나 기울어져 있는지

3. 수직 진동 (Vertical Oscillation)
   - 측정값: {vertical:.3f}
   - 정상 범위: {vertical_ref['normal_range'][0]:.3f} ~ {vertical_ref['normal_range'][1]:.3f}
   - 상태: {get_status(vertical, 'vertical')}
   - 의미: 러닝 중 몸의 상하 움직임 폭

[피드백 작성 가이드]
1. 각 지표가 정상 범위에 있는지 평가
2. 범위를 벗어난 지표에 대해 구체적인 개선 방법 제시:

오버스트라이드가 기준값을 초과한 경우
과보폭으로 인한 제동(braking) 발생 가능성 언급
케이던스 증가 권장 (목표 약 180 bpm)기본적으로 "약간 올리기(5~8%)"를 제안하되,
만약 사용자가 "이미 너무 빠르게 뛰는 느낌/종아리 과부하/발을 급하게 찍는 느낌"이 있다고 하면
케이던스는 올리기보다 "리듬을 안정"시키는 방향(크게 바꾸지 않기)으로 안내한다.
ABNORMAL 또는 BORDERLINE이면:
  1) "발을 몸 아래로 디딘다" 큐를 먼저 제안
  2) "보폭을 5~10% 줄이기"를 제안

상체 기울기 해석 (프로 러너 범위: -88° ~ -72°):
- 각도가 -90°에 가까울수록 = 직립
- 각도가 -90°에서 멀어질수록 (예: -70°) = 앞으로 숙임

상체 기울기가 -88° 미만인 경우 (예: -90°, -89°)
→ 너무 직립됨
→ 골반을 기준으로 상체를 아주 살짝 전방으로 기울이기
→ 허리가 아닌 발목에서의 자연스러운 기울기 강조

상체 기울기가 -72° 초과인 경우 (예: -71°, -70°)
→ 너무 앞으로 숙여짐
→ 시선을 전방으로 높이고 가슴을 자연스럽게 열어 상체 세우기
→ 허리 굽힘이 아닌 전신 정렬 회복에 초점

무게중심 수직진동(VO)이 6.0%를 초과한 경우
(High VO – 수직 에너지 낭비 가능성)
착지 시 반동을 줄이고 무릎·고관절로 충격 흡수
위로 튀어 오르는 동작보다 앞으로 미끄러지듯 진행하는 감각 유도
부드럽게 착지
   
3. 즉시 실천 가능한 구체적인 팁 2-3가지 제시
4. 친근하고 격려하는 톤으로 3-4문단 작성



피드백:
"""
    
    def _generate_fallback_feedback(
        self,
        overstride: float,
        tilt: float,
        vertical: float
    ) -> str:
        """LLM 실패 시 기본 피드백"""
        
        from ..analysis.metrics_config import is_in_range
        
        feedback_parts = []
        
        # Overstride 평가
        if is_in_range(overstride, 'overstride'):
            feedback_parts.append("과보폭이 적절합니다.")
        elif overstride > 0.18:
            feedback_parts.append("과보폭이 큽니다. 보폭을 줄이고 케이던스를 높여보세요.")
        else:
            feedback_parts.append("과보폭이 매우 안정적입니다.")
        
        # Tilt 평가
        if is_in_range(tilt, 'tilt'):
            feedback_parts.append("상체 기울기가 적절합니다.")
        elif tilt > -78:
            feedback_parts.append("상체가 너무 직립되어 있습니다. 골반부터 살짝 앞으로 기울여보세요.")
        else:
            feedback_parts.append("상체가 너무 앞으로 기울어져 있습니다. 시선을 높이고 상체를 세워보세요.")
        
        # Vertical 평가
        if is_in_range(vertical, 'vertical'):
            feedback_parts.append("수직 진동이 적절합니다.")
        elif vertical > 0.07:
            feedback_parts.append("수직 진동이 큽니다. 부드럽게 착지하고 무릎으로 충격을 흡수하세요.")
        else:
            feedback_parts.append("수직 진동이 매우 작아 효율적입니다.")
        
        return " ".join(feedback_parts)
