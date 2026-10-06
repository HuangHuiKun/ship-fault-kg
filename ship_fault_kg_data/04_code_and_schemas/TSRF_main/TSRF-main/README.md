# TSRF - Thermodynamic Simulation-Assisted Random Forest

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/Paper-Published-success.svg)](#citation)

> **Code Repository for**: _"Thermodynamic simulation-assisted random forest: Towards explainable fault diagnosis of combustion chamber components of marine diesel engines"_

## Overview

This repository contains the implementation code for our paper on **explainable fault diagnosis** of marine diesel engine combustion chamber components using thermodynamic simulation-assisted machine learning.

**Key Contributions**:

- 🔥 Typical fault dataset of marine diesel engines
- 🤖 Multi-model comparison: KNN, Random Forest, SVM
- 🔍 SHAP-based interpretability analysis with bivariate feature interactions
- 🎯 High accuracy: ~99% for combustion chamber fault diagnosis

**6 Fault Types**: Normal | Head-crack | Liner-wear | Piston-ablation | Ring-adhesion | Ring-wear

## Project Structure

```
TSRF/
├── main.py                      # Main training pipeline
├── interactive_shap.py          # Interactive SHAP analysis tool
├── run_interactive_shap.bat     # Quick launcher (Windows)
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── LICENSE                      # MIT License
├── data/                        # Dataset
│   ├── Normal.csv
│   ├── Head-crack.csv
│   ├── Liner-wear.csv
│   ├── Piston-ablation.csv
│   ├── Ring-adhesion.csv
│   └── Ring-wear.csv
├── src/                         # Source modules
│   ├── data_loader.py
│   ├── models.py
│   ├── visualization.py
│   └── shap_analysis.py         # SHAP analyzer
└── outputs/                     # Generated outputs
```

## Requirements

- Python 3.8 or higher
- Required packages listed in `requirements.txt`

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train Models

```bash
python main.py
```

### 3. SHAP Analysis (Interactive)

**Windows (Double-click)**:

```bash
run_interactive_shap.bat
```

**IDE (PyCharm/VS Code)**:

- **Option 1**: Right-click `interactive_shap.py` → Run
- **Option 2**: Open terminal in IDE → `python interactive_shap.py`
- **Option 3** (Windows): Right-click `run_interactive_shap.bat` → Open with → Command Prompt

**Command Line**:

```bash
python interactive_shap.py
```

**Example Session**:

```
Fault type: 0                    # Select class (0-5)
Plot type: 4                     # Bivariate dependence
Feature pairs: P03-P04,P05-P06   # Use P01-P14 codes
```

**Output**: SHAP visualizations in `outputs/` directory with P01-P14 feature codes

---

## Features

### Model Training

- **3 ML Algorithms**: KNN, Random Forest, SVM
- **Automated Evaluation**: Confusion matrices, ROC curves, model comparison
- **Feature Selection**: Optional 9-feature subset (via `--use-feature-selection`)
- **Reproducibility**: Fixed random_state=20

### SHAP Analysis

- **5 Plot Types**: Waterfall | Beeswarm | Composite | Dependence | Interaction
- **Bivariate Analysis**: Feature interaction visualization using P01-P14 codes
- **Interactive Mode**: User selects fault types, samples, and feature pairs
- **Batch Processing**: Multi-class analysis support

---

## Advanced Usage

### Custom Training

```bash
# With feature selection
python main.py --use-feature-selection

# With SHAP analysis
python main.py --enable-shap

# Specific classes only
python main.py --enable-shap --shap-classes "0,2,4"
```

### Programmatic SHAP

```python
from src.shap_analysis import SHAPAnalyzer

# Initialize analyzer
analyzer = SHAPAnalyzer(model, X_train, X_test, feature_names)

# Generate bivariate plot
analyzer.plot_dependence('P03', feature_y='P04', class_idx=0)
```

---

## Output Files

### Model Performance

- `confusion_matrix_*.png` - Confusion matrices (KNN, RF, SVM)
- `ROC_*.png` - ROC curves
- `model_comparison.png` - Performance comparison chart
- `ROC_data_*.csv`, `model_comparison.csv` - Raw metrics

### SHAP Visualizations (using P01-P14 codes)

- `SHAP_waterfall_F*_sample*.png` - Single sample explanation
- `SHAP_beeswarm_F*.png` - Global feature importance
- `SHAP_composite_F*.png` - Combined importance view
- `SHAP_dependence_bivariate_F*_P**_vs_P**.png` - Feature interactions
- `SHAP_interaction_F*.png` - Interaction strength matrix

---

## Dataset

**6 Health States**: Normal | Head-crack | Linner-wear | Piston-ablation | Ring-adhesion | Ring-wear

**14 Features** (P01-P14):

```
P01: Cylinder-Pre          P08: TurbWallHeatFlow
P02: Cylinder-Tem          P09: Turbine-out-Tem
P03: BlowBy                P10: TurbinePower
P04: HeadWallHeatFlow      P11: Out-Pre
P05: BlowByHeatFlow        P12: Turbine-out-Pre
P06: Turbine-in-Pre        P13: Head-Tem
P07: PistWallHeatFlow      P14: Out-Tem
```

---

## Model Configuration

| Model             | Key Parameters                              |
| ----------------- | ------------------------------------------- |
| **KNN**           | Grid Search: n_neighbors=[3-15], 10-fold CV |
| **Random Forest** | n_estimators=20, random_state=20            |
| **SVM**           | Linear kernel, random_state=20              |

**Data Split**: 1296 train / 216 test (stratified)  
**Preprocessing**: StandardScaler normalization

---

## Note on Reproducibility

> ⚠️ **Important**: The results produced by this implementation may differ slightly from those reported in the paper, although the overall accuracy remains comparable. This is due to:
>
> - **Library version differences**: Variations in scikit-learn, SHAP, and other dependency versions
> - **Random state sensitivity**: Minor differences in random number generation across platforms
> - **Hardware/software environment**: Floating-point precision variations between systems
>
> These factors are common in machine learning research and do not affect the validity of the methodology or conclusions.

---

## Citation

 If you find this work useful for your research, please consider reading the following paper 😊:

```bibtex
@article{luo2025thermodynamic,
  title={Thermodynamic simulation-assisted random forest: Towards explainable fault diagnosis of combustion chamber components of marine diesel engines},
  author={Luo, Congcong and Zhao, Minghang and Fu, Xuyun and Zhong, Shisheng and Fu, Song and Zhang, Kai and Yu, Xiaoxia},
  journal={Measurement},
  year={2025},
  volume={251},
  pages={117252},
  publisher={Elsevier},
  doi={10.1016/j.measurement.2025.117252}
}
```

## License

MIT License - See [LICENSE](LICENSE) file for details
