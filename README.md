# CANVAS
**CANVAS: CANOPUS and SIRIUS Visualization & Analysis System**

## Overview
CANVAS is an interactive Dash application for **visualization and interpretation of LC-MS metabolomics data** integrated with [MSDIAL](https://systemsomicslab.github.io/compms/msdial/main.html) and processed with the [SIRIUS](https://bio.informatik.uni-jena.de/software/sirius/) workflow, including compound classification results from **CANOPUS**.  

The tool enables researchers to:
- Integrate SIRIUS and CANOPUS outputs with intensity-based measurements.
- Explore metabolite classes dynamically using thresholds and ontology levels.
- Visualize results with **sunburst plots, bar charts, PCA and random forest classifier**.
- Compare metabolite distributions across samples or conditions.
- Streamline hypothesis generation in untargeted metabolomics workflows.

---

## Features
- 📊 **Interactive visualizations** (sunburst, bar charts, PCA, random forest).  
- 🧭 **Dynamic filtering** by class confidence and Sirius annotation scores, by hierarchy levels and intensity levels.  
- 🔍 **Exploration of SIRIUS & CANOPUS outputs** with user-friendly controls.  
- 🧪 **Example datasets** provided (plant, lipidomics, human cell metabolomics).  

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/CANVAS.git
cd CANVAS
````
### 2. Install dependencies

```bash
pip install -r requirements.txt
````

### 3. Run CANVAS

```bash
python app.py
````
This should automatically open a new navigator windows on your computer on the following adress (http://127.0.0.1:8050)
