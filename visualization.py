from models import ChartFlag, ChartType
import json

def create_metadata(df):
    return df.head().to_string()

def potential_data_visualisation(user_input, session_state, client):
    """
    Decide whether a visualisation is needed and, if so, which one.

    Parameters
    ----------
    user_input : str
        The user’s prompt.
    session_state : streamlit.session_state
        Holds df / forecast_df / forecast flag.
    client : OpenAI
        OpenAI client.

    Returns
    -------
    ChartType | None
        A ChartType instance describing the chosen visualisation,
        or None if no chart is necessary.
    """

    # ------------------------------------------------------------------
    # 1) Detect forecasting mode
    # ------------------------------------------------------------------
    forecasting = bool(getattr(session_state, "forecast", False))

    # ------------------------------------------------------------------
    # 2) Build metadata strings
    # ------------------------------------------------------------------
    md_main = create_metadata(session_state.df)
    retrieved_context = f"Main DataFrame Metadata:\n{md_main}"

    if forecasting:
        md_fore = create_metadata(session_state.forecast_df)
        retrieved_context += f"\n\nForecast DataFrame Metadata:\n{md_fore}"
        dfs_desc = (
            "'dataframe' is the main dataset; "
            "'forecast_dataframe' is the forecasted data."
        )
    else:
        dfs_desc = "'dataframe' is the main dataset."

    # ------------------------------------------------------------------
    # 3) First LLM call – is a chart needed?
    # ------------------------------------------------------------------
    flag_schema = {
        "name": "visualisation_flag",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "visualisation_necessary": {
                    "type": "boolean",
                    "description": "Whether a visualisation is required."
                }
            },
            "required": ["visualisation_necessary"],
            "additionalProperties": False
        },
    }

    flag_prompt = (
        f"Given the prompt `{user_input}` and the metadata below, decide if the "
        f"answer should be shown as a data visualisation. Return JSON like "
        f'{{"visualisation_necessary": true|false}}. {dfs_desc}'
    )

    flag_resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": flag_prompt},
            {"role": "user", "content": f"{retrieved_context}"}
        ],
        response_format={"type": "json_schema", "json_schema": flag_schema},
    )

    if not ChartFlag.model_validate_json(flag_resp.choices[0].message.content
                                         ).visualisation_necessary:
        return None  # ‑‑ textual answer is enough
    
    chart_types = [{'Type': 'Scatter',
  'Method': 'scatter',
  'Description': 'In a scatter plot, each row of data_frame is represented by a symbol mark in 2D space.'},
 {'Type': 'Line',
  'Method': 'line',
  'Description': 'In a 2D line plot, each row of data_frame is represented as vertex of a polyline mark in 2D space.'},
 {'Type': 'Area',
  'Method': 'area',
  'Description': 'In a stacked area plot, each row of data_frame is represented as vertex of a polyline mark in 2D space. The area between successive polylines is filled.'},
 {'Type': 'Bar',
  'Method': 'bar',
  'Description': 'In a bar plot, each row of data_frame is represented as a rectangular mark.'},
 {'Type': 'Funnel',
  'Method': 'funnel',
  'Description': 'In a funnel plot, each row of data_frame is represented as a rectangular sector of a funnel.'},
 {'Type': 'Timeline',
  'Method': 'timeline',
  'Description': 'In a timeline plot, each row of data_frame is represented as a rectangular mark on an x axis of type date, spanning from x_start to x_end.'},
 {'Type': 'Pie',
  'Method': 'pie',
  'Description': 'In a pie plot, each row of data_frame is represented as a sector of a pie.'},
 {'Type': 'Sunburst',
  'Method': 'sunburst',
  'Description': 'A sunburst plot represents hierarchial data as sectors laid out over several levels of concentric rings.'},
 {'Type': 'Treemap',
  'Method': 'treemap',
  'Description': 'A treemap plot represents hierarchial data as nested rectangular sectors.'},
 {'Type': 'Icicle',
  'Method': 'icicle',
  'Description': 'An icicle plot represents hierarchial data with adjoined rectangular sectors that all cascade from root down to leaf in one direction.'},
 {'Type': 'Funnel Area',
  'Method': 'funnel_area',
  'Description': 'In a funnel area plot, each row of data_frame is represented as a trapezoidal sector of a funnel.'},
 {'Type': 'Histogram',
  'Method': 'histogram',
  'Description': "In a histogram, rows of data_frame are grouped together into a rectangular mark to visualize the 1D distribution of an aggregate function histfunc (e.g. the count or sum) of the value y (or x if orientation is 'h')."},
 {'Type': 'Box',
  'Method': 'box',
  'Description': 'In a box plot, rows of data_frame are grouped together into a box-and-whisker mark to visualize their distribution. Each box spans from quartile 1 (Q1) to quartile 3 (Q3). The second quartile (Q2) is marked by a line inside the box. By default, the whiskers correspond to the box’ edges +/- 1.5 times the interquartile range (IQR: Q3-Q1), see “points” for other options.'},
 {'Type': 'Violin',
  'Method': 'violin',
  'Description': 'In a violin plot, rows of data_frame are grouped together into a curved mark to visualize their distribution.'},
 {'Type': 'Strip',
  'Method': 'strip',
  'Description': 'In a strip plot each row of data_frame is represented as a jittered mark within categories.'},
 {'Type': 'ECDF',
  'Method': 'ecdf',
  'Description': "In a Empirical Cumulative Distribution Function (ECDF) plot, rows of data_frame are sorted by the value x (or y if orientation is 'h') and their cumulative count (or the cumulative sum of y if supplied and orientation is h) is drawn as a line."},
 {'Type': 'Density Heatmap',
  'Method': 'density_heatmap',
  'Description': 'In a density heatmap, rows of data_frame are grouped together into colored rectangular tiles to visualize the 2D distribution of an aggregate function histfunc (e.g. the count or sum) of the value z.'},
 {'Type': 'Density Contour',
  'Method': 'density_contour',
  'Description': 'In a density contour plot, rows of data_frame are grouped together into contour marks to visualize the 2D distribution of an aggregate function histfunc (e.g. the count or sum) of the value z.'},
 {'Type': 'Imshow', 'Method': 'imshow', 'Description': 'No blockquote found'},
 {'Type': 'Scatter 3D',
  'Method': 'scatter_3d',
  'Description': 'In a 3D scatter plot, each row of data_frame is represented by a symbol mark in 3D space.'},
 {'Type': 'Line 3D',
  'Method': 'line_3d',
  'Description': 'In a 3D line plot, each row of data_frame is represented as vertex of a polyline mark in 3D space.'},
 {'Type': 'Scatter Matrix',
  'Method': 'scatter_matrix',
  'Description': 'In a scatter plot matrix (or SPLOM), each row of data_frame is represented by a multiple symbol marks, one in each cell of a grid of 2D scatter plots, which plot each pair of dimensions against each other.'},
 {'Type': 'Parallel Coordinates',
  'Method': 'parallel_coordinates',
  'Description': 'In a parallel coordinates plot, each row of data_frame is represented by a polyline mark which traverses a set of parallel axes, one for each of the dimensions.'},
 {'Type': 'Parallel Categories',
  'Method': 'parallel_categories',
  'Description': 'In a parallel categories (or parallel sets) plot, each row of data_frame is grouped with other rows that share the same values of dimensions and then plotted as a polyline mark through a set of parallel axes, one for each of the dimensions.'},
 {'Type': 'Scatter Mapbox',
  'Method': 'scatter_mapbox',
  'Description': 'In a Mapbox scatter plot, each row of data_frame is represented by a symbol mark on a Mapbox map.'},
 {'Type': 'Line Mapbox',
  'Method': 'line_mapbox',
  'Description': 'In a Mapbox line plot, each row of data_frame is represented as vertex of a polyline mark on a Mapbox map.'},
 {'Type': 'Choropleth Mapbox',
  'Method': 'choropleth_mapbox',
  'Description': 'In a Mapbox choropleth map, each row of data_frame is represented by a colored region on a Mapbox map.'},
 {'Type': 'Density Mapbox',
  'Method': 'density_mapbox',
  'Description': 'In a Mapbox density map, each row of data_frame contributes to the intensity of the color of the region around the corresponding point on the map'},
 {'Type': 'Scatter Geo',
  'Method': 'scatter_geo',
  'Description': 'In a geographic scatter plot, each row of data_frame is represented by a symbol mark on a map.'},
 {'Type': 'Line Geo',
  'Method': 'line_geo',
  'Description': 'In a geographic line plot, each row of data_frame is represented as vertex of a polyline mark on a map.'},
 {'Type': 'Choropleth',
  'Method': 'choropleth',
  'Description': 'In a choropleth map, each row of data_frame is represented by a colored region mark on a map.'},
 {'Type': 'Scatter Polar',
  'Method': 'scatter_polar',
  'Description': 'In a polar scatter plot, each row of data_frame is represented by a symbol mark in polar coordinates.'},
 {'Type': 'Line Polar',
  'Method': 'line_polar',
  'Description': 'In a polar line plot, each row of data_frame is represented as vertex of a polyline mark in polar coordinates.'},
 {'Type': 'Bar Polar',
  'Method': 'bar_polar',
  'Description': 'In a polar bar plot, each row of data_frame is represented as a wedge mark in polar coordinates.'},
 {'Type': 'Scatter Ternary',
  'Method': 'scatter_ternary',
  'Description': 'In a ternary scatter plot, each row of data_frame is represented by a symbol mark in ternary coordinates.'},
 {'Type': 'Line Ternary',
  'Method': 'line_ternary',
  'Description': 'In a ternary line plot, each row of data_frame is represented as vertex of a polyline mark in ternary coordinates.'}]# Keep the existing chart_types definition here

    vis_schema = {
        "name": "visualisation_format",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "Type":        {"type": "string"},
                "Method":      {"type": "string"},
                "Description": {"type": "string"},
            },
            "required": ["Type", "Method", "Description"],
            "additionalProperties": False,
        },
    }

    vis_prompt = (
        f"Prompt: `{user_input}`\n\nChoose the single best chart type from the "
        f"list supplied. Respond in JSON like "
        f'{{"Type": "...", "Method": "...", "Description": "..."}}. {dfs_desc}'
    )

    vis_resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": vis_prompt},
            {"role": "user",   "content": f"{retrieved_context}\n\nChoices:\n{json.dumps(chart_types)}"},
        ],
        response_format={"type": "json_schema", "json_schema": vis_schema},
    )

    return ChartType.model_validate_json(vis_resp.choices[0].message.content)