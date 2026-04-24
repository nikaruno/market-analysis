# 📊 Market Analysis System

**Simple. No Docker. Just Works.**

---

## 🚀 Quick Start (3 Steps)

```bash
# 1. Extract
tar -xzf market-analysis-SIMPLE.tar.gz
cd market-analysis

# 2. Install (one time)
bash install.sh

# 3. Run GUI
bash run_gui.sh
```

Open browser: **http://localhost:8501**

---

## 📦 What's Included

- **10 analysis modules** - Download data, compute metrics, technical analysis
- **2 automation scripts** - Run full pipeline, generate reports
- **1 GUI app** - Interactive dashboard with working "Run Analysis" button
- **3 simple scripts** - install.sh, run_gui.sh, run_analysis.sh

**Total: 16 files. Clean. Simple.**

---

## 📋 Files

```
market-analysis/
├── install.sh              # Run once to install packages
├── run_gui.sh              # Start the GUI
├── run_analysis.sh         # Run analysis without GUI
├── README.md               # This file
│
├── src/exMarket/           # 10 analysis modules
│   ├── download_market_data.py
│   ├── market_regime.py
│   ├── scrape_fundamentals.py
│   ├── technical_analysis.py
│   └── ... (6 more)
│
├── automation_scripts/     # 2 automation scripts
│   ├── automate_analysis_with_tech.py
│   └── report_generator_enhanced.py
│
├── gui/                    # 1 GUI app
│   └── app.py
│
└── .streamlit/             # 1 config
    └── config.toml
```

---

## 🎯 Usage

### Option 1: Interactive GUI

```bash
bash run_gui.sh
```

Then:
- Open http://localhost:8501
- Click "▶️ Run Analysis" button
- Wait 15-20 minutes
- View results in tabs

### Option 2: Command Line

```bash
bash run_analysis.sh
```

View report:
```bash
cat data/executive_summary.md
```

---

## ✨ GUI Features

**5 Tabs:**
1. 📈 Overview - Charts, distributions, stats
2. 🏆 Top Companies - Rankings, best in class
3. 📊 Technical Analysis - RSI, MACD, signals
4. 📄 Full Report - Complete markdown report
5. 📚 Help - All formulas explained

**Sidebar Controls:**
- Adjust quality score weights (6 sliders)
- Select sectors to analyze
- Choose companies per sector (5-30)
- **▶️ Run Analysis button** (working!)
- Reset to defaults

---

## ⚙️ Configuration

Edit `src/exMarket/scrape_fundamentals.py` line 197:

```python
top_n=10  # Change to 20 for more companies
```

Or use the slider in the GUI!

---

## 📊 Output

After running:

```
data/
├── executive_summary.md       # 3-page report
├── technical_analysis.csv     # All indicators
├── fundamentals/
│   └── absolute_scores.csv    # Quality rankings
├── technical_charts/          # Stock charts
└── plots/                     # Regime charts
```

---

## 📝 Requirements

- Python 3.8 or higher
- Internet connection
- 4GB RAM
- 2GB disk space

---

## 🐛 Troubleshooting

**"python3: command not found"**
→ Install Python 3.8+

**"streamlit: command not found"**
→ Run `bash install.sh` again

**GUI won't start**
→ Try: `python3 -m streamlit run gui/app.py`

**No data in GUI**
→ Click "Run Analysis" button or run `bash run_analysis.sh`

---

## 💡 Tips

- First time: Click "Run Analysis" to generate data (takes 15-20 mins)
- Adjust weights and re-run to see how rankings change
- Refresh browser page after analysis completes
- View charts in `data/technical_charts/` folder

---

**Simple. No Docker. Works every time.** 🚀
