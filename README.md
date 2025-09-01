sies# CANVAS
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


## Data Input processing

CANVAS uses 4 different input files:
- One csv file that contains the aligned, and integrated intensity features. MSDIAL is used for this app, but other LC/MS/MS extracting softwares should work with the right formating.
- Two csv files obtained from the Sirius processing: The structure file from Sirius:CSI:FingerID and the canopus file from CANOPUS.
- One metadata file containing all the variable to considerate.

  ### 1. Integrated peak file
  The easiest way to start this dash app is to use integrated features extracted with MSDIAL. Diverse tutorials for extracting and integrating LC/MS/MS raw data from DIA or DDA experiments can be found on the github of [MSDIAL] (https://systemsomicslab.github.io/mtbinfo.github.io/MS-DIAL/tutorial.html#chapter-2). 
  Briefly, after the aligment and integration, you should be able to export bith the aligned mat file needed for Sirius processing and the list of extracted areas.
  <img width="1279" height="908" alt="image" src="https://github.com/user-attachments/assets/6e3a0898-aa6a-40ea-b41a-daf9dd0b7ee6" /> <img width="432" height="750" alt="image" src="https://github.com/user-attachments/assets/a158103a-fb59-494b-babb-585ae7e6bc84" />


