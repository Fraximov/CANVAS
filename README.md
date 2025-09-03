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
- Two tsv files obtained from the Sirius processing: The structure file from Sirius:CSI:FingerID and the canopus file from CANOPUS.
- One metadata file containing all the variable to considerate.

  ### 1. Integrated area peak file
  The easiest way to start this dash app is to use integrated features extracted with MSDIAL. Diverse tutorials for extracting and integrating LC/MS/MS raw data from DIA or DDA experiments can be found on the github of [MSDIAL] (https://systemsomicslab.github.io/mtbinfo.github.io/MS-DIAL/tutorial.html#chapter-2). 
  Briefly, after the aligment and integration, you should be able to export both the aligned mat file needed for Sirius processing and the list of extracted areas. Click on Export -> Aligment result and you should have the following windows opening:
  <img width="1279" height="908" alt="image" src="https://github.com/user-attachments/assets/6e3a0898-aa6a-40ea-b41a-daf9dd0b7ee6" />
  Be sure to select the spectra with .mat extension for export (MS/MS) <img width="432" height="750" alt="image" src="https://github.com/user-attachments/assets/a158103a-fb59-494b-babb-585ae7e6bc84" />
  Be sure to chose a directory for saving your files. Click export. You should now have several files exported in your directory. The aligned area peaks and the .mat spectra file are the ones we need to keep for the further steps.

   ### 2. Sirius structure and Canopus output files
  To run Sirius for your LC/MS/MS analysis pipeline, you can now import the .mat file generated at the previous step and create a new sirius project. Tutorials and guidelines can be found in the Sirius website for more details. After your analysis is done, you can click "Summaries" and select the export files of interest. CANVAS has been optimized to use Sirius     export based on the top 1 Hit. Save the files in .tsv. Quality check can be done in the Sirius GUI over the different MS2 features to ensure an overall good quality of the data. You should now have "structure_identification.tsv" and "canopus_structure_identification.tsv" saved in your directory:
  <img width="1328" height="778" alt="image" src="https://github.com/user-attachments/assets/cb142b14-3428-4ee2-9b73-9489e68c5f2f" />


   ### 3. Metadata
  The last input file is the metadata, created by the user. The file needs to be saved in .csv and needs to follow these formatting requirements:
  - The first row of the file is the column names. The first column name should always be named "name_file".
  - The first column should contain the list of the sample names. The names should be the same as the names of the files loaded in MSDIAL (Tip: you can open the aligned area peaks file from MSDIAL and copy the names directly there).
  - Each other column names contain the variable names of the experiment.
  - For blank samples, some variable should contain the name "Blank" so they can be identified by CANVAS and be automatically used for blank substraction.
  <img width="588" height="348" alt="image" src="https://github.com/user-attachments/assets/09673fe1-95fe-4379-94bf-29c8119d8228" />

## Starting CANVAS
 ### 1. Loading the data
Once you open CANVAS, you can load the four different input files in the header section. When correctly loaded, the icons below the loading area should be updated.
<img width="2376" height="312" alt="image" src="https://github.com/user-attachments/assets/58078b72-89e5-40ab-acfa-8203b59ebad7" />
For a first-time analysis of the data, you will need to select "Files are raw". If the processing has alreaady been performed once before and the data saved, you can directly processed to "Load Files".
<img width="2298" height="606" alt="image" src="https://github.com/user-attachments/assets/b17f212e-fba4-4340-83d5-73ffc39cbf52" />
You will need to select "Trim raw file". This option enables the removal of the first few lines of the area peak files from MSDIAL before processing. You will need to write a name commun pattern identifier that is contain in your file name list. Once you click "Load Files", you should see a confirmation of the loaded data with a rectangular blue button. If the dataset is huge (>50mb), this step can takes up from several seconds to a couple of minutes.

### 2. Processing the data
After the loading of the raw data, you have the possibility to process the data through different steps:
#### 1. Blank removal
identify the samples annotated with 'Blank' in the metadata. The blanked samples are then averaged over each feature. Each feature is compared to the blank feature. If the feature is below the indicated ratio by the user (slider), it is removed from the list of analyzed features. A typical value is 0.1, i.e. all features that are not at least 10 times higher than the background will be removed.
#### 2. Imputation
Data can then be imputed. Briefly, missing feature values and equal to 0 will be replaced by sampling a normal distribution set between 0 and the minimum value of the data.
#### 3. Normalization
The normalization step consists of normalizing each feature of the dataset by the TIC (Total Ion Chromatograme) of each sample. TIC normalization assumes a set of assumption (such as equal distibution of feature intensities over all samples) that the author invites the user to verifiy before applying this step.
#### 3. Scaling
For data export and facilitating the visualization with certain tools, it may be necessary to scale the data to minimize the impact of extreme values. For that, the data are transformed with log2 and are then centered around 0.

