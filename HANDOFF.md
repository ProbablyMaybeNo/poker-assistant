# Poker AI Assistant - Handoff Document

**Date:** 2026-01-27
**Status:** Alpha / Integrated

## Overview

This project is a real-time Poker AI Assistant designed to capture a poker table window, detect cards via template matching and OCR, calculate hand strength and equity, and provide strategic advice via a transparent overlay.

The system is modularized into:

1. **Capture**: Finds window, grabs screen, maps regions.
2. **Detection**: Recognizes cards (Suit/Rank) and parses game state (Pot, Bet, Stack).
3. **Strategy**: Evaluates expected value (EV) using Hand Strength, Equity (Monte Carlo), and Pot Odds.
4. **UI**: Displays recommendations on a transparent PyQt5 overlay.

## Environment & Setup

- **Python Version**: 3.10+ recommended.
- **Virtual Environment**: `venv` (located in project root).
- **Dependencies**: Listed in `requirements.txt`. Key libs: `opencv-python`, `numpy`, `mss`, `pytesseract`, `PyQt5`, `pywin32`.
- **Tesseract**: Requires Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` (configurable in `src/detection/text_reader.py`).

## Core Components

### 1. Capture System (`src/capture/`)

- `window_finder.py`: Locates "PokerStars" (configurable) window handle.
- `anchor_manager.py`: Finds a static template (anchor) to align all other regions (cards, text).
- **Critical**: Run `tools/calibrate_anchors.py` if the table size/layout changes.

### 2. Detection System (`src/detection/`)

- `card_detector.py`: Uses template matching (`cv2.matchTemplate`) to identify cards in `models/templates/`.
- `text_reader.py`: Wraps Tesseract to read numbers (Stack, Pot).
- `game_state.py`: Aggregates all info into a `GameState` object.

### 3. Strategy Engine (`src/strategy/`)

- `hand_evaluator.py`: Determines hand rank (Flush, Pair, etc.) and granular strength (0.0 - 1.0).
- `equity_calculator.py`: Runs Monte Carlo sims (1000+ iterations) to estimate Win %.
- `decision_engine.py`: Combines Equity, Pot Odds, and Rules logic to output Fold/Call/Raise.

### 4. UI (`src/ui/`)

- `display_manager.py`: Manages the PyQt5 application.
- `overlay.py` (Merged into display_manager): Draws the transparent HUD.

## Current Status & Integration

- **`main.py`**: The fully integrated loop. It initializes the UI in the main thread and runs the Game Logic in a generic `QThread`.
- **Verification**: `test_full_system.py` passes all integration checks (imports, classes, window mocking).
- **Strategy Verification**: `test_strategy.py` passes logic checks (Equity thresholds, Hand ID).

## How to Run

### 1. Activate Environment

```bash
.\venv\Scripts\Activate.ps1
```

### 2. Run the Assistant

```bash
python src/main.py
```

* Ensure a poker client (e.g., PokerStars) or a screenshot of one is visible.
- The overlay should appear (transparent w/ HUD box).

### 3. Run Tests

```bash
# Full Integration Test
python test_full_system.py

# Strategy Logic Test
python test_strategy.py
```

## Known Issues / Optimization Opportunities

1. **Anchor Calibration**: The `anchor_config.json` is user-specific. A new user **must** run calibration or the system won't find the table.
2. **Tesseract Path**: Hardcoded in `text_reader.py`. Should be moved to `settings.json`.
3. **Performance**: Monte Carlo simulations (1000 iter) take ~50-100ms. If frame rate drops, consider optimizing `equity_calculator.py` (e.g., lookup tables or vectorization).
4. **OCR Reliability**: Tesseract can be flaky with small fonts. Consider training a custom small-CNN for digits if reliability is low.
5. **Multi-Table**: Currently supports only one active window.

## File Structure

```
project/
├── config/             # JSON configs
├── models/             # Templates (Card images)
├── src/
│   ├── capture/        # Screen & Window logic
│   ├── detection/      # Computer Vision (Cards/Text)
│   ├── strategy/       # Poker Logic (Math/Equity)
│   ├── ui/             # PyQt5 Overlay
│   ├── utils/          # Logger, ConfigLoader
│   └── main.py         # Entry point
├── tools/              # calibration & template creation scripts
├── tests/              # Additional unit tests
├── test_full_system.py # Integration test
└── test_strategy.py    # Strategy test
```

## Next Steps for AI Agent

1. **Optimize**: Profile `main.py` loop time.
2. **Refine**: Improve `DecisionEngine` thresholds based on real hand history analysis.
3. **UI**: Add "History" or "Opponent Stats" to the overlay.
