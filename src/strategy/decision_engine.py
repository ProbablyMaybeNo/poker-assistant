"""
Main strategic decision engine.
Combines GTO preflop lookup, hand evaluation, equity, and pot odds to suggest actions.

Architecture:
- Preflop: Uses PreflopStrategy for GTO-based decisions
- Postflop: Uses hand evaluation + equity + pot odds heuristics
"""
from typing import Optional, List
from dataclasses import dataclass

from src.strategy.hand_evaluator import HandEvaluator, HandEvaluation
from src.strategy.equity_calculator import EquityCalculator
from src.strategy.pot_odds import PotOddsCalculator
from src.strategy.preflop_strategy import PreflopStrategy, Position, PreflopAction
from src.detection.game_state import GameState, BettingRound
from src.utils.logger import logger
from src.utils.config_loader import config_loader


@dataclass
class Decision:
    """Strategic decision output."""
    action: str  # fold, call, raise, check
    amount_bb: Optional[float]  # Bet size in big blinds
    amount_chips: Optional[float]  # Bet size in chips
    confidence: float  # 0-1 confidence score
    reasoning: List[str]  # Explanation for the decision
    hand_evaluation: HandEvaluation
    equity: float  # Win probability percentage
    pot_odds: Optional[float]  # Pot odds ratio
    source: str = "unknown"  # gto_solver, heuristic, or mixed

    def __str__(self):
        action_str = self.action.upper()
        if self.amount_bb:
            action_str += f" {self.amount_bb:.1f}BB"
        return f"{action_str} ({self.confidence*100:.0f}% conf, {self.source})"


class DecisionEngine:
    """
    Main poker decision engine using GTO lookup + heuristics.

    Preflop: GTO ranges from database/preflop/
    Postflop: Hand strength + equity + pot odds heuristics
    """

    def __init__(self):
        """Initialize decision engine with all strategy components."""
        # Core evaluators
        self.hand_evaluator = HandEvaluator()
        self.equity_calc = EquityCalculator()
        self.pot_odds_calc = PotOddsCalculator()

        # GTO preflop strategy
        self.preflop_strategy = PreflopStrategy()

        # Load configuration
        try:
            self.config = config_loader.load('settings.json')
        except Exception:
            self.config = {}

        self.style = self.config.get('strategy', {}).get('style', 'tight_aggressive')

        # Big blind size for chip calculations (default 1.0, can be updated)
        self.bb_size = 1.0

        logger.info(f"DecisionEngine initialized with style: {self.style}")

    def set_bb_size(self, bb_size: float):
        """Set big blind size for accurate chip calculations."""
        self.bb_size = bb_size
        logger.debug(f"BB size set to {bb_size}")

    def decide(self, game_state: GameState) -> Decision:
        """
        Make strategic decision based on current game state.

        Args:
            game_state: Current game state with cards, pot, stack, etc.

        Returns:
            Decision object with action, sizing, confidence, and reasoning
        """
        logger.info(f"Deciding for {game_state.betting_round.value}: {game_state.hole_cards}")

        # Validate we have hole cards
        if len(game_state.hole_cards) < 2:
            return self._create_error_decision("No hole cards detected")

        # Evaluate hand
        hand_eval = self.hand_evaluator.evaluate(
            game_state.hole_cards,
            game_state.community_cards
        )

        # Calculate equity (reduce iterations preflop for speed)
        iterations = 500 if game_state.betting_round == BettingRound.PREFLOP else 1000
        equity = self.equity_calc.calculate_equity(
            game_state.hole_cards,
            game_state.community_cards,
            num_opponents=max(1, game_state.num_opponents),
            iterations=iterations
        )

        # Calculate pot odds if facing a bet
        pot_odds = None
        if game_state.current_bet and game_state.current_bet > 0:
            pot_odds = self.pot_odds_calc.calculate_pot_odds(
                game_state.pot_size,
                game_state.current_bet
            )

        # Route to appropriate decision method
        if game_state.betting_round == BettingRound.PREFLOP:
            decision = self._decide_preflop_gto(game_state, hand_eval, equity, pot_odds)
        else:
            decision = self._decide_postflop(game_state, hand_eval, equity, pot_odds)

        logger.info(f"Decision: {decision}")
        return decision

    def _decide_preflop_gto(self,
                           game_state: GameState,
                           hand_eval: HandEvaluation,
                           equity: float,
                           pot_odds: Optional[float]) -> Decision:
        """
        Make preflop decision using GTO lookup.

        Uses PreflopStrategy for position-aware GTO decisions.
        """
        # Determine our position (default to BTN if unknown)
        position = self._get_position(game_state)

        # Determine if we're facing a raise
        facing_raise = game_state.current_bet and game_state.current_bet > self.bb_size

        if facing_raise:
            # Facing a raise - use vs_raise logic
            # Assume raiser is one position earlier (simplified)
            raiser_position = self._estimate_raiser_position(position)
            preflop_decision = self.preflop_strategy.get_vs_raise_action(
                hand=game_state.hole_cards,
                our_position=position,
                raiser_position=raiser_position,
                raise_size_bb=game_state.current_bet / self.bb_size if self.bb_size > 0 else 2.5,
                stack_bb=game_state.stack_size / self.bb_size if self.bb_size > 0 else 100
            )
        else:
            # No raise - opening decision
            preflop_decision = self.preflop_strategy.get_open_action(
                hand=game_state.hole_cards,
                position=position,
                stack_bb=game_state.stack_size / self.bb_size if self.bb_size > 0 else 100
            )

        # Convert PreflopDecision to Decision
        action = preflop_decision.action.value
        amount_bb = preflop_decision.sizing_bb

        # Build reasoning
        reasoning = [preflop_decision.reasoning]
        if preflop_decision.frequency < 1.0:
            reasoning.append(f"Mixed strategy: {preflop_decision.frequency*100:.0f}% frequency")
        reasoning.append(f"Position: {position.value}")
        reasoning.append(f"Equity: {equity:.1f}%")

        return Decision(
            action=action,
            amount_bb=amount_bb,
            amount_chips=amount_bb * self.bb_size if amount_bb else None,
            confidence=preflop_decision.confidence,
            reasoning=reasoning,
            hand_evaluation=hand_eval,
            equity=equity,
            pot_odds=pot_odds,
            source=preflop_decision.source
        )

    def _decide_postflop(self,
                        game_state: GameState,
                        hand_eval: HandEvaluation,
                        equity: float,
                        pot_odds: Optional[float]) -> Decision:
        """
        Make postflop decision using equity + pot odds heuristics.

        Strategy based on hand strength categories:
        - Strong (>0.7): Value bet/raise
        - Medium (0.4-0.7): Pot odds dependent
        - Weak (<0.4): Check/fold unless good pot odds
        """
        reasoning = []
        source = "heuristic"

        # Calculate stack-to-pot ratio for bet sizing
        spr = game_state.stack_size / game_state.pot_size if game_state.pot_size > 0 else 10

        # Check if we can check (no bet to call)
        can_check = game_state.current_bet == 0 or game_state.current_bet is None

        # Strong hand (>70% strength)
        if hand_eval.hand_strength > 0.7:
            reasoning.append(f"Strong hand: {hand_eval.description}")
            reasoning.append(f"Equity: {equity:.1f}%")

            if can_check:
                # Bet for value
                action = "raise"
                # Bet 66-75% pot with strong hands
                bet_pct = 0.66 if spr > 3 else 0.75
                amount_bb = (game_state.pot_size * bet_pct) / self.bb_size
                confidence = 0.85
                reasoning.append("Betting for value")
            else:
                # Raise for value
                action = "raise"
                amount_bb = (game_state.pot_size * 0.75 + game_state.current_bet * 2) / self.bb_size
                confidence = 0.85
                reasoning.append("Raising for value")

        # Medium hand (40-70% strength)
        elif hand_eval.hand_strength > 0.4:
            reasoning.append(f"Medium hand: {hand_eval.description}")
            reasoning.append(f"Equity: {equity:.1f}%")

            if can_check:
                # Mix between check and bet
                if equity > 55:
                    action = "raise"
                    amount_bb = (game_state.pot_size * 0.5) / self.bb_size
                    confidence = 0.65
                    reasoning.append("Thin value bet")
                else:
                    action = "check"
                    amount_bb = None
                    confidence = 0.7
                    reasoning.append("Pot control with medium hand")
            else:
                # Facing bet - use pot odds
                if pot_odds and self.pot_odds_calc.is_profitable_call(equity, pot_odds):
                    action = "call"
                    amount_bb = None
                    confidence = 0.7
                    reasoning.append("Calling with good pot odds")
                    if pot_odds:
                        reasoning.append(f"Pot odds: {pot_odds:.1f}:1")
                elif equity > 60:
                    action = "call"
                    amount_bb = None
                    confidence = 0.6
                    reasoning.append("Calling with equity advantage")
                else:
                    action = "fold"
                    amount_bb = None
                    confidence = 0.65
                    reasoning.append("Folding medium hand facing aggression")

        # Weak hand (<40% strength)
        else:
            reasoning.append(f"Weak hand: {hand_eval.description}")

            if can_check:
                action = "check"
                amount_bb = None
                confidence = 0.8
                reasoning.append("Checking with weak hand")
            else:
                # Facing bet with weak hand
                if pot_odds and equity > self.pot_odds_calc.pot_odds_to_percentage(pot_odds) + 5:
                    action = "call"
                    amount_bb = None
                    confidence = 0.5
                    reasoning.append("Drawing with pot odds")
                else:
                    action = "fold"
                    amount_bb = None
                    confidence = 0.85
                    reasoning.append("Folding weak hand")

        return Decision(
            action=action,
            amount_bb=amount_bb,
            amount_chips=amount_bb * self.bb_size if amount_bb else None,
            confidence=confidence,
            reasoning=reasoning,
            hand_evaluation=hand_eval,
            equity=equity,
            pot_odds=pot_odds,
            source=source
        )

    def _get_position(self, game_state: GameState) -> Position:
        """
        Determine player position from game state.

        Falls back to BTN if position unknown (most common assumption).
        """
        if game_state.position:
            # Map from game_state Position enum to strategy Position enum
            pos_map = {
                "UTG": Position.UTG,
                "UTG+1": Position.MP,
                "MP": Position.MP,
                "MP+1": Position.CO,
                "CO": Position.CO,
                "BTN": Position.BTN,
                "SB": Position.SB,
                "BB": Position.BB,
            }
            pos_str = game_state.position.value if hasattr(game_state.position, 'value') else str(game_state.position)
            return pos_map.get(pos_str, Position.BTN)

        # Default to BTN (optimistic assumption for opens)
        return Position.BTN

    def _estimate_raiser_position(self, our_position: Position) -> Position:
        """
        Estimate the raiser's position based on our position.

        Simple heuristic: assume raiser is ~2 positions earlier.
        """
        position_order = [Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB, Position.BB]

        try:
            our_idx = position_order.index(our_position)
            # Raiser is typically earlier position
            raiser_idx = max(0, our_idx - 2)
            return position_order[raiser_idx]
        except ValueError:
            return Position.MP  # Default assumption

    def _create_error_decision(self, error_msg: str) -> Decision:
        """Create a default fold decision when error occurs."""
        from src.strategy.hand_evaluator import HandType

        return Decision(
            action="fold",
            amount_bb=None,
            amount_chips=None,
            confidence=0.0,
            reasoning=[f"Error: {error_msg}"],
            hand_evaluation=HandEvaluation(
                hand_type=HandType.HIGH_CARD,
                hand_strength=0.0,
                description="Unknown",
                best_five=[],
                kickers=[]
            ),
            equity=0.0,
            pot_odds=None,
            source="error"
        )
