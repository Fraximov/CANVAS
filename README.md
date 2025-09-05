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

---
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
---
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
The normalization step consists of normalizing the features of each sample by the TIC (Total Ion Chromatograme) of the sample. TIC normalization is an easy normalization and inexpensive computationally, but assumes that the amount injected across all samples is consistent. It also assumes all metabolites are stable between samples, which have obvious limitations according to the experimental design and background.
#### 4. Scaling
In order to facilitethe visualization with certain tools or specific analysis, it may be necessary to scale the data to minimize the impact of extreme values. For that, the data are transformed with the StandardScaler() method from sklearn.preprocessing. Each feature is center-scaled by substracting the mean and diving by the standard deviation of the feature over all samples, resulting of the final data being centered around 0 with a standard deviation of 1.

<img width="2521" height="608" alt="image" src="https://github.com/user-attachments/assets/c3aa179c-0c24-4baa-a658-38ce8f8c2d8a" />


 ---
## Using CANVAS for visualization and data analysis
### 1. GUI interface for data selection 
After loading the data and process them until the step of choice, you can now use the GUI to visualize and analyze your data. The GUI parameters is separated in different pannels: 
- Filter pannels
- Display options
- Selected options
- Browse by specific features
#### 1. Display options
You can chose to visualize the data based on the area intensity of each feature or based on the number of features detected with the intensity treshold (see Filters). The data can be visualized for every level of the NPC classification made by CANOPUS. By default, every hierarchical level is activated to be displayed.
<img width="424" height="163" alt="image" src="https://github.com/user-attachments/assets/345f3854-b57d-48ce-b343-23cea06bee4a" />

#### 2.Selection options 
You can chose the data processed with your method of your choice. Note that you had to processed the data (see previously) to be able to select the corresponding formatted data. 
You can chose two levels of variable parameters. By default, only one level is activated as it is often sufficient for a first overview. Once you selected the parameter of interest, you can refine which variable is considered for the visualization in the selection toolbox below. You can directly select all variables belonging to the chosen parameter(s) by clicking "select all".
<img width="1253" height="384" alt="image" src="https://github.com/user-attachments/assets/e140cc4a-7493-460c-a28a-f8ef69a9c6bc" />
<img width="1250" height="354" alt="image" src="https://github.com/user-attachments/assets/522c13bd-0a88-4f3e-97b4-f6cc546b2af3" />
<img width="1242" height="125" alt="image" src="https://github.com/user-attachments/assets/20f2bc9a-27d7-4282-a140-335ab37807b0" />

#### 3. Filters 
You can filter the dataset with three different filter sliders:
- Intensity thresholding: in percent of the cut-off intensity threshold below which one the features are kept, i.e. if the slider is on 10, it means the data will retain 10% of the most intense features.
- Sirius score threshold: Features possessing lower scores than this treshold will be removed from the analysis. The General Sirius score indicates how confident Sirius is on the molecular formula annotation.
- Canopus score threshold: Features posessing lower scores than this threshold will be removed from the analysis: The Canopus score treshold applies individually to Pathway, classes and subclasses hierarchy. If one of these values is lower than the treshold, the feature is removed entirely. We advice to keep this threshold fairly low.

#### 4. Select specific features
If the feature has been identified in Sirius CSI:Finger ID, you can browse the list of compound names here by searching the name by the entry text. Select the compounds of interests and everything else will be discarded from the dataset. You can add as many compounds as wanted.


### 2. Data visualization
#### 1. Sunburst plot
<img width="2519" height="432" alt="image" src="https://github.com/user-attachments/assets/4434e1fb-19aa-457b-a4d9-527976fe0ffb" />

#### 2. Barplot chart 
<img width="2513" height="406" alt="image" src="https://github.com/user-attachments/assets/fdd64c3c-1461-40b8-8fb6-e789cd2c25c8" />

#### 3. individual boxplots 
<img width="2065" height="657" alt="image" src="https://github.com/user-attachments/assets/10d4c9c3-1448-4d64-a39a-5cbf226c05cf" />


