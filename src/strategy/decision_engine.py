"""
Main strategic decision engine.
Combines hand evaluation, equity, and pot odds to suggest actions.
"""
from typing import Optional, List
from dataclasses import dataclass
from src.strategy.hand_evaluator import HandEvaluator, HandEvaluation
from src.strategy.equity_calculator import EquityCalculator
from src.strategy.pot_odds import PotOddsCalculator
from src.detection.game_state import GameState, BettingRound
from src.utils.logger import logger
from src.utils.config_loader import config_loader

@dataclass
class Decision:
    """Strategic decision."""
    action: str  # fold, call, raise
    amount_bb: Optional[float]  # Bet size in big blinds
    amount_chips: Optional[float]  # Bet size in chips
    confidence: float  # 0-1
    reasoning: List[str]
    hand_evaluation: HandEvaluation
    equity: float
    pot_odds: Optional[float]
    
    def __str__(self):
        return f"{self.action.upper()}" + (f" {self.amount_bb}BB" if self.amount_bb else "")

class DecisionEngine:
    """Make strategic poker decisions."""
    
    def __init__(self):
        """Initialize decision engine."""
        self.evaluator = HandEvaluator()
        self.equity_calc = EquityCalculator()
        self.pot_odds_calc = PotOddsCalculator()
        
        # Load strategy configuration
        try:
            self.config = config_loader.load('settings.json')
        except:
            self.config = {}
            
        self.style = self.config.get('strategy', {}).get('style', 'tight_aggressive')
        
        # Preflop hand ranges (simplified)
        self.preflop_ranges = self._load_preflop_ranges()
    
    def _load_preflop_ranges(self) -> dict:
        """Load preflop hand ranges."""
        # Simplified tight-aggressive ranges
        return {
            'premium': ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo'],
            'strong': ['TT', '99', 'AQs', 'AQo', 'AJs', 'KQs'],
            'playable': ['88', '77', '66', 'ATs', 'AJo', 'KQo', 'KJs', 'QJs'],
            'speculative': ['55', '44', '33', '22', 'A9s', 'A8s', 'KTs', 'QTs', 'JTs']
        }
    
    def decide(self, game_state: GameState) -> Decision:
        """
        Make strategic decision based on game state.
        
        Args:
            game_state: Current game state
        
        Returns:
            Decision object
        """
        logger.info(f"Making decision for {game_state.betting_round.value}")
        
        # Evaluate hand
        hand_eval = self.evaluator.evaluate(
            game_state.hole_cards,
            game_state.community_cards
        )
        
        # Calculate equity
        equity = self.equity_calc.calculate_equity(
            game_state.hole_cards,
            game_state.community_cards,
            num_opponents=game_state.num_opponents,
            iterations=1000
        )
        
        # Calculate pot odds
        pot_odds = None
        if game_state.current_bet > 0:
            pot_odds = self.pot_odds_calc.calculate_pot_odds(
                game_state.pot_size,
                game_state.current_bet
            )
        
        # Make decision based on betting round
        if game_state.betting_round == BettingRound.PREFLOP:
            decision = self._decide_preflop(game_state, hand_eval, equity, pot_odds)
        else:
            decision = self._decide_postflop(game_state, hand_eval, equity, pot_odds)
        
        logger.info(f"Decision: {decision}")
        return decision
    
    def _decide_preflop(self, 
                       game_state: GameState,
                       hand_eval: HandEvaluation,
                       equity: float,
                       pot_odds: Optional[float]) -> Decision:
        """Make preflop decision."""
        reasoning = []
        
        # Simplified preflop logic
        if hand_eval.hand_type.value >= 2:  # Pair or better
            action = "raise"
            amount_bb = 3.0
            confidence = 0.9
            reasoning.append("Strong starting hand")
        elif equity > 60:
            action = "raise"
            amount_bb = 3.0
            confidence = 0.8
            reasoning.append("High equity hand")
        elif game_state.current_bet == 0:
            action = "call"
            amount_bb = 1.0
            confidence = 0.6
            reasoning.append("No bet to call, see flop")
        elif pot_odds and self.pot_odds_calc.is_profitable_call(equity, pot_odds):
            action = "call"
            amount_bb = None
            confidence = 0.7
            reasoning.append("Good pot odds")
        else:
            action = "fold"
            amount_bb = None
            confidence = 0.8
            reasoning.append("Weak hand, fold")
        
        return Decision(
            action=action,
            amount_bb=amount_bb,
            amount_chips=amount_bb * 1.0 if amount_bb else None,  # Assume 1 BB = 1 chip for now
            confidence=confidence,
            reasoning=reasoning,
            hand_evaluation=hand_eval,
            equity=equity,
            pot_odds=pot_odds
        )
    
    def _decide_postflop(self,
                        game_state: GameState,
                        hand_eval: HandEvaluation,
                        equity: float,
                        pot_odds: Optional[float]) -> Decision:
        """Make postflop decision."""
        reasoning = []
        
        # Postflop logic based on hand strength and pot odds
        if hand_eval.hand_strength > 0.7:
            # Strong hand - raise
            action = "raise"
            amount_bb = game_state.pot_size * 0.75 / 1.0  # 75% pot bet
            confidence = 0.9
            reasoning.append(f"Strong hand: {hand_eval.description}")
            reasoning.append(f"High equity: {equity:.1f}%")
        
        elif hand_eval.hand_strength > 0.4:
            # Medium hand - call or raise based on pot odds
            if pot_odds and self.pot_odds_calc.is_profitable_call(equity, pot_odds):
                action = "call"
                amount_bb = None
                confidence = 0.7
                reasoning.append("Medium strength with good pot odds")
            else:
                action = "raise"
                amount_bb = game_state.pot_size * 0.5 / 1.0  # 50% pot bet
                confidence = 0.6
                reasoning.append("Medium hand, small raise")
        
        else:
            # Weak hand
            if pot_odds and equity > self.pot_odds_calc.pot_odds_to_percentage(pot_odds) + 10:
                action = "call"
                amount_bb = None
                confidence = 0.5
                reasoning.append("Weak but good pot odds for draw")
            else:
                action = "fold"
                amount_bb = None
                confidence = 0.9
                reasoning.append("Weak hand, fold")
        
        return Decision(
            action=action,
            amount_bb=amount_bb,
            amount_chips=amount_bb if amount_bb else None,
            confidence=confidence,
            reasoning=reasoning,
            hand_evaluation=hand_eval,
            equity=equity,
            pot_odds=pot_odds
        )
