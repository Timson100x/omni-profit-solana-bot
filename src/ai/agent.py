"""AI Agent - Token analysis using Google Gemini."""

import asyncio
from typing import Dict, Optional
from src.core.config import settings
from src.core.logger import log

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AIAgent:
    def __init__(self):
        self._logger = log.bind(module="ai_agent")
        self.model = None
        self.enabled = False
        
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # Use gemini-1.5-flash instead of deprecated gemini-pro
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.enabled = True
                self._logger.info("✅ Gemini AI initialized")
            except Exception as e:
                self._logger.warning("gemini_init_failed", error=str(e))
        else:
            self._logger.warning("gemini_not_available", 
                               has_key=bool(settings.GEMINI_API_KEY),
                               installed=GEMINI_AVAILABLE)
    
    async def analyze_token(self, 
                          token_address: str,
                          token_name: str,
                          market_data: Dict,
                          signal_confidence: float) -> Dict:
        """Analyze token and return trading decision"""
        
        if not self.enabled:
            # Fallback: Simple heuristic analysis
            return await self._fallback_analysis(market_data)
        
        try:
            prompt = self._build_analysis_prompt(market_data)
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            return self._parse_response(response.text, market_data)
            
        except Exception as e:
            self._logger.error("ai_analysis_failed", error=str(e))
            return await self._fallback_analysis(market_data)
    
    def _build_analysis_prompt(self, token_data: Dict) -> str:
        """Build analysis prompt for Gemini"""
        return f"""Analyze this Solana token for trading:

Token: {token_data.get('name', 'Unknown')}
Address: {token_data.get('address', 'Unknown')}
Liquidity: ${token_data.get('liquidity', 0):,.2f}
Volume 24h: ${token_data.get('volume_24h', 0):,.2f}
Price Change 24h: {token_data.get('price_change_24h', 0):.2f}%
Holder Count: {token_data.get('holders', 0)}

Provide a trading decision:
- SCORE: 0-100 (confidence to buy)
- REASON: Brief explanation
- RISK: LOW/MEDIUM/HIGH
- TARGET: Expected profit multiplier (e.g., 2x)

Format your response as:
SCORE: [number]
REASON: [text]
RISK: [level]
TARGET: [multiplier]
"""
    
    def _parse_response(self, response_text: str, token_data: Dict) -> Dict:
        """Parse Gemini response into structured data"""
        lines = response_text.strip().split('\n')
        result = {
            'should_buy': False,
            'confidence': 0.0,
            'reason': 'Unknown',
            'risk_level': 'HIGH',
            'target_multiplier': 2.0
        }
        
        for line in lines:
            if line.startswith('SCORE:'):
                score = int(''.join(filter(str.isdigit, line)))
                result['confidence'] = score / 100.0
                result['should_buy'] = score >= 70
            elif line.startswith('REASON:'):
                result['reason'] = line.replace('REASON:', '').strip()
            elif line.startswith('RISK:'):
                result['risk_level'] = line.replace('RISK:', '').strip()
            elif line.startswith('TARGET:'):
                target_str = line.replace('TARGET:', '').strip()
                result['target_multiplier'] = float(''.join(filter(lambda x: x.isdigit() or x == '.', target_str)))
        
        self._logger.info("ai_analysis_complete", 
                         token=token_data.get('name'),
                         score=result['confidence'],
                         decision='BUY' if result['should_buy'] else 'SKIP')
        
        return result
    
    async def _fallback_analysis(self, token_data: Dict) -> Dict:
        """Simple heuristic analysis when AI is unavailable"""
        self._logger.info("using_fallback_analysis", token=token_data.get('name'))
        
        score = 0
        
        # Check liquidity
        liquidity = token_data.get('liquidity', 0)
        if liquidity > 100000:
            score += 30
        elif liquidity > 50000:
            score += 20
        elif liquidity > 10000:
            score += 10
        
        # Check volume
        volume = token_data.get('volume_24h', 0)
        if volume > 50000:
            score += 30
        elif volume > 10000:
            score += 20
        
        # Check price change
        price_change = token_data.get('price_change_24h', 0)
        if 0 < price_change < 50:  # Positive but not parabolic
            score += 20
        elif price_change > 50:  # Too hot
            score -= 20
        
        # Check holders
        holders = token_data.get('holders', 0)
        if holders > 1000:
            score += 20
        elif holders > 500:
            score += 10
        
        confidence = min(score / 100.0, 1.0)
        
        return {
            'should_buy': score >= 70,
            'confidence': confidence,
            'reason': f'Heuristic score: {score}/100',
            'risk_level': 'MEDIUM' if score >= 70 else 'HIGH',
            'target_multiplier': 2.0
        }

ai_agent = AIAgent()
