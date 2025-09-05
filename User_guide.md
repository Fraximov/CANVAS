# CANVAS User Guide
**CANVAS: CANOPUS and SIRIUS Visualization & Analysis System**

This document provides a detailed guide to using CANVAS, including input preparation, data processing, filters, and analysis features.

---

## Data Input Processing

CANVAS requires **four input files**:

1. **Integrated intensity features** (`.csv`)  
   - Exported from MSDIAL or other LC–MS/MS software.  
   - Contains aligned and integrated peak intensities.

2. **SIRIUS structure output** (`structure_identification.tsv`)  
   - Exported from the SIRIUS “Summaries” tab.  
   - Recommended to use the top 1 hit.

3. **CANOPUS output** (`canopus_structure_identification.tsv`)  
   - Class annotations from SIRIUS/CANOPUS export.  

4. **Metadata file** (`.csv`)  
   - User-generated, contains experimental variables and sample information.  
   - Must have a first column named `name_file`.  
   - Blank samples should include the keyword `Blank`.

---

### 1. Integrated Area Peak File (MSDIAL)
The easiest starting point is integrated features extracted with MSDIAL.  
Tutorials: [MSDIAL](https://systemsomicslab.github.io/mtbinfo.github.io/MS-DIAL/tutorial.html#chapter-2).  

Export:  
- **Aligned area peaks** (CSV).  
- **MS/MS spectra** (`.mat` file for SIRIUS).  

Be sure to choose an export directory. You will obtain several files, but the aligned peak areas and the `.mat` spectra file are required for SIRIUS processing.

---

### 2. SIRIUS Structure & CANOPUS Output Files
1. Import the `.mat` file into SIRIUS and create a new project.  
2. After analysis, export results from the **Summaries** tab.  
3. Recommended exports:  
   - `structure_identification.tsv`  
   - `canopus_structure_identification.tsv`  

CANVAS is optimized for SIRIUS export based on the top 1 hit.

---

### 3. Metadata File
- Must be saved as `.csv`.  
- Rules:  
  - First row = column names.  
  - First column = `name_file`.  
  - Sample names must match those from MSDIAL output.  
  - Blank samples must contain `"Blank"` in at least one variable.  

---

## Starting CANVAS

### Loading Data
After launching CANVAS:  
1. Load the four input files from the header section.  
2. For first-time processing, select **“Files are raw”**.  
3. For saved datasets, select **“Load Files”**.  
4. Optionally, use **“Trim raw file”** to remove unwanted rows.  

Large datasets (>50 MB) may take several seconds to load.

---

## Data Processing Steps

1. **Blank Removal**  
   - Identifies samples annotated as blanks.  
   - Averages blank signals across features.  
   - Removes features that are not sufficiently higher than blanks (user-defined ratio, e.g., 0.1 = 10× higher).  

2. **Imputation**  
   - Replaces missing or zero values with small values.  
   - Sampled from a normal distribution between 0 and the minimum observed value.  

3. **Normalization**  
   - By **Total Ion Chromatogram (TIC)**.  
   - Assumes similar injection amounts across samples.  
   - Fast but has limitations depending on experimental design.  

4. **Scaling**  
   - Uses `StandardScaler()` from `sklearn.preprocessing`.  
   - Each feature is centered (mean 0) and scaled (standard deviation 1).  
   - Helps balance extreme values for multivariate analysis.

---

## Filters & Options

### GUI Panels
The interface contains several panels:  
- **Filters**  
- **Display options**  
- **Selection options**  
- **Feature browsing**  

### Display Options
- Visualize data based on **intensity values** or **number of features**.  
- Explore metabolite classes at any hierarchical level from CANOPUS (NPC classification).  

### Selection Options
- Choose which processed dataset to use.  
- Select variables of interest for grouping.  
- Multi-level selection available (default = 1 level).  
- “Select all” to quickly include all variables in a group.

### Filters
Three filter sliders are available:  
1. **Intensity threshold** – keeps only features above a % intensity cutoff (e.g., top 10%).  
2. **SIRIUS score threshold** – removes features with low annotation confidence.  
3. **CANOPUS score threshold** – applies to pathway, class, and subclass.  
   - Features failing threshold for any category are removed.  
   - Recommended to set thresholds relatively low.  

### Select Specific Features
- If compounds are identified in SIRIUS CSI:FingerID, they can be searched by name.  
- Selecting compounds keeps only those features.  
- Multiple compounds can be added.

---

## Data Visualization

### 1. Sunburst Plot
- Displays hierarchical class distribution (pathway → class → subclass).  
- Interactive filtering and exploration supported.  

### 2. Bar Charts
- Show distribution of classes across conditions.  
- Can be based on feature intensity or counts.  

### 3. Boxplots
- Compare intensity distributions for selected features or classes.  

---

## Multivariate Analysis

### PCA (Principal Component Analysis)
- Plots first two components across samples.  
- Right panel shows features contributing most to PC1 and PC2.  
- High-contribution features indicate variance drivers across all samples.  
- MANOVA (Wilks’ Lambda p) provided as a quick significance test.  

### Random Forest (Supervised Learning)
- Classifier identifies features most important for distinguishing groups.  
- Feature importance is based on error reduction across decision trees.  
- Useful for supervised comparisons.  

---

## Exporting Data
- Use **“Export data”** to save processed datasets.  
- If **“Filtered”** is checked → only filtered data are exported.  
- If unchecked → full processed dataset is exported.  
- Exported data are merged with structural annotations for downstream analysis.

---

## Best Practices
- Always quality-check exported SIRIUS results before analysis.  
- Use blank removal and TIC normalization carefully depending on study design.  
- Combine exploratory plots (sunburst, bar chart) with PCA/Random Forest for robust interpretation.  

---

## Citation
If you use CANVAS in your research, please cite:  

> Lehr, F.-X., Paczia, N. **CANVAS: An Interactive Dash Application for Visualization and Analysis of LC-MS Metabolomics Data using the SIRIUS Workflow**. *Year*.
