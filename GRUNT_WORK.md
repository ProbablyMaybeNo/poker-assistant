# Poker AI Assistant - Grunt Work for Other Agents

**Status:** Core architecture complete. This document lists specific tasks for other AI agents to complete.

**CRITICAL RULES:**
1. NO PLACEHOLDER DATA - Use real GTO ranges, real solver output, real values
2. Test every change against the existing test suite
3. Maintain the existing interfaces - don't change method signatures without updating callers

---

## High Priority Tasks

### Task 1: Generate Preflop GTO Ranges with TexasSolver
**Estimated Complexity:** Medium
**Files to Create/Modify:**
- `database/preflop/open_ranges.json`
- `database/preflop/3bet_ranges.json`
- `database/preflop/call_ranges.json`
- `tools/generate_preflop_ranges.py`

**Instructions:**
1. Clone TexasSolver: `https://github.com/bupticybee/TexasSolver.git`
2. Build according to their instructions
3. Generate ranges for 6-max 100BB cash game:
   - Opening ranges for UTG, MP, CO, BTN, SB
   - 3bet ranges for each position vs each opener
   - Calling ranges vs opens and vs 3bets
4. Export to JSON format matching schema below

**JSON Schema for open_ranges.json:**
```json
{
  "UTG": {
    "AA": {"action": "raise", "sizing": 2.5, "frequency": 1.0},
    "AKs": {"action": "raise", "sizing": 2.5, "frequency": 1.0},
    "72o": {"action": "fold", "frequency": 1.0}
  },
  "MP": { ... },
  "CO": { ... },
  "BTN": { ... },
  "SB": { ... }
}
```

---

### Task 2: Add Community Card Regions to Anchor Config
**Estimated Complexity:** Low
**Files to Modify:**
- `config/anchor_config.json`

**Instructions:**
1. Add these regions to the `regions` object:
   - `community_cards`: Region containing all 5 community card positions
   - `pot_amount`: Region showing pot size
   - `player_stack`: Region showing player's chip stack
   - `current_bet`: Region showing current bet to call

**Note:** Exact pixel values depend on table resolution. User will need to calibrate.

---

### Task 3: Create Postflop Strategy Module
**Estimated Complexity:** High
**Files to Create:**
- `src/strategy/postflop_strategy.py`
- `database/postflop/board_textures.json`
- `database/postflop/cbet_strategy.json`

**Instructions:**
1. Follow the pattern in `preflop_strategy.py`
2. Implement board texture classification:
   - Dry (rainbow, unpaired, unconnected)
   - Wet (flush draws, straight draws)
   - Paired boards
   - Monotone boards
3. Implement continuation bet strategy based on:
   - Board texture
   - Hand strength (made hand vs draw)
   - Position (IP vs OOP)
   - Number of opponents
4. Return action + sizing + frequency + confidence

---

### Task 4: Implement Session Logger
**Estimated Complexity:** Medium
**Files to Create:**
- `src/utils/session_logger.py`
- `database/learning/` (session files created at runtime)

**Instructions:**
1. Create `SessionLogger` class that logs:
   - Timestamp
   - Game state (cards, pot, stack, position)
   - Decision made
   - Confidence level
   - Outcome (if detectable from next hand)
2. Store as JSON lines in `database/learning/session_YYYYMMDD_HHMMSS.jsonl`
3. Add configuration option to enable/disable logging

---

### Task 5: Upgrade to CUDA PyTorch
**Estimated Complexity:** Low
**Files to Modify:**
- `requirements.txt`
- `test_installation.py`

**Instructions:**
1. Replace current PyTorch with CUDA version:
   ```
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```
2. Update `requirements.txt` with correct CUDA versions
3. Add CUDA detection to `test_installation.py`:
   ```python
   import torch
   assert torch.cuda.is_available(), "CUDA not available"
   print(f"CUDA device: {torch.cuda.get_device_name(0)}")
   ```

---

### Task 6: Complete Anchor Calibration Tool GUI
**Estimated Complexity:** Medium
**Files to Modify:**
- `src/ui/calibration_tool.py`
- `tools/calibrate_anchors.py`

**Instructions:**
1. Add GUI workflow:
   - Step 1: Select stable anchor point (e.g., dealer button, table edge)
   - Step 2: Draw rectangle around hole cards region
   - Step 3: Draw rectangle around community cards region
   - Step 4: Draw rectangle around pot display
   - Step 5: Draw rectangle around stack display
   - Step 6: Draw rectangle around bet display
2. Save all regions relative to anchor position
3. Add validation that all required regions are defined
4. Add preview mode showing regions overlaid on screenshot

---

### Task 7: Integrate PreflopStrategy into DecisionEngine
**Estimated Complexity:** Low
**Files to Modify:**
- `src/strategy/decision_engine.py`

**Instructions:**
1. Import `PreflopStrategy` class
2. In `__init__`, create `self.preflop_strategy = PreflopStrategy()`
3. In `_decide_preflop`, call `self.preflop_strategy.get_open_action()` or `get_vs_raise_action()`
4. Convert `PreflopDecision` to existing `Decision` format
5. Keep existing heuristic as ultimate fallback

---

## Medium Priority Tasks

### Task 8: Add Board Texture Analysis
**Files to Create:**
- `src/strategy/board_analyzer.py`

**Instructions:**
1. Create `BoardAnalyzer` class
2. Implement `analyze(community_cards)` returning:
   - `is_paired`: bool
   - `is_monotone`: bool (3+ same suit)
   - `flush_possible`: bool
   - `straight_possible`: bool
   - `texture_score`: float (0=dry, 1=wet)
   - `high_card_rank`: str
3. Use in postflop decisions

---

### Task 9: Add Pot Odds and EV Display to Overlay
**Files to Modify:**
- `src/ui/display_manager.py`

**Instructions:**
1. Add pot odds calculation display
2. Add expected value display
3. Show equity as progress bar
4. Color-code recommendation (green=raise, yellow=call, red=fold)

---

### Task 10: Create Performance Monitor
**Files to Create:**
- `src/utils/performance.py`

**Instructions:**
1. Track timing for each pipeline step:
   - Screen capture time
   - Anchor detection time
   - Card detection time
   - OCR time
   - Decision time
   - Total frame time
2. Log warnings if any step exceeds threshold
3. Expose stats via method for debugging

---

## Low Priority Tasks (V2 Prep)

### Task 11: Multi-table Foundation
- Create `TableManager` class that can track multiple windows
- Each table gets its own `GameLoop` instance
- Shared strategy engine

### Task 12: Hand History Export
- Export completed hands to standard hand history format
- Support PokerStars format for analysis tools

### Task 13: Opponent Modeling Foundation
- Track opponent actions over time
- Calculate VPIP/PFR/AF statistics
- Store in SQLite database

---

## Testing Requirements

For each task, ensure:
1. `python test_installation.py` passes
2. `python test_full_system.py` passes
3. No new warnings/errors in logs
4. Code follows existing patterns (type hints, docstrings, logger usage)

---

## File Structure Reference

```
project/
├── config/
│   ├── anchor_config.json    # Anchor + regions (needs Task 2)
│   └── settings.json         # App settings
├── database/
│   ├── preflop/              # (Task 1)
│   │   ├── open_ranges.json
│   │   ├── 3bet_ranges.json
│   │   └── call_ranges.json
│   ├── postflop/             # (Task 3)
│   │   ├── board_textures.json
│   │   └── cbet_strategy.json
│   ├── spots/                # Future: solver outputs
│   └── learning/             # (Task 4)
├── src/
│   ├── strategy/
│   │   ├── preflop_strategy.py   # ✅ Created (needs data)
│   │   ├── postflop_strategy.py  # (Task 3)
│   │   ├── decision_engine.py    # (Task 7)
│   │   └── board_analyzer.py     # (Task 8)
│   └── utils/
│       ├── session_logger.py     # (Task 4)
│       └── performance.py        # (Task 10)
└── tools/
    └── generate_preflop_ranges.py  # (Task 1)
```

---

## Contact / Questions

If you encounter blockers or need clarification:
1. Check existing code patterns in similar modules
2. Review HANDOFF.md for context
3. Check test files for expected behavior
4. Leave TODO comments for unresolved questions
