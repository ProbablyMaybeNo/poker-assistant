# Poker AI Assistant

An AI-powered poker assistant that uses computer vision to watch your PokerStars game in real-time and provides strategic suggestions via a transparent overlay.

## 🎯 Purpose

This is a **learning and practice tool** designed for use with play money only on PokerStars simulator. It demonstrates advanced concepts in:
- Computer Vision & Image Processing
- Machine Learning & AI
- Real-time Systems
- Game Theory & Probability
- Software Architecture

## ⚠️ Disclaimer

**For Educational Purposes Only**: This tool is designed for learning poker strategy and practicing with play money. Using automated assistance in real-money poker games may violate terms of service and is not recommended.

## 🛠️ System Requirements

- **OS**: Windows 11
- **Python**: 3.11+ (tested with 3.13.5)
- **GPU**: RTX 4060 8GB or similar (optional, for GPU acceleration)
- **RAM**: 64GB recommended
- **Software**: PokerStars client

## 📋 Features

### Phase 1: Environment Setup ✅
- [x] Project structure and virtual environment
- [x] Dependency management
- [x] Configuration system
- [x] Logging infrastructure

### Phase 2: Screen Capture (In Progress)
- [ ] Window detection for PokerStars
- [ ] Region-based screen capture
- [ ] Interactive calibration tool
- [ ] Screenshot management

### Phase 3: Card Detection (Planned)
- [ ] Template matching for card recognition
- [ ] OCR for chip counts and pot amounts
- [ ] Game state tracking
- [ ] Detection accuracy optimization

### Phase 4: Strategy Engine (Planned)
- [ ] Hand evaluation (all poker hands)
- [ ] Equity calculator (Monte Carlo simulation)
- [ ] Pot odds calculator
- [ ] Decision engine with strategic recommendations

### Phase 5: Overlay & Integration (Planned)
- [ ] Transparent overlay window
- [ ] Real-time display updates
- [ ] Complete system integration
- [ ] Performance optimization

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ProbablyMaybeNo/poker-assistant.git
   cd poker-assistant
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python test_installation.py
   ```

### Running the Application

```bash
# Activate virtual environment
venv\Scripts\activate

# Run main application
python src/main.py
```

## 📁 Project Structure

```
poker_assistant/
├── config/              # Configuration files
│   ├── settings.json    # Application settings
│   ├── regions.json     # Screen region coordinates
│   └── poker_rules.json # Game constants
├── database/            # Strategy databases and charts
├── logs/                # Application logs
├── models/              # AI models and card templates
│   ├── card_detector/   # YOLO model files
│   └── card_templates/  # Template matching images
├── screenshots/         # Test images and calibration
├── src/                 # Source code
│   ├── capture/         # Screen capture system
│   ├── detection/       # Card and text detection
│   ├── strategy/        # Hand evaluation and decision engine
│   ├── ui/              # Overlay and calibration tools
│   └── utils/           # Logger and config utilities
├── tools/               # Utility scripts
├── venv/                # Virtual environment
├── .gitignore
├── README.md
├── requirements.txt
└── test_installation.py
```

## 🧪 Testing

Run the installation verification:
```bash
python test_installation.py
```

This will verify:
- All required packages are installed
- CUDA/GPU availability (optional)
- Project directory structure
- Configuration files

## 📚 Dependencies

### Core Libraries
- **numpy** - Numerical computing
- **pillow** - Image processing
- **opencv-python** - Computer vision
- **mss** - Screen capture

### AI/ML Libraries
- **torch** - PyTorch deep learning framework
- **torchvision** - Computer vision models
- **ultralytics** - YOLO object detection

### OCR & UI
- **pytesseract** - Optical character recognition
- **PyQt5** - GUI framework

### Utilities
- **python-dotenv** - Environment configuration
- **tqdm** - Progress bars
- **pywin32** - Windows API access

See `requirements.txt` for complete list with versions.

## 🎓 Learning Outcomes

By building and using this project, you'll gain experience with:

- **Computer Vision**: Template matching, image preprocessing, OCR, object detection
- **Machine Learning**: Monte Carlo simulation, probability calculations, decision trees
- **Software Engineering**: Modular architecture, configuration management, logging
- **Game Theory**: Poker hand rankings, pot odds, equity, position-based strategy
- **Python Development**: PyTorch, OpenCV, PyQt5, multi-threaded applications

## 🔧 Configuration

### Settings (`config/settings.json`)

Configure capture interval, detection thresholds, overlay appearance, strategy style, and performance parameters.

### Regions (`config/regions.json`)

Define screen regions for cards, pot, player stack, and action buttons. Use the calibration tool (Phase 2) to set these coordinates.

## 🐛 Troubleshooting

### Common Issues

**Python not found**
- Install Python 3.11+ and add to PATH

**Virtual environment activation fails**
- Run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell

**PyTorch CUDA not available**
- Update NVIDIA drivers
- Reinstall PyTorch with CUDA: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

**PokerStars window not found**
- Ensure PokerStars is running
- Check window title in `config/settings.json`
- Try running as administrator

**Cards not detected**
- Recalibrate regions using the calibration tool
- Adjust confidence threshold in settings
- Verify screenshot quality

See `logs/errors.log` for detailed error information.

## 📝 Development Status

**Current Phase**: Phase 1 Complete ✅
**Next Phase**: Phase 2 - Screen Capture System

### Phase 1 Completion Checklist
- [x] Project structure created
- [x] Virtual environment setup
- [x] All dependencies installed
- [x] Configuration files created
- [x] Logger and config utilities implemented
- [x] Installation tests passing

## 🤝 Contributing

This is an educational project. Contributions, suggestions, and improvements are welcome!

## 📄 License

This project is for educational purposes. Please use responsibly and in accordance with PokerStars Terms of Service.

## 🔗 Resources

- [OpenCV Documentation](https://docs.opencv.org/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [Poker Strategy Resources](https://upswingpoker.com/)

## 📧 Contact

**GitHub**: [@ProbablyMaybeNo](https://github.com/ProbablyMaybeNo)

---

**Remember**: This tool is for learning only. Use responsibly with play money for practice purposes. 🎯♠️♥️♣️♦️
