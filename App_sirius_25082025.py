import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
import plotly.express as px
import time 

from dash import Dash, html, dcc, callback, Input, Output, State, dash_table, ctx, no_update, callback_context
from dash.dash_table import DataTable
from dash import jupyter_dash
from dash.exceptions import PreventUpdate
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score   

from flask_caching import Cache
from uuid import uuid4
import dash_bootstrap_components as dbc
import platform
import math
import base64
import io

import dash_bootstrap_components as dbc
from dash import dcc, html

import chardet  # Optional: for more robust encoding detection if needed
from plotly.colors import sample_colorscale
from sklearn.ensemble import RandomForestClassifier
from statsmodels.multivariate.manova import MANOVA
from plotly.subplots import make_subplots


# ---- Helpers to store/fetch heavy DataFrames ----
def cache_put(df, stage_key):
    """Stage key is a short name like 'raw', 'blanked', etc."""
    # Optionally downcast here if you want one centralized place
    # df = downcast_numeric(df)
    cache.set(stage_key, df)
    return stage_key

def cache_get(stage_key):
    if not stage_key:
        return None
    return cache.get(stage_key)



jupyter_dash.default_mode="external"


# In[17]:


external_stylesheets = [dbc.themes.FLATLY]

app = Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)

# Create the cache object first
cache = Cache()


# Then initialize it with the underlying Flask server
cache.init_app(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",   # or "simple" for in-memory
        "CACHE_DIR": "dash_cache",    # required for filesystem
        "threshold": 500,             # max entries
        "default_timeout": 24*3600,   # 1 day
    }
)


selection_card = dbc.Card(
    dbc.CardBody([
        html.H5("Selection Options", className="card-title"),

        dbc.Row([
            dbc.Label("Select Data Version"),
            dcc.Dropdown(
                id='data-version-dropdown',
                options=[
                    {'label': 'Raw (Peak Areas)', 'value': 'raw'},
                    {'label': 'Blanked', 'value': 'blanked'},
                    {'label': 'Imputed', 'value': 'imputed'},
                    {'label': 'Normalized', 'value': 'normalized'},
                    {'label': 'Scaled', 'value': 'scaled'},
                ],
                value='raw',  # default selection
                clearable=False,
                
            ),
            
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Label("Select parameter(s)"),
            dcc.Dropdown(
                id='parameter-dropdown',
                options=[],
                value=None,
                clearable=False,
            ),

            dcc.Dropdown(
                id='parameter-dropdown2',
                options=[],   # filled dynamically or same as first
                multi=False,
                placeholder='Select second grouping parameter (optional)'
            ),
                
        ], className="mb-3"),

        dbc.Label("Select information for plotting:"),        
        dbc.Row([
            dbc.Col(
                [
                    
                    dcc.Dropdown(
                        id='information-dropdown',
                        options=[],
                        value=None,
                        multi=True
                    ),
                ],
                width=8
            ),
            dbc.Col(
                dbc.Button("Select All", id="select-all-btn", color="primary"),
                width="auto"
            ),
            dbc.Col(
                [
                    
                    dcc.Dropdown(
                        id='information-dropdown2',
                        options=[],
                        value=None,
                        multi=True
                    ),
                ],
                width=8
            ),

             dbc.Col(
                dbc.Button("Select All", id="select-all-btn2", color="primary"),
                width="auto"
            ),
            
        ]),
        
    ]),
    className="mb-4 g-3",
)
# --- First card: Buttons and Checkboxes
controls_card = dbc.Card(
    dbc.CardBody([
        html.H5("Display Options", className="card-title"),

        dbc.ButtonGroup(
            [
                dbc.Button("Intensity", id="radio-intensity", color="primary", outline=True, active=True, n_clicks=0, size="sm", className="mx-1"),
                dbc.Button("Count", id="radio-count", color="primary", outline=True, active=False, n_clicks=0, size="sm", className="mx-1"),
            ],
            className="mb-4 g-3",
            id="radio-style-buttons",
        ),

        html.H6("Group By", className="card-subtitle mb-2 text-muted"),

        dbc.Checklist(
            options=[
                {"label": "Pathway", "value": "NPC#pathway"},
                {"label": "Superclass", "value": "NPC#superclass"},
                {"label": "Class", "value": "NPC#class"},
            ],
            value=[ "NPC#pathway", "NPC#superclass","NPC#class"],  # default checked
            id="checkbox-levels",
            inline=True,
            switch=True,
        ),
 
    ]),
    className="mb-4 g-3",
    #style={"width": "22rem", "minWidth": "300px"},
)

# --- Second card: Sliders
sliders_card = dbc.Card(
    dbc.CardBody([
        html.H5("Filters", className="card-title"),

        dbc.Label("Threshold:", className="mt-2"),
        dcc.Slider(
            id='threshold-slider',
            min=0, max=1, step=0.01, value=0.1, marks=None,
            tooltip={"placement": "bottom", "always_visible": True},
        ),

        dbc.Label("Min Probability:", className="mt-4"),
        dcc.Slider(
            id='probability-slider',
            min=0, max=1, step=0.05, value=0.3, marks=None,
            tooltip={"placement": "bottom", "always_visible": True},
        ),

        dbc.Label("Min Sirius Score:", className="mt-4"),
        dcc.Slider(
            id='sirius-slider',
            min=0, max=1, step=0.05, value=0.5, marks=None,
            tooltip={"placement": "bottom", "always_visible": True},
        ),
    ]),
     className="mb-4 g-3",
    #style={"width": "25rem", "minWidth": "320px"},a
)


# --- Third card: Toat information

toast_card = dbc.Card(
    dbc.Toast(
        id="data-summary-toast",
        header="Data Summary",
        icon="info",
        dismissable=True,
        is_open=False  # closes automatically after 8s
    )

)

# --- Fourth card: Specific compound selector

compound_selection_card = dbc.Card(
        dbc.CardBody([
            dbc.Checkbox(
                id='browse-compounds-checkbox',
                label="Browse by specific items"
            ),
            html.Div(  # this div wraps the searchable UI and starts hidden
                [
                    dbc.Label("Search compound name"),
                    dcc.Input(
                        id='compound-search-input', 
                        type='text',
                        placeholder='Type part of compound name...'
                    ),
                    dcc.Dropdown(
                        id='compound_dropdown',
                        options=[],
                        value=[],
                        clearable=False,
                        multi=True,
                    )
                ],
                id="compound-search-controls",
                style={"display": "none"}  # hidden by default
            )
        ])
    )
 



app.layout = dbc.Container([


    dcc.Store(id='store-peak-areas'),
    dcc.Store(id='store-metadata'),
    dcc.Store(id='store-canopus'),
    dcc.Store(id="radio-mode-store", data="Intensity"),
    dcc.Store(id='store-blanked'),       # after blank subtraction
    dcc.Store(id='store-imputed'),       # after imputation
    dcc.Store(id='store-normalized'),    # after normalization
    dcc.Store(id='store-scaled'),        # after scaling
    dcc.Store(id="store-current-step"),
    dcc.Store(id='store-compound-names'),
    
    dbc.Row([
        html.H2("Sirius-Canopus visualization of LC-MS data")
    ]),
    
    dbc.Button("Show/Hide Upload Panel", id="toggle-upload-panel", className="mb-2", color="primary"),
    
    dbc.Collapse([
        dbc.Row([
            dbc.Col([
                html.H5("Upload Peak Areas"),
                dcc.Upload(
                    id='upload-peak-areas',
                    children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                    multiple=False,
                    accept='.csv',
                    style={'border': '1px dashed #aaa', 'padding': '10px'}
                ),
            ]),
            dbc.Col([
                html.H5("Upload Metadata"),
                dcc.Upload(
                    id='upload-metadata',
                    children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                    multiple=False,
                    accept='.csv',
                    style={'border': '1px dashed #aaa', 'padding': '10px'}
                ),
            ]),
            dbc.Col([
                html.H5("Upload CANOPUS"),
                dcc.Upload(
                    id='upload-canopus',
                    children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                    multiple=False,
                    accept= '.csv,.tsv',
                    style={'border': '1px dashed #aaa', 'padding': '10px'}
                ),
            ]),
            dbc.Col([
                html.H5("Upload SIRIUS structure"),
                dcc.Upload(
                    id='upload-structure',
                    children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                    multiple=False,
                    accept= '.csv,.tsv',
                    style={'border': '1px dashed #aaa', 'padding': '10px'}
                ),
            ]),            
            
            dbc.Col([
                html.Div(id='file-status'),
                ]),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Div(id='file-status-drop', style={'marginTop': '15px'})
                    ])
                ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Checkbox(id='is-raw-checkbox', label='Files are raw (need processing)', value=False)
            ]),]),
                dbc.Collapse(
                id="raw-settings-collapse",
                is_open=False,
                children=[
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Checklist(options=[{"label": "Trim raw file", "value": "check_trim"}],
                                                               value=["check_trim"],  # default checked
                                                                id="checkbox-trim",
                                                                inline=True,
                                                                switch=True),
                            html.Label("Sample name pattern:"),
                            dbc.Input(id="sample-pattern-input", placeholder="e.g., sample_*_rep*", type="text"),


                            dbc.Row([
                                dbc.Col([
                                        
                            
                                    dbc.Label("Blank Threshold:", className="mt-2"),
                                    dcc.Slider(
                                            id='blank-slider',
                                            min=0, max=1, step=0.01, value=0.1, marks=None,
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        
                                        )], width=3
                                       ),
                                
                                 dbc.Col(
                                    dbc.ButtonGroup([
                                        dbc.Button("Blanked", id="btn-blanked", color="primary", outline=False, className="me-1"),
                                        dbc.Button("Imputed", id="btn-imputed", color="success", outline=False, className="me-1", disabled=True),
                                        dbc.Button("Normalized", id="btn-normalized", color="info", outline=False, className="me-1", disabled=True),
                                        dbc.Button("Scaled", id="btn-scaled", color="warning", outline=False, className="me-1",disabled=True),
                                    ],
                                    size="lg"),
                                    width=9,
                                    className="d-flex align-items-center justify-content-center"
                                )
                            ])
                            

                            
                        ])
                    )
                ]
            ),
        
        
        dbc.Row([
            dbc.Col(
            dbc.Button("Load Files", id="load-files-button", color="primary"),
            width="auto"
            ),
            dbc.Col(
            dcc.Loading(
            html.Div("", id="loading-display-output"),
            id="loading-display"
        ),   
            ),
            dbc.Col(
            html.Div(id="upload-status"),
            width=True  # Automatically takes remaining space
        ),
            dbc.Col(
            html.Div(id="upload-status-blank"),
            width=True  # Automatically takes remaining space
        ),
            dbc.Col(
            html.Div(id="upload-status-imputation"),
            width=True  # Automatically takes remaining space
        ),
            dbc.Col(
            html.Div(id="upload-status-normalization"),
            width=True  # Automatically takes remaining space
        ),
            dbc.Col(
            html.Div(id="upload-status-scaling"),
            width=True  # Automatically takes remaining space
        ),
        ], align="center", className="mb-3")
    ], id="upload-panel", is_open=False),




    

    
    

    dbc.Row([
        dbc.Col([sliders_card,
                 toast_card,
                compound_selection_card]),
        dbc.Col([controls_card,
               selection_card]),
        
    ], className="mb-4 4 mt-4"),  # g-3 adds small gap between cols
    
 
    dbc.Tabs(
        id='tabs-final-plot',
        active_tab='sunburst',
        children=[
            dbc.Tab(label='Sunburst Plot', tab_id='sunburst'),
            dbc.Tab(label='Barplot', tab_id='barplot'),
            dbc.Tab(label='PCA', tab_id = 'PCA'),
            dbc.Tab(label='line_plot', tab_id = 'line_plot'),
            dbc.Tab(label='Random Forest', tab_id='rf'),
    ]),

    dbc.Spinner(
        dcc.Graph(id='final-graph',
                 config={
        "toImageButtonOptions": {
            "format": "svg",  # one of png, svg, jpeg, webp
            "filename": "my_plot",
            "height": 600,
            "width": 800,
            "scale": 1
        }}),
        color="primary",  # 'primary', 'secondary', 'success', etc.
        type="border",    # or 'grow'
        fullscreen=False,  # You can set to True for full-page overlay
        size="md",        # 'sm', 'md', 'lg'
        spinner_style={"width": "3rem", "height": "3rem"}  # optional custom style
    ),
    
    dbc.Row([
        html.H4("Data Preview"),
        dcc.Tabs(id="preview-tabs", value='peak', children=[
        dcc.Tab(label='Peak Areas', value='peak'),
        dcc.Tab(label='Metadata', value='meta'),
        dcc.Tab(label='CANOPUS', value='cano'),
        ]),
        dash_table.DataTable(id='data-preview-table',
                     style_table={'overflowX': 'auto'},
                     page_size=5),
            ]),
    dbc.Row([
    dbc.Button("Download CSV", id="download-btn", color="primary", className="mb-2"),
    dcc.Download(id="download-dataframe-csv"),          
    ]),
    
], fluid=True)


# In[18]:


@callback(
    Output("data-summary-toast", "children"),
    Output("data-summary-toast", "is_open"),
    Output('final-graph', 'figure'),
    Input('tabs-final-plot', 'active_tab'),
    Input('parameter-dropdown', 'value'),
    Input('parameter-dropdown2', 'value'),  
    Input('information-dropdown', 'value'),
    Input('information-dropdown2', 'value'),
    Input('threshold-slider', 'value'),
    Input('probability-slider', 'value'),
    Input('sirius-slider', 'value'),
    Input('radio-mode-store', 'data'),
    Input('checkbox-levels', 'value'),
    Input("store-current-step", "data"),    # <-- key, not big JSON
    Input("compound_dropdown", "value"),
    State('store-metadata', 'data'),
    State('store-canopus', 'data'),
)
def update_sunburst(tab_choice, selected_param, second_param, selected_locations,
                    selected_samples2, threshold, filter_prob, filter_sirius,
                    radio_choice, checkbox_levels, current_step_key, selected_compounds,
                    metadata_dict, canopus_dict):

    if not selected_locations or not metadata_dict or not canopus_dict or not current_step_key:
        return no_update, False, go.Figure()

    cleaned_data = cache_get(current_step_key)  # <-- fetch from cache
    if cleaned_data is None:
        return no_update, False, go.Figure()

    cleaned_data = convert_commas_to_floats(cleaned_data)
    if not cleaned_data.empty and cleaned_data.shape[1] > 0:
        cleaned_data.set_index(cleaned_data.columns[0], inplace=True)
    else:
        return no_update, False, go.Figure()

    if selected_compounds:
        if not isinstance(selected_compounds, list):
            selected_compounds = [selected_compounds]
    else:
        selected_compounds = None

    metadata = pd.DataFrame(metadata_dict)
    metadata.set_index(metadata.columns[0], inplace=True)

    ft_sirius_NPC = pd.DataFrame(canopus_dict)
    ft_sirius_NPC = convert_commas_to_floats(ft_sirius_NPC)
    ft_sirius_NPC.set_index(ft_sirius_NPC.columns[0], inplace=True)

    cleaned_data.index.name = 'filename'
    metadata.index.name = 'filename'
    ft_sirius_NPC.index.name = 'compound_name'

    if second_param and selected_samples2:
        if not isinstance(selected_samples2, list):
            selected_samples2 = [selected_samples2]
        metadata = metadata[metadata[second_param].isin(selected_samples2)]

    filtered_df = filter_merged_dataset(
        cleaned_data=cleaned_data,
        metadata=metadata.reset_index(),
        ft_sirius=ft_sirius_NPC.reset_index(),
        attribute_name=selected_param,
        sample_locations=selected_locations,
        threshold=threshold,
        filter_class=None,
        filter_prob=filter_prob,
        filter_sirius=filter_sirius,
        selected_compounds=selected_compounds 
    )

    n_features = filtered_df.shape[0] + 1
    n_samples = filtered_df.shape[1] 
    n_pathways = filtered_df['NPC#pathway'].nunique()
    n_superclasses = filtered_df['NPC#superclass'].nunique()
    n_classes = filtered_df['NPC#class'].nunique()

    filtered_df.index.name = 'filename'
    
    summary = dbc.Row([
        dbc.Col([
            html.P(f"Retained features: {n_features}", className="mb-1"),
            html.P(f"Retained samples: {n_samples}", className="mb-1"),
        ], width=7),
        dbc.Col([
            html.P(f"Retained superclasses: {n_superclasses}", className="mb-1"),
            html.P(f"Retained classes: {n_classes}", className="mb-1"),
            html.P(f"Retained pathways: {n_pathways}", className="mb-1"),
        ], width=7),
    ])

    if not isinstance(selected_locations, list):
        selected_locations = [selected_locations]

    # your plot branch stays the same...
    # (sunburst / barplot / PCA / line_plot / RT_mz / rf)
    # just keep passing the DataFrames as you already do

    # ...
    # return summary, True, fig

    if tab_choice == 'sunburst':
        if radio_choice == 'Intensity':
         
            fig = process_and_plot_intensity_NPC(
                cleaned_data=cleaned_data,
                metadata=metadata.reset_index(),
                ft_sirius=ft_sirius_NPC.reset_index(),
                attribute_name=selected_param,
                sample_locations= selected_locations,
                threshold=threshold,
                node_color_map=node_color_map,
                filter_class=None,  # You can later wire this up from another input
                filter_prob=filter_prob,
                filter_sirius=filter_sirius,
                selected_compounds = selected_compounds,
            )
        elif radio_choice == 'Count':
            
            fig = process_and_plot_NPC_count(
                cleaned_data=cleaned_data,
                metadata=metadata.reset_index(),
                ft_sirius=ft_sirius_NPC.reset_index(),
                attribute_name=selected_param,
                sample_locations=selected_locations,
                threshold=threshold,
                node_color_map=node_color_map,
                filter_class=None,  # You can later wire this up from another input
                filter_prob=filter_prob,
                filter_sirius=filter_sirius,
                selected_compounds = selected_compounds,
            )

        else:
            fig = go.Figure()
        
    elif tab_choice == 'barplot':
        fig = process_and_plot_barplot_NPC(
            cleaned_data=cleaned_data,
            metadata=metadata.reset_index(),
            ft_sirius=ft_sirius_NPC.reset_index(),
            attribute_name=selected_param,
            sample_locations=selected_locations,
            threshold=threshold,
            node_color_map=node_color_map,
            filter_class=None,
            filter_prob=filter_prob,
            filter_sirius=filter_sirius,
            group_cols = checkbox_levels,
            type_plot = radio_choice,
            selected_compounds = selected_compounds,
        )
        
    elif tab_choice == 'PCA':
        fig = process_and_plot_pca(
            cleaned_data=cleaned_data,
            metadata=metadata.reset_index(),
            ft_sirius=ft_sirius_NPC.reset_index(),
            attribute_name=selected_param,
            sample_locations=selected_locations,
            threshold=threshold,
            filter_class=None,
            filter_prob=filter_prob,
            filter_sirius=filter_sirius, 
            selected_compounds = selected_compounds,
        )   
        
    elif tab_choice == 'line_plot':
        fig = process_and_plot_lineplot_NPC(
            cleaned_data=cleaned_data,
            metadata=metadata.reset_index(),
            ft_sirius=ft_sirius_NPC.reset_index(),
            attribute_name=selected_param,
            sample_locations=selected_locations,
            threshold=threshold,
            node_color_map=node_color_map,
            filter_class=None,
            filter_prob=filter_prob,
            filter_sirius=filter_sirius,
            group_cols = checkbox_levels,
            type_plot = radio_choice,
            selected_compounds = selected_compounds,               
        )
    elif tab_choice == 'RT_mz':
        fig = scatter_rt_mz(
            cleaned_data=cleaned_data,
            metadata=metadata.reset_index(),
            ft_sirius=ft_sirius_NPC.reset_index(),
            attribute_name=selected_param,
            sample_locations=selected_locations,
            threshold=threshold,
            node_color_map=node_color_map,
            filter_class=None,
            filter_prob=filter_prob,
            filter_sirius=filter_sirius,
            group_cols = checkbox_levels,
            type_plot = radio_choice,
            selected_compounds = selected_compounds,
        )

    
    elif tab_choice == "rf":
        fig = process_and_plot_rf(
            cleaned_data=cleaned_data,
            metadata=metadata,
            ft_sirius=ft_sirius_NPC,
            group_col=selected_param,
            sample_locations=selected_locations,
            threshold=threshold,
            filter_class=checkbox_levels,
            filter_prob=filter_prob,
            filter_sirius=filter_sirius,
            type_plot=radio_choice
        )
        return summary, True, fig

         
    else:
        fig = go.Figure()
        
    return summary, True, fig


@callback(
    Output("loading-display-output", "children"),
    Input("load-files-button", "n_clicks"),
)
def load_output(n):
    if n:
        time.sleep(2)
        return f"Data updated {n} times."
    return no_update



@callback(
    Output("radio-mode-store", "data"),
    Output("radio-intensity", "active"),
    Output("radio-count", "active"),
    Input("radio-intensity", "n_clicks"),
    Input("radio-count", "n_clicks"),
    prevent_initial_call=True
)
def toggle_radio_style(n_int, n_count):
    if not ctx.triggered:
        return dash.no_update
    clicked = ctx.triggered[0]["prop_id"].split(".")[0]

    if clicked == "radio-intensity":
        return "Intensity", True, False
    elif clicked == "radio-count":
        return "Count", False, True

    return dash.no_update
    
@callback(
    Output('information-dropdown', 'options'),
    Output('information-dropdown', 'value'),
    Input('parameter-dropdown', 'value'),
    Input('select-all-btn', 'n_clicks'),
    State('store-metadata', 'data'),
    State('information-dropdown', 'value'),
    prevent_initial_call=True
)
def update_information_dropdown(selected_param, n_clicks, metadata_dic, current_selection):
    if metadata_dic is None:
        return [], None 
    
    metadata = pd.DataFrame(metadata_dic)

    if selected_param is None or selected_param not in metadata.columns:
        return [], None

    unique_vals = metadata[selected_param].dropna().unique()
    options = [{"label": val, "value": val} for val in unique_vals]
    all_values = list(unique_vals)

    # Use callback context to detect which input triggered the callback
    triggered_id = ctx.triggered_id

    if triggered_id == 'parameter-dropdown':
        # Parameter changed: return new options and a default value (first one selected)
        default_value = [all_values[0]] if all_values else []
        return options, default_value

    elif triggered_id == 'select-all-btn':
        # Button clicked: toggle all vs none
        if set(current_selection or []) == set(all_values):
            return options, []  # Deselect all
        else:
            return options, all_values  # Select all

    return options, current_selection

@callback(
    Output('information-dropdown2', 'options'),
    Output('information-dropdown2', 'value'),
    Input('parameter-dropdown2', 'value'),
    Input('select-all-btn2', 'n_clicks'),
    State('store-metadata', 'data'),
    State('information-dropdown2', 'value'),
    prevent_initial_call=True
)
def update_information_dropdown(selected_param, n_clicks, metadata_dic, current_selection):
    if metadata_dic is None:
        return [], None 
    
    metadata = pd.DataFrame(metadata_dic)

    if selected_param is None or selected_param not in metadata.columns:
        return [], None

    unique_vals = metadata[selected_param].dropna().unique()
    options = [{"label": val, "value": val} for val in unique_vals]
    all_values = list(unique_vals)

    # Use callback context to detect which input triggered the callback
    triggered_id = ctx.triggered_id

    if triggered_id == 'parameter-dropdown':
        # Parameter changed: return new options and a default value (first one selected)
        default_value = [all_values[0]] if all_values else []
        return options, default_value

    elif triggered_id == 'select-all-btn2':
        # Button clicked: toggle all vs none
        if set(current_selection or []) == set(all_values):
            return options, []  # Deselect all
        else:
            return options, all_values  # Select all

    return options, current_selection


@callback(
    Output('file-status-drop', 'children'),
    Input('upload-peak-areas', 'filename'),
    Input('upload-metadata', 'filename'),
    Input('upload-canopus', 'filename'),
    Input('upload-structure','filename'),
)
def show_uploaded_filenames(peak_name, meta_name, canopus_name,structure_name):
    messages = []

    if peak_name:
        messages.append(f"📄 Peak Areas file: {peak_name}")
    else:
        messages.append("❌ Peak Areas file not uploaded")

    if meta_name:
        messages.append(f"📄 Metadata file: {meta_name}")
    else:
        messages.append("❌ Metadata file not uploaded")

    if canopus_name:
        messages.append(f"📄 Canopus file: {canopus_name}")
    else:
        messages.append("❌ Canopus file not uploaded")

    if structure_name:
        messages.append(f"📄 Sirius structure file: {structure_name}")
    else:
        messages.append("❌ Structure file not uploaded")

    return html.Ul([html.Li(msg) for msg in messages])

@callback(
    Output('file-status', 'children'),
    Input('store-peak-areas', 'data'),
    Input('store-metadata', 'data'),
    Input('store-canopus', 'data'),
)


def show_file_status(peak_data, meta_data, canopus_data):
    messages = []
    if peak_data:
        messages.append("✅ Peak Areas loaded")
    else:
        messages.append("❌ Peak Areas missing")

    if meta_data:
        messages.append("✅ Metadata loaded")
    else:
        messages.append("❌ Metadata missing")

    if canopus_data:
        messages.append("✅ Canopus analysis loaded")
    else:
        messages.append("❌ Canopus analysis missing")

    return html.Ul([html.Li(msg) for msg in messages]) 


# Toggle collapse
@callback(
    Output("upload-panel", "is_open"),
    Input("toggle-upload-panel", "n_clicks"),
    State("upload-panel", "is_open"),
    prevent_initial_call=True
)


def toggle_collapse(n_clicks, is_open):
    return not is_open

@callback(
    Output("raw-settings-collapse", "is_open"),
    Input("is-raw-checkbox", "value"),
    State("raw-settings-collapse", "is_open"),
)
def toggle_collapse(raw_toggle_checked, is_open):
    if raw_toggle_checked:
        return True
    return False

from dash import callback, Output, Input, State, ctx, no_update
import pandas as pd

@callback(
    Output('data-preview-table', 'data'),
    Output('data-preview-table', 'columns'),
    Input('preview-tabs', 'value'),
    Input("store-current-step", "data"),
    State('store-metadata', 'data'),
    State('store-canopus', 'data'),
)
def update_data_preview(tab_selected, current_step_key, meta_data, cano_data):
    if tab_selected == 'peak':
        df = cache_get(current_step_key)
        if df is None:
            return [], []
        df = df.head(10)
    elif tab_selected == 'meta':
        if not meta_data:
            return [], []
        df = pd.DataFrame(meta_data).head(10)
    elif tab_selected == 'cano':
        if not cano_data:
            return [], []
        df = pd.DataFrame(cano_data).head(10)
    else:
        return [], []

    columns = [{"name": i, "id": i} for i in df.columns]
    return df.to_dict('records'), columns


# Enable 'Impute' after 'Blank Subtraction'
@app.callback(
    Output('btn-imputed', 'disabled'),
    Input('btn-blanked', 'n_clicks'),
)
def enable_impute(n_clicks_blank):
    if n_clicks_blank is None:
        return True  # Keep the button disabled
    return n_clicks_blank <= 0  # Disable if not clicked yet


# Enable 'Normalization' after 'Impute'
@app.callback(
    Output('btn-normalized', 'disabled'),
    Output('btn-scaled', 'disabled'),
    Input('btn-imputed', 'n_clicks'),
)
def enable_impute(n_clicks_blank):
    if n_clicks_blank is None:
        return True, True  # Keep the button disabled
    return n_clicks_blank <= 0,  n_clicks_blank <= 0 # Disable if not clicked yet

@app.callback(
    Output("upload-status", "children"),
    Output('store-peak-areas', 'data'),   # now a KEY like "raw"
    Output('store-canopus', 'data'),
    Output('store-metadata', 'data'),
    Output('parameter-dropdown', 'options'),
    Output('parameter-dropdown2', 'options'),
    Output('parameter-dropdown', 'value'),
    Output('parameter-dropdown2', 'value'),
    Input("load-files-button", "n_clicks"),
    State("upload-peak-areas", "contents"),
    State("upload-metadata", "contents"),
    State("upload-canopus", "contents"),
    State("upload-structure", "contents"),
    State("is-raw-checkbox", "value"),
    State("sample-pattern-input", "value"),
    State("checkbox-trim", "value"),
    prevent_initial_call=True
)
def handle_file_upload(n_clicks, peak_contents, metadata_contents, canopus_contents, structure_contents,
                       is_raw, sample_pattern, checkbox_trim):
    if not all([peak_contents, metadata_contents, canopus_contents]):
        return dbc.Alert("Please upload all required files.", color="warning"), None, None, None, [], [], None, None

    if not sample_pattern:
        return dbc.Alert("Please enter a sample name pattern.", color="danger"), None, None, None, [], [], None, None

    if is_raw:
        pattern = sample_pattern
        is_trim = "check_trim" in checkbox_trim
        df1 = parse_contents(peak_contents, trim=is_trim)
        df2 = parse_contents(canopus_contents)
        df3 = parse_contents(metadata_contents)
        df4 = parse_contents(structure_contents)

        # Your pipeline
        df1_p, df2_p = processing_raw_files(df1, df3, df2, df4, pattern)

        # Downcast
        df1_p = downcast_numeric(df1_p)
        df2_p = downcast_numeric(df2_p)
        df3   = downcast_numeric(df3)

        # Put heavy frames in cache
        raw_key = cache_put(df1_p, "raw")

        # Keep metadata/canopus in Store
        df3_dict = df3.to_dict("records")
        cano_dict = df2_p.to_dict("records")

        options = [{"label": col, "value": col} for col in df3.columns]
        return (
            dbc.Alert("Raw files uploaded and processed.", color="info"),
            raw_key,                # store-peak-areas holds "raw"
            cano_dict,
            df3_dict,
            options, options, df3.columns[1], df3.columns[1]
        )
    else:
        df1 = parse_contents(peak_contents)
        df2 = parse_contents(canopus_contents)
        df3 = parse_contents(metadata_contents)

        # Downcast
        df1 = downcast_numeric(df1)
        df2 = downcast_numeric(df2)
        df3 = downcast_numeric(df3)

        # Cache raw
        raw_key = cache_put(df1, "raw")

        options = [{"label": col, "value": col} for col in df3.columns]
        return (
            dbc.Alert("Processed files uploaded.", color="success"),
            raw_key,                 # store-peak-areas holds "raw"
            df2.to_dict("records"),
            df3.to_dict("records"),
            options, options, df3.columns[1], df3.columns[1]
        )


@app.callback(
    Output('store-blanked', 'data'),                 # now "blanked"
    Output('upload-status-blank', 'children'),
    Input('btn-blanked', 'n_clicks'),
    State('store-peak-areas', 'data'),               # "raw"
    State('store-metadata', 'data'),
    prevent_initial_call=True
)
def apply_blank(n_clicks, raw_key, meta_data):
    if not raw_key or not meta_data:
        return no_update, dbc.Alert("Missing input for blank subtraction.", color="danger")

    ft = cache_get(raw_key)
    if ft is None:
        return no_update, dbc.Alert("Cached RAW data not found.", color="danger")

    md = pd.DataFrame(meta_data)
    ft = convert_commas_to_floats(ft).set_index(ft.columns[0])
    md = convert_commas_to_floats(md).set_index(md.columns[0])
    try:
        cleaned_df, _ = blank_processing(ft, md)
        cleaned_df = downcast_numeric(cleaned_df)
        blanked_key = cache_put(cleaned_df, "blanked")
        return blanked_key, dbc.Alert("Blank subtraction complete.", color="success")
    except Exception as e:
        return no_update, dbc.Alert(f"Blank subtraction failed: {e}", color="danger")


@app.callback(
    Output('store-imputed', 'data'),                 # "imputed"
    Output('upload-status-imputation', 'children'),
    Input('btn-imputed', 'n_clicks'),
    State('store-blanked', 'data'),                  # "blanked"
    prevent_initial_call=True
)
def apply_imputation(n_clicks, blanked_key):
    if not blanked_key:
        return no_update, dbc.Alert("No data to impute.", color="danger")

    df = cache_get(blanked_key)
    if df is None:
        return no_update, dbc.Alert("Cached BLANKED data not found.", color="danger")

    try:
        imputed_df = imputation(df)
        imputed_df = downcast_numeric(imputed_df)
        imputed_key = cache_put(imputed_df, "imputed")
        return imputed_key, dbc.Alert("Imputation complete.", color="success")
    except Exception as e:
        return no_update, dbc.Alert(f"Imputation failed: {e}", color="danger")


@app.callback(
    Output('store-normalized', 'data'),              # "normalized"
    Output('upload-status-normalization', 'children'),
    Input('btn-normalized', 'n_clicks'),
    State('store-imputed', 'data'),                  # "imputed"
    prevent_initial_call=True
)
def apply_normalization(n_clicks, imputed_key):
    if not imputed_key:
        return no_update, dbc.Alert("No data to normalize.", color="danger")

    df = cache_get(imputed_key)
    if df is None:
        return no_update, dbc.Alert("Cached IMPUTED data not found.", color="danger")

    try:
        normalized_df = normalization(df)
        normalized_df = downcast_numeric(normalized_df)
        normalized_key = cache_put(normalized_df, "normalized")
        return normalized_key, dbc.Alert("Normalization complete.", color="success")
    except Exception as e:
        return no_update, dbc.Alert(f"Normalization failed: {e}", color="danger")


@app.callback(
    Output('store-scaled', 'data'),                  # "scaled"
    Output('upload-status-scaling', 'children'),
    Input('btn-scaled', 'n_clicks'),
    State('store-imputed', 'data'),                  # "imputed" (your pipeline uses imputed -> scaled)
    prevent_initial_call=True
)
def apply_scaling(n_clicks, imputed_key):
    if not imputed_key:
        return no_update, dbc.Alert("No data to scale.", color="danger")

    df = cache_get(imputed_key)
    if df is None:
        return no_update, dbc.Alert("Cached IMPUTED data not found.", color="danger")

    try:
        scaled_df = scaling(df)
        scaled_df = downcast_numeric(scaled_df)
        scaled_key = cache_put(scaled_df, "scaled")
        return scaled_key, dbc.Alert("Scaling complete.", color="success")
    except Exception as e:
        return no_update, dbc.Alert(f"Scaling failed: {e}", color="danger")

@callback(
    Output('store-current-step', 'data'),  # e.g. "blanked"
    Input('data-version-dropdown', 'value'),
    State('store-peak-areas', 'data'),
    State('store-blanked', 'data'),
    State('store-imputed', 'data'),
    State('store-normalized', 'data'),
    State('store-scaled', 'data'),
    prevent_initial_call=True
)
def update_current_step(selected_version, raw_key, blanked_key, imputed_key, normalized_key, scaled_key):
    mapping = {
        'raw': raw_key,
        'blanked': blanked_key,
        'imputed': imputed_key,
        'normalized': normalized_key,
        'scaled': scaled_key
    }
    key = mapping.get(selected_version)
    if key:
        return key
    elif raw_key:
        return raw_key
    else:
        return no_update


@callback(
    Output("download-dataframe-csv", "data"),
    Input("download-btn", "n_clicks"),
    State("store-current-step", "data"),
    prevent_initial_call=True,
)
def download_csv(n_clicks, current_step_key):
    df = cache_get(current_step_key)
    if df is None:
        return no_update

    df = convert_commas_to_floats(df)
    if not df.empty and df.shape[1] > 0:
        df.set_index(df.columns[0], inplace=True)
    else:
        return no_update 

    return dcc.send_data_frame(df.to_csv, 'data_processed.csv', index=True)


@callback(
    Output('store-compound-names', 'data'),
    Input("store-current-step", "data"),
    prevent_initial_call=True
)
def extract_compound_names(current_step_key):
    if not current_step_key:
        return []

    df = cache_get(current_step_key)
    if df is None or df.empty or df.shape[1] == 0:
        return []

    df = df.copy()
    df.set_index(df.columns[0], inplace=True)

    compound_names = [
        col.rsplit('_', 1)[-1].rsplit(';', 1)[0]
        for col in df.columns
    ]
    return compound_names



@callback(
    Output('compound_dropdown', 'options'),
    #Output('compound_dropdown', 'value'),
    Input('compound-search-input', 'value'),
    Input('browse-compounds-checkbox', 'value'),
    State('store-compound-names', 'data'),
    prevent_initial_call=True
)
def update_information_dropdown(search_value, is_checked, compound_names):
    if not is_checked:
        return []

    if not compound_names:
        return []

    if search_value:
        filtered = [
            name for name in compound_names
            if search_value.lower() in name.lower()
        ]
    else:
        filtered = []
        #default_value = filtered[0] if filtered else None
    # Limit to first 20 to keep UI light
    filtered = filtered[:20]
    
    options = [{"label": name, "value": name} for name in filtered]
    

    return options



@app.callback(
    Output("compound-search-controls", "style"),
    Input("browse-compounds-checkbox", "value"),
)
def toggle_search_controls(is_checked):
    if is_checked:
        return {"display": "block"}
    return {"display": "none"}


if __name__ == '__main__':
    app.run(debug=True)    


# In[19]:


def processing_raw_files(peak_areas,metadata,canopus,structure,pattern):
    ft = peak_areas
    md = metadata
    an_gnps = structure
    sirius = canopus

    if not ft["Alignment ID"].dtype== sirius["mappingFeatureId"].dtype:# for feature table and the Sirius result table
        return None, None, None, None 


# Merge 'an_analog' with 'an_gnps' using a full join on the '#Scan#' column
    an_final = an_gnps
    an_final = pd.merge(an_gnps, sirius, on='mappingFeatureId', how='outer')
# Consolidate multiple annotations for a single '#Scan#' into one combined name


    an_final_single = an_final.groupby("mappingFeatureId").apply(lambda group: pd.Series({
        'Combined_Name': combine_names(group.iloc[0])
    })).reset_index()

# To get the DataFrame with that exact column name (without automatic renaming)
    an_final_single.columns = an_final_single.columns.str.replace('.', '_')

    ft_an1 = ft.merge(an_final, left_on= "Alignment ID",  how='inner', right_on= "mappingFeatureId", sort=True)

    ft_an = ft_an1.merge(an_final_single, left_on= "mappingFeatureId",  how='inner', right_on= "mappingFeatureId", sort=True)
    an_final = an_final.rename(columns={'Alignment ID':'mappingFeatureId'})
    # Merge 'an_final' with 'sirius' on 'row ID'
    merged_data = pd.merge(an_final, sirius, on='mappingFeatureId', how='outer')

    new_md = md.copy() #storing the files under different names to preserve the original files
    new_ft2 = ft.copy()
    
    # Perform the inner join to get the matching rows
    matching_rows = new_ft2.merge(an_final_single, left_on="Alignment ID", right_on="mappingFeatureId", how='inner')
    
    # Filter the original DataFrame to keep only the matching rows
    new_ft = ft[ft["Alignment ID"].isin(matching_rows["Alignment ID"])]

    #new_ft.columns = new_ft.columns.str.replace(' Peak area', '') # Removing " Peak area" extensions from the column names of new_ft
    new_ft = new_ft.sort_values(by='Alignment ID') # Arranging the rows of new_ft by ascending order of "row ID"
    
    new_ft = new_ft.loc[:, new_ft.notna().sum() > 0] # Removing columns in new_ft where all values are NaN
    new_md = new_md.loc[:, new_md.notna().sum() > 0] # Removing columns in new_md where all values are NaN
    
    new_md = new_md[new_md.apply(lambda row: all(item != "" for item in row), axis=1)] # Remove rows where all the elements are empty strings
    new_md = new_md.applymap(lambda x: x.strip() if isinstance(x, str) else x) # Remove leading and trailing spaces from each column of new_md

    # Changing the index (row names) of new_ft into the combined name as "XID_mz_RT":
    new_name = 'X' + new_ft['Alignment ID'].astype(str) + '_' + new_ft['Average Mz'].round(3).astype(str) + '_' + new_ft['Average Rt(min)'].round(3).astype(str) 
    new_name_values = new_name.values
    
    if 'ft_an' in locals():
        combined_name_ft = ft_an['Combined_Name'].astype(str).values
        underscore_added = ['_' + x for x in combined_name_ft] #add a underscore prefix
        new_name_values = np.core.defchararray.add(new_name_values.astype(str), underscore_added)
    
    # Set the new index and remove trailing underscore if present
    new_ft.index = new_name_values
    ft_an.index = new_name_values
    
    # Selecting only the columns with names containing 'mzXML' or 'mzML'
    new_ft = new_ft.loc[:, new_ft.columns.str.contains(f'^{pattern}')]
    new_ft_sirius_NPC = ft_an.loc[:, ft_an.columns.str.contains('^NPC|^SiriusScoreNormalized')]
    new_md = new_md.rename(columns={'name_file': 'filename'})
    new_ft = new_ft.reindex(columns=sorted(new_ft.columns)) # Ordering the columns of 'new_ft' by their names
    new_md = new_md.sort_values(by='filename').reset_index(drop=True) #ordering the md by the 1st column filename

    #DATA CLEAN UP PART
    ft_t = pd.DataFrame(new_ft).T
    ft_t = ft_t.apply(pd.to_numeric) #converting all values to numeric
    
    ft_t = ft_t.reset_index()
    new_ft_sirius_NPC = new_ft_sirius_NPC.reset_index()
    
    return ft_t,new_ft_sirius_NPC
   


# In[20]:


def scaling(imp):
    Imp_scaled = imp.copy()
    Imp_scaled.set_index(Imp_scaled.columns[0], inplace=True)
    Imp_scaled = pd.DataFrame(StandardScaler().fit_transform(Imp_scaled),
                      index=Imp_scaled.index,
                      columns=Imp_scaled.columns)
    Imp_scaled.index.name = 'filename'
    Imp_scaled.columns.name = 'compound_name'
    Imp_scaled = Imp_scaled.reset_index()
    return Imp_scaled


# In[21]:


def normalization(imp):
    normalized = imp.copy()
    normalized.set_index(normalized.columns[0], inplace=True)
    # Dividing each element of a particular row (as each row is the sample) with its row sum
    norm_TIC = normalized.apply(lambda x: x/np.sum(x), axis=1)
    norm_TIC.index.name = 'filename'
    norm_TIC.columns.name = 'compound_name'
    norm_TIC = norm_TIC.reset_index()
    return norm_TIC


# In[22]:


def imputation(blk_rem):
    cutoff_LOD = round(blk_rem.replace(0, np.nan).min(numeric_only=True).min())
    np.random.seed(141222)
    imp = blk_rem.copy()
    imp = imp.applymap(lambda x: np.random.randint(1, cutoff_LOD) if x == 0 else x)

    return imp


# In[23]:


def blank_processing(ft_t, new_md):

    Cutoff = 0.3
    print(ft_t.head)
    # Automatically find the first column that contains the word 'Blank' in any of its values
    blank_column = None
    for col in new_md.columns:
        if new_md[col].astype(str).str.contains('Blank', case=False).any():
            blank_column = col
            break
    
    if blank_column is None:
        raise ValueError("No column found containing 'Blank' values.")
    
    # Use this column as the grouping attribute
    sample_attribute = blank_column
    
    # Show unique values in the attribute column
    unique_levels = new_md[sample_attribute].unique()
    
    # Determine which levels are blanks (those containing 'Blank' in the string)
    blank_levels = [lvl for lvl in unique_levels if 'blank' in str(lvl).lower()]
    
    # All other levels can be considered samples (you can refine this if needed)
    sample_levels = [lvl for lvl in unique_levels if lvl not in blank_levels]
    
    # Check that filename column exists
    #assert 'filename' in new_md.columns, "'filename' column missing in metadata."
    
        # Filter for blanks
    md_Blank = new_md[new_md[sample_attribute].isin(blank_levels)]
    Blank = ft_t[ft_t.index.isin(md_Blank.index)]
    
    # Filter for samples
    md_Samples = new_md[new_md[sample_attribute].isin(sample_levels)]
    Samples = ft_t[ft_t.index.isin(md_Samples.index)]
    
    
    # Getting mean for every feature in blank and Samples in a DataFrame named 'Avg_ft'
    Avg_ft = pd.DataFrame({'Avg_blank': Blank.mean(axis=0, skipna=False)}) # Set skipna=False to check if there are NA values
    Avg_ft['Avg_samples'] = Samples.mean(axis=0, skipna=False) # Adding another column 'Avg_samples' for feature means of samples
    
    # Getting the ratio of blank vs Sample
    Avg_ft['Ratio_blank_Sample'] = (Avg_ft['Avg_blank'] + 1) / (Avg_ft['Avg_samples'] + 1)
    
    # Creating a bin with 1s when the ratio > Cutoff, else put 0s
    Avg_ft['Bg_bin'] = (Avg_ft['Ratio_blank_Sample'] > Cutoff).astype(int)
    
    # Calculating the number of background features and features present
    print("Total no.of features:", Samples.shape[1])
    print("No.of Background or noise features:", Avg_ft['Bg_bin'].sum())
    print("No.of features after excluding noise:", (Samples.shape[1] - Avg_ft['Bg_bin'].sum()))
    
    # Merging Samples with Avg_ft and selecting only the required rows and columns
    blk_rem = pd.concat([Samples.T, Avg_ft], axis=1, join='inner')
    blk_rem = blk_rem[blk_rem['Bg_bin'] == 0]  # Picking only the features
    blk_rem = blk_rem.drop(columns=['Avg_blank', 'Avg_samples', 'Ratio_blank_Sample', 'Bg_bin'])  # Removing the last 4 columns
    md_Samples.index.name = 'name_file'
    #
    blk_rem = blk_rem.T
    blk_rem.index.name = 'filename'      # samples on rows
    blk_rem.columns.name = 'compound_name'  # features on columns
    md_Samples = md_Samples.reset_index()
    blk_rem = blk_rem.reset_index()
    return blk_rem, md_Samples


# In[24]:


def combine_names(row):
    if row['name'] == row['pubchemids']:
        return row['name']
    return ';'.join([str(row['name']), str(row['pubchemids'])])


# In[25]:


def downcast_numeric(df):
    """
    Downcast all numeric columns in a DataFrame to float32
    """
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[numeric_cols] = df[numeric_cols].astype('float32')
    return df


# In[26]:


def convert_commas_to_floats(df):
    for col in df.columns:
        # Only attempt conversion on object (string) columns
        if df[col].dtype == 'object':
            try:
                df[col] = df[col].str.replace(",", ".").astype(float)
            except:
                pass  # Column may not be numeric-like, skip it
    return df


# In[27]:


def filter_merged_dataset(cleaned_data, metadata, ft_sirius, attribute_name,
                          sample_locations, threshold,
                          filter_class, filter_prob, filter_sirius,selected_compounds):
    
    if not sample_locations:
        return pd.DataFrame()
        
    if isinstance(sample_locations, str):
        sample_locations = [sample_locations]

    # 💡 NEW: filter cleaned_data columns by selected_compounds, if provided
    if selected_compounds:
        matched_columns = [
            col for col in cleaned_data.columns
            for name in selected_compounds
            if name in col  # partial match; or name.lower() in col.lower() for case-insensitive
        ]
        if matched_columns:  # only keep if something matched
            cleaned_data = cleaned_data[matched_columns]
        else:
            # Nothing matched; return empty dataframe early
            return pd.DataFrame()

        # Also filter ft_sirius to those compounds
        # Because ft_sirius['compound_name'] usually contains just the compound name part
        mask = ft_sirius['compound_name'].apply(
        lambda full_name: any(sel in full_name for sel in selected_compounds)
        )
        ft_sirius = ft_sirius[mask]
        if ft_sirius.empty:
            return pd.DataFrame()
    
    # Merge peak areas with metadata
    merged_md = pd.merge(cleaned_data, metadata, on='filename')
    merged_md = merged_md[merged_md[attribute_name].isin(sample_locations)]

    # Compute average intensity across X columns
    filtered_X = merged_md.loc[:, merged_md.columns.str.startswith('X')]
    row_avg = filtered_X.T.mean(axis=1)

    averaged_df = pd.DataFrame({
        'compound_name': cleaned_data.T.index,
        'average': row_avg
    }).set_index('compound_name')

    # Merge with ft_sirius
    merged = pd.merge(ft_sirius, averaged_df, on='compound_name')

    # Apply intensity threshold filter
    cutoff_value = merged['average'].quantile(1 - threshold)
    merged = merged[merged['average'] > cutoff_value]

    # Apply Sirius and NPC filters
    if filter_class:
        merged = merged[merged['NPC#class'].isin(filter_class)]
    if filter_prob:
        merged = merged[merged['NPC#pathway Probability'] > filter_prob]
        merged = merged[merged['NPC#superclass Probability'] > filter_prob]
        merged = merged[merged['NPC#class Probability'] > filter_prob]
    if filter_sirius:
        merged = merged[merged['SiriusScoreNormalized'] > filter_sirius]

    return merged.fillna("Unclassified")


# In[28]:


def process_and_plot_barplot_NPC(cleaned_data, metadata, ft_sirius, attribute_name,
                                  sample_locations, threshold, node_color_map,
                                  filter_class, filter_prob, filter_sirius,
                                  group_cols, type_plot, selected_compounds = None):
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if not sample_locations or not group_cols:
        return go.Figure()


    if selected_compounds:
        matched_columns = [
            col for col in cleaned_data.columns
            for name in selected_compounds
            if name in col
        ]
        if matched_columns:
            cleaned_data = cleaned_data[matched_columns]
        else:
            return go.Figure()
    
        mask = ft_sirius['compound_name'].apply(
            lambda full_name: any(sel in full_name for sel in selected_compounds)
        )
        ft_sirius = ft_sirius[mask]
        if ft_sirius.empty:
            return go.Figure()
            
    # Merge peak data with metadata
    cleaned_data_md = pd.merge(cleaned_data, metadata, on='filename')

    # Create one subplot per selected group_col
    fig = make_subplots(
        rows=len(group_cols), cols=1,
        shared_xaxes=True,
        subplot_titles=[f'Grouped by {col.capitalize()}' for col in group_cols],
        vertical_spacing=0.15
    )

    for idx, group_col in enumerate(group_cols, start=1):
        data = {}

        for location in sample_locations:
            filtered = cleaned_data_md[cleaned_data_md[attribute_name] == location]
            filtered_X = filtered.loc[:, filtered.columns.str.startswith('X')]
            row_avg = filtered_X.T.mean(axis=1)

            averaged_df = pd.DataFrame({
                'compound_name': cleaned_data.T.index,
                'average': row_avg
            }).set_index('compound_name')

            merged = pd.merge(ft_sirius, averaged_df, on='compound_name')
            cutoff_value = merged['average'].quantile(1 - threshold)
            merged = merged[merged['average'] > cutoff_value]

            if filter_class:
                merged = merged[merged[group_col].isin(filter_class)]
            if filter_prob:
                merged = merged[merged['NPC#pathway Probability'] > filter_prob]
                merged = merged[merged['NPC#superclass Probability'] > filter_prob]
                merged = merged[merged['NPC#class Probability'] > filter_prob]
            if filter_sirius:
                merged = merged[merged['SiriusScoreNormalized'] > filter_sirius]

            merged = merged.fillna('Unclassified')

            # Group by group_col and store per sample
            if type_plot == 'Intensity':
                grouped = merged.groupby(group_col)['average'].mean()
            elif type_plot == 'Count':
                grouped = merged.groupby(group_col)['average'].count()

            for group_name, val in grouped.items():
                if group_name not in data:
                    data[group_name] = {}
                data[group_name][location] = val

        # Add bars for this group_col
        for group_name, values in data.items():
            y_vals = [values.get(sample, 0) for sample in sample_locations]
            fig.add_trace(
                go.Bar(
                    x=sample_locations,
                    y=y_vals,
                    name=group_name,
                    marker_color=node_color_map.get(group_name, '#CCCCCC'),
                    #showlegend=(idx == 1)  # Only show legend once
                ),
                row=idx, col=1
            )

    fig.update_layout(
        barmode='group',
        height=400 * len(group_cols),  # Adjust height dynamically
        title="Average Intensity or Count per Group (Multiple Subplots)",
        template="simple_white",
        legend_title="Group",
    )

    return fig


# In[29]:


def process_and_plot_lineplot_NPC(
    cleaned_data, metadata, ft_sirius, attribute_name,
    sample_locations, threshold, node_color_map,
    filter_class, filter_prob, filter_sirius,
    group_cols, type_plot,  selected_compounds=None ):
    import pandas as pd
    import plotly.graph_objects as go
    import math
    
    from plotly.subplots import make_subplots

    if not sample_locations or not group_cols:
        return 

    # Ensure group_cols is always a list
    if isinstance(group_cols, str):
        group_cols = [group_cols]
        
    if selected_compounds:
        matched_columns = [
            col for col in cleaned_data.columns
            for name in selected_compounds
            if name in col
        ]
        if matched_columns:
            cleaned_data = cleaned_data[matched_columns]
        else:
            return go.Figure()
    
        mask = ft_sirius['compound_name'].apply(
            lambda full_name: any(sel in full_name for sel in selected_compounds)
        )
        ft_sirius = ft_sirius[mask]
        if ft_sirius.empty:
            return go.Figure()
    
                 
    # Merge peak data with metadata
    cleaned_data_md = pd.merge(cleaned_data, metadata, on='filename')

    # Collect all unique (group_col, group_value) combinations
    unique_groups = []

    for group_col in group_cols:
        # merged data before sample filtering (we will filter again later)
        unique_values = ft_sirius[group_col].dropna().unique()
        for group_value in unique_values:
            unique_groups.append((group_col, group_value))

    # Create subplot per unique group value
    n_subplots = len(unique_groups)
    n_plots = len(unique_groups)
    n_cols = 5  # or 4, adjust as needed
    n_rows = math.ceil(n_plots / n_cols)
    
    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=[f"{col}: {val}" for col, val in unique_groups],
        vertical_spacing=0.05,   # a bit more space vertically
        horizontal_spacing=0.05  # space between columns
    )
    for idx, (group_col, group_value) in enumerate(unique_groups, start=0):
        # Collect data per sample_location
        traces = []

        for location in sample_locations:
            # Filter metadata to this sample location
            filtered = cleaned_data_md[cleaned_data_md[attribute_name] == location]
            filtered_X = filtered.loc[:, filtered.columns.str.startswith('X')]
            row_avg = filtered_X.T.mean(axis=1)
        
            averaged_df = pd.DataFrame({
                'compound_name': cleaned_data.T.index,
                'average': row_avg
            }).set_index('compound_name')
        
            merged = pd.merge(ft_sirius, averaged_df, on='compound_name')
            cutoff_value = merged['average'].quantile(1 - threshold)
            merged = merged[merged['average'] > cutoff_value]
        
            # Apply filters
            if filter_class:
                merged = merged[merged[group_col].isin(filter_class)]
            if filter_prob:
                merged = merged[merged['NPC#pathway Probability'] > filter_prob]
                merged = merged[merged['NPC#superclass Probability'] > filter_prob]
                merged = merged[merged['NPC#class Probability'] > filter_prob]
            if filter_sirius:
                merged = merged[merged['SiriusScoreNormalized'] > filter_sirius]



            
            
            # remove outliers
            Q1 = merged['average'].quantile(0.25)
            Q3 = merged['average'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            merged = merged[(merged['average'] >= lower_bound) & (merged['average'] <= upper_bound)]
        
            # Filter to current group_value
            subset = merged[merged[group_col] == group_value]
        
            color = node_color_map.get(group_value, '#CCCCCC')
        
            if subset.empty:
                # add empty box for this location
                trace_box = go.Box(
                    y=[None],
                    name=location,
                    marker_color=color,
                    boxmean='sd',
                    showlegend=False
                )
                trace_scatter = go.Scatter(
                    x=[location],
                    y=[None],
                    mode='markers',
                    marker=dict(size=6, color=node_color_map.get(group_value, '#999999')),
                    name=f"{location}",
                    showlegend=False
                )
            else:
                trace_box = go.Box(
                    y=subset['average'],
                    name=location,
                    marker_color=color,
                    boxmean='sd',
                    showlegend=False
                )
                trace_scatter = go.Scatter(
                    x=[location]*len(subset),
                    y=subset['average'],
                    mode='markers+text' if selected_compounds else 'markers',
                    marker=dict(size=6, color=node_color_map.get(group_value, '#999999')),
                    hovertext=subset['compound_name'] if selected_compounds else None,
                    hoverinfo='text+y',
                    textposition='top center',
                    name=f"{location}",
                    showlegend=False
                )
        
            row_idx = idx // n_cols + 1
            col_idx = idx % n_cols + 1
        
            fig.add_trace(trace_box, row=row_idx, col=col_idx)
            fig.add_trace(trace_scatter, row=row_idx, col=col_idx)
            
    for i in range(1, n_rows * n_cols + 1):
        fig.update_xaxes(categoryorder='array', categoryarray=sample_locations, row=(i-1)//n_cols+1, col=(i-1)%n_cols+1)
            
    fig.update_layout(height=300 * n_rows, width=400 * n_cols,
                      template="simple_white")

    return fig



# In[30]:


def process_and_plot_intensity_NPC(cleaned_data, metadata, ft_sirius, attribute_name, sample_locations, threshold, node_color_map, filter_class, filter_prob, filter_sirius, selected_compounds = None):
    from plotly.subplots import make_subplots
    import plotly.express as px
    import plotly.graph_objects as go
    import math
    import pandas as pd

    if not sample_locations:
        return go.Figure()  # empty figure to avoid crashing

    if selected_compounds:
        matched_columns = [
            col for col in cleaned_data.columns
            for name in selected_compounds
            if name in col
        ]
        if matched_columns:
            cleaned_data = cleaned_data[matched_columns]
        else:
            return go.Figure()
    
        mask = ft_sirius['compound_name'].apply(
            lambda full_name: any(sel in full_name for sel in selected_compounds)
        )
        ft_sirius = ft_sirius[mask]
        if ft_sirius.empty:
            return go.Figure()    

    plots_per_row = 5  # adjust to fit your layout needs
    total_plots = len(sample_locations)
    n_rows = math.ceil(total_plots / plots_per_row)
    n_cols = min(total_plots, plots_per_row)

    # Build the specs dynamically: each row has 'n_cols' domains
    specs = []
    for _ in range(n_rows):
        row_specs = [{'type': 'domain'}] * n_cols
        specs.append(row_specs)

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=sample_locations,
        specs=specs
    )

    for idx, location in enumerate(sample_locations):
        row_idx = idx // plots_per_row + 1
        col_idx = idx % plots_per_row + 1

        cleaned_data_md = pd.merge(cleaned_data, metadata, on='filename')
        filtered = cleaned_data_md[cleaned_data_md[attribute_name] == location]
        filtered_X = filtered.loc[:, filtered.columns.str.startswith('X')]
        row_avg = filtered_X.T.mean(axis=1)

        averaged_df = pd.DataFrame({
            'compound_name': cleaned_data.T.index,
            'average': row_avg
        }).set_index('compound_name')

        values_raw = averaged_df['average']

        min_val = values_raw.min()
        if min_val <= 0:
            values = values_raw + abs(min_val) + 1e-6
        else:
            values = values_raw

        averaged_df['average'] = values

        merged = pd.merge(ft_sirius, averaged_df, on='compound_name')
        cutoff_value = merged['average'].quantile(1 - threshold)
        merged = merged[merged['average'] > cutoff_value]

        if filter_class:
            merged = merged[merged['NPC#pathway'].isin(filter_class)]
        if filter_prob:
            merged = merged[merged['NPC#pathway Probability'] > filter_prob]
            merged = merged[merged['NPC#superclass Probability'] > filter_prob]
            merged = merged[merged['NPC#class Probability'] > filter_prob]
        if filter_sirius:
            merged = merged[merged['SiriusScoreNormalized'] > filter_sirius]

        merged = merged.fillna('Unclassified')

        sunburst = px.sunburst(
            merged,
            path=['NPC#pathway', 'NPC#superclass', 'NPC#class'],
            values='average',
        )

        # Re-map each node's label to its color
        for trace in sunburst.data:
            labels = trace.labels
            trace.marker.colors = [node_color_map.get(label, '#CCCCCC') for label in labels]

            fig.add_trace(trace, row=row_idx, col=col_idx)

    fig.update_layout(
        title_text="Sunburst Plots with Distinct Colors Per Node",
        showlegend=False,
        height=400 * n_rows  # adjust figure height dynamically
    )

    return fig


# In[31]:


def process_and_plot_NPC_count(cleaned_data, metadata, ft_sirius, attribute_name,sample_locations,threshold,node_color_map,filter_class,filter_prob,filter_sirius, selected_compounds = None):
    from plotly.subplots import make_subplots
    import plotly.express as px
    import pandas as pd
    if not sample_locations:
        return go.Figure()  # return an empty plot to prevent crashing

    if selected_compounds:
        matched_columns = [
            col for col in cleaned_data.columns
            for name in selected_compounds
            if name in col
        ]
        if matched_columns:
            cleaned_data = cleaned_data[matched_columns]
        else:
            return go.Figure()
    
        mask = ft_sirius['compound_name'].apply(
            lambda full_name: any(sel in full_name for sel in selected_compounds)
        )
        ft_sirius = ft_sirius[mask]
        if ft_sirius.empty:
            return go.Figure()
    
    fig = make_subplots(
        rows=1,
        cols=len(sample_locations),
        subplot_titles=sample_locations,
        specs=[[{'type': 'domain'}] * len(sample_locations)]
    )

    for i, location in enumerate(sample_locations):
        # Merge cleaned_data with metadata on 'filename'
        cleaned_data_md = pd.merge(cleaned_data, metadata, on='filename')

        # Filter the merged data based on the current sample location
        cleaned_data_md_filtered = cleaned_data_md[cleaned_data_md[attribute_name] == location]

        # Select columns that start with 'X'
        cleaned_data_filtered_X = cleaned_data_md_filtered.loc[:, cleaned_data_md_filtered.columns.str.startswith('X')]

        # Calculate row averages
        row_averages = cleaned_data_filtered_X.T.mean(axis=1)

        # Create a new DataFrame with the index and the averaged values
        averaged_df = pd.DataFrame({
            'compound_name': cleaned_data.T.index,
            'average': row_averages
        })

        #Set the index of the new DataFrame
        averaged_df.set_index('compound_name', inplace=True)

        # Merge with ft_sirius on 'compound_name'
        merged_sirius_data_T = pd.merge(ft_sirius, averaged_df, on='compound_name')
        if filter_class:
          merged_sirius_data_T = merged_sirius_data_T[merged_sirius_data_T['NPC#pathway'].isin(filter_class)]
        if filter_prob:
          merged_sirius_data_T = merged_sirius_data_T[merged_sirius_data_T['NPC#pathway Probability'] > filter_prob]
          merged_sirius_data_T = merged_sirius_data_T[merged_sirius_data_T['NPC#superclass Probability'] > filter_prob]
          merged_sirius_data_T = merged_sirius_data_T[merged_sirius_data_T['NPC#class Probability'] > filter_prob]
        if filter_sirius:
          merged_sirius_data_T = merged_sirius_data_T[merged_sirius_data_T['SiriusScoreNormalized'] > filter_sirius]
        merged_sirius_data_T = merged_sirius_data_T.fillna('Unclassified')
        # Copy and filter columns of interest
        merged_sirius_data_T_copy = merged_sirius_data_T.copy()
        col_interests =['NPC#pathway', 'NPC#superclass', 'NPC#class','average']
        merged_sirius_data_T_copy = merged_sirius_data_T_copy[col_interests].fillna('Unclassified')
       # merged_sirius_data_T_copy = merged_sirius_data_T_copy[merged_sirius_data_T['average'] > threshold]
        
         
        cutoff_value = merged_sirius_data_T_copy['average'].quantile(1 - threshold)
        merged_sirius_data_T_copy = merged_sirius_data_T_copy[merged_sirius_data_T_copy['average'] > cutoff_value]
        
         # Create a sunburst plot for the current sample location
        sunburst = px.sunburst(
            merged_sirius_data_T_copy,
            path=['NPC#pathway', 'NPC#superclass', 'NPC#class'],
            values=None
        )

        # Re-map each node's label to its color
        for trace in sunburst.data:
            labels = trace.labels
            trace.marker.colors = [node_color_map.get(label, '#CCCCCC') for label in labels]

        for trace in sunburst.data:
            fig.add_trace(trace, row=1, col=i+1)

    # Update layout
    fig.update_layout(
        title_text="Sunburst Plots with Distinct Colors Per Node",
        showlegend=False
    )

    return fig





# In[33]:



def process_and_plot_pca(
    cleaned_data,
    metadata,
    ft_sirius,
    attribute_name,
    sample_locations,
    threshold,
    filter_class,
    filter_prob,
    filter_sirius,
    selected_compounds = None 
):
    import pandas as pd
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    import plotly.express as px
    import plotly.graph_objects as go

    if not sample_locations:
        return go.Figure()

    if selected_compounds:
        matched_columns = [
            col for col in cleaned_data.columns
            for name in selected_compounds
            if name in col
        ]
        if matched_columns:
            cleaned_data = cleaned_data[matched_columns]
        else:
            return go.Figure()
    
        mask = ft_sirius['compound_name'].apply(
            lambda full_name: any(sel in full_name for sel in selected_compounds)
        )
        ft_sirius = ft_sirius[mask]
        if ft_sirius.empty:
            return go.Figure()

    
    # Merge peak and metadata
    data = pd.merge(cleaned_data, metadata, on='filename')
    data = convert_commas_to_floats(data)
    ft_sirius = convert_commas_to_floats(ft_sirius)

    # Filter by selected sample locations
    data = data[data[attribute_name].isin(sample_locations)]

    # Extract compound intensity columns
    compound_cols = [col for col in data.columns if col.startswith("X")]
    intensity_matrix = data[compound_cols].copy()

    # Handle negative/zero values (important for log-based data or scaling)
    if intensity_matrix.min().min() <= 0:
        intensity_matrix += abs(intensity_matrix.min().min()) + 1e-6

    # Transpose to get per-compound averages for filtering
    compound_averages = intensity_matrix.mean(axis=0).reset_index()
    compound_averages.columns = ['compound_name', 'average']

    # Merge with annotation
    merged = pd.merge(ft_sirius, compound_averages, on='compound_name', how='inner')

    # Apply filtering logic
    cutoff = merged['average'].quantile(1 - threshold)
    merged = merged[merged['average'] > cutoff]

    if filter_class:
        merged = merged[merged['NPC#pathway'].isin(filter_class)]
    if filter_prob:
        merged = merged[
            (merged['NPC#pathway Probability'] > filter_prob) &
            (merged['NPC#superclass Probability'] > filter_prob) &
            (merged['NPC#class Probability'] > filter_prob)
        ]
    if filter_sirius:
        merged = merged[merged['SiriusScoreNormalized'] > filter_sirius]

    selected_compounds = merged['compound_name'].tolist()
    selected_cols = [col for col in compound_cols if col in selected_compounds]

    if not selected_cols:
        return go.Figure()

    # Extract the final matrix and labels
    final_matrix = intensity_matrix[selected_cols]
    labels = data[attribute_name].values

    if final_matrix.shape[0] < 2 or final_matrix.shape[1] < 2:
        return go.Figure(
            layout=dict(
                title="Not enough samples or features for PCA.",
                template="plotly_white"
            )
        )


    
    # Scale the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(final_matrix)

    # Apply PCA
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)

    # Create plot dataframe
    pca_df = pd.DataFrame({
        'PC1': components[:, 0],
        'PC2': components[:, 1],
        'Location': labels
    })
        # Run MANOVA to test group separation
    subtitle = ""
    if len(set(labels)) > 1:
        pc_df = pd.DataFrame({
        'PC1': components[:, 0],
        'PC2': components[:, 1],
        'group': labels
        })
        try:
            maov = MANOVA.from_formula('PC1 + PC2 ~ group', data=pc_df)
            test_res = maov.mv_test()
            # Extract Wilks' Lambda p-value
            wilks_pval = test_res.results['group']['stat']['Pr > F']["Wilks' lambda"]
            subtitle = f" (Wilks' Lambda p = {wilks_pval:.3e})"
        except Exception as e:
            subtitle = ""

    # --- Scatter plot (PCA of samples) ---
    scatter = px.scatter(
        pca_df,
        x='PC1',
        y='PC2',
        color='Location',
        labels={
            'PC1': f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)",
            'PC2': f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)"
        }
    )
    scatter.update_traces(marker=dict(size=10, line=dict(width=1, color='black')))
    
    # --- Heatmap (Feature contributions) ---
    loadings = np.dot(X_scaled.T, components)
    loadings_df = pd.DataFrame(
        loadings,
        index=selected_cols,
        columns=[f'PC{i+1}' for i in range(components.shape[1])]
    )
    loadings_df = (loadings_df - loadings_df.mean()) / loadings_df.std()
    
    heatmap = px.imshow(
        loadings_df,
        color_continuous_scale="RdBu_r",
        labels=dict(x="Principal Components", y="Features", color="Contribution")
    )
    
    # --- Combine both into one figure with subplots ---
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7,0.3],
        row_heights = [1],
        subplot_titles=(f'PCA of Samples{subtitle}', "Features")
    )
    
    # Add scatter traces
    for trace in scatter.data:
        fig.add_trace(trace, row=1, col=1)
    
    # Add heatmap trace
    for trace in heatmap.data:
        fig.add_trace(trace, row=1, col=2)
    
    # Update layout
    fig.update_layout(
        template="plotly_white",
        height=1200,
        width=2000
    )
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    # Hide duplicate legends and fix overlap
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Contribution",
            x=1.05  # pushes the heatmap colorbar to the right of the figure
        ),
        legend=dict(
            orientation="h",   # horizontal legend
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    # Restore PCA axis labels
    fig.update_xaxes(
        title_text=f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)",
        row=1, col=1
    )
    fig.update_yaxes(
        title_text=f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)",
        row=1, col=1
    )
    return fig   


# In[34]:


def process_and_plot_rf(cleaned_data, metadata, ft_sirius,
                        group_col, sample_locations,
                        threshold, filter_class, filter_prob, filter_sirius,
                        type_plot="Intensity"):
    """
    Train a Random Forest classifier on LC-MS/MS data and return a feature importance plot.
    """


    # --- Merge cleaned_data with metadata ---
    #if 'filename' not in cleaned_data.columns or 'filename' not in metadata.columns:
       # return px.scatter(title="Missing 'filename' column to merge cleaned data and metadata")

    df = pd.merge(cleaned_data, metadata, on='filename')

    # --- Only keep selected samples (if provided) ---
    if sample_locations:
        df = df[df[group_col].isin(sample_locations)]
        if df.empty:
            return px.scatter(title="No matching samples after filtering")

    # --- Apply Sirius/Canopus filters ---
    ft = ft_sirius.copy()

    #if filter_class:
    #    ft = ft[ft['NPC#superclass'].isin(filter_class) |
     #           ft['NPC#class'].isin(filter_class) |
     #           ft['NPC#pathway'].isin(filter_class)]
    if filter_prob:
        ft = ft[(ft['NPC#pathway Probability'] > filter_prob) &
                (ft['NPC#superclass Probability'] > filter_prob) &
                (ft['NPC#class Probability'] > filter_prob)]
    if filter_sirius:
        ft = ft[ft['SiriusScoreNormalized'] > filter_sirius]

    if ft.empty:
        return px.scatter(title="No features passed the filtering criteria")

    # --- Build feature matrix ---
    # Assume compound intensities are columns "X..." and identified in ft_sirius["compound_name"]
    feature_cols = [c for c in df.columns if c.startswith("X")]
    X = df[feature_cols]
    y = df[group_col]

    if y.nunique() < 2:
        return px.scatter(title="Need at least 2 groups for classification")

    # --- Train Random Forest ---
    rf = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
    rf.fit(X, y)

    cv_dynamic = min(5, y.nunique())
    
    scores = cross_val_score(rf, X, y, cv=cv_dynamic)
    acc = scores.mean()

    # --- Importances ---
    importances = pd.Series(rf.feature_importances_, index=feature_cols)

    feat_imp = (
        importances.to_frame('importance')
        .reset_index()
        .rename(columns={'index': 'compound_id'})
        .merge(ft, left_on='compound_id', right_on='compound_name', how='left')
        .sort_values('importance', ascending=False)
    )

    top_feats = feat_imp.head(20)

    # --- Plot ---
    fig = px.bar(
        top_feats,
        x="importance",
        y="compound_id",
        color="NPC#superclass",
        orientation="h",
        hover_data=["NPC#class", "NPC#pathway"]
    )
    fig.update_layout(
        title=f"Top 20 Features by Random Forest Importance<br>(CV Accuracy = {acc:.2f})",
        xaxis_title="Importance",
        yaxis_title="Feature",
        yaxis={"categoryorder": "total ascending"}
    )

    return fig


# In[35]:


def generate_node_level_color_map(ft_sirius):

        # Create a mapping for aliases / typo corrections
    alias_map = {
        "Sphingolipids": "Spingolipids",
        "GlycoLipids": "Glycolipids",
        # Add more mappings here as needed
    }

    # Apply alias mapping to relevant columns
    for col in ['NPC#pathway', 'NPC#superclass', 'NPC#class']:
        ft_sirius[col] = ft_sirius[col].replace(alias_map)
    # Combine all unique labels
    pathways = ft_sirius['NPC#pathway'].fillna('Unclassified').unique()
    superclasses = ft_sirius['NPC#superclass'].fillna('Unclassified').unique()
    classes = ft_sirius['NPC#class'].fillna('Unclassified').unique()
    all_labels = sorted(set(pathways.tolist() + superclasses.tolist() + classes.tolist()))

    # 🔥 Better color palette
    palette = sample_colorscale('Plasma', [i/len(all_labels) for i in range(len(all_labels))])

    color_map = dict(zip(all_labels, palette))
    return color_map

# Node color mapping (placeholder; you can customize this)
ft_sirius_NPC2 = pd.read_csv('NPC_ft.csv', index_col = 0)

node_color_map = generate_node_level_color_map(ft_sirius_NPC2)


# In[36]:


def parse_contents(contents,trim=False):

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    decoded_str = decoded.decode('utf-8')

    # Try to detect if it's TSV or CSV based on first line
    first_line = decoded_str.splitlines()[0]
    delimiter = '\t' if '\t' in first_line else ','

    if trim:
        df = pd.read_csv(io.StringIO(decoded_str), delimiter=delimiter,skiprows=4)
    else:
        df = pd.read_csv(io.StringIO(decoded_str), delimiter=delimiter)
    
    df.reset_index(drop=True, inplace=True)
    print("Index name:", df.index.name)
    print(df.head())
    return df





# In[ ]:





# In[ ]:




