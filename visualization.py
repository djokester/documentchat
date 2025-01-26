from models import ChartFlag, ChartType
import json

def create_metadata(df):
    return df.head().to_string()

def potential_data_visualisation(user_input, session_state, forecasting, client ):
    """
    Determines if a data visualization is necessary and identifies the best visualization type.

    Parameters:
    - user_input: The user's prompt for the visualization.
    - session_state: An object containing the state, including dataframes and metadata.
    - client: The OpenAI client for generating queries.
    - forecasting: A boolean indicating if forecasting-related data is included.

    Returns:
    - A ChartType object containing the type, method, and description of the visualization if needed.
    """
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

    # Generate metadata based on the forecasting flag
    if forecasting:
        metadata_df = create_metadata(session_state.df)
        metadata_forecast_df = create_metadata(session_state.forecast_df)
        retrieved_context = (
            f"Main DataFrame Metadata:\n{metadata_df}\n\n"
            f"Forecast DataFrame Metadata:\n{metadata_forecast_df}"
        )
        dataframes_description = (
            "'dataframe' represents the main dataset, while 'forecast_dataframe' represents forecasted data."
        )
    else:
        metadata_df = create_metadata(session_state.df)
        retrieved_context = f"Main DataFrame Metadata:\n{metadata_df}"
        dataframes_description = "'dataframe' represents the main dataset."

    # First system prompt to determine if visualization is necessary
    flag_format = "{\"visualisation_necessary\": flag}"
    system_prompt = (
        f"Given the prompt: `{user_input}` and the metadata below, can you determine if the response can be best represented in the form of a data visualization? "
        "The decision should be based on whether the question inherently requires a comparative or analytical response that would benefit from a visual representation, "
        "not just the availability of data. "
        f"Your response needs to be in a JSON format: {flag_format}. `visualisation_necessary` represents whether a data visualization is necessary or not with a boolean flag. "
        f"{dataframes_description}."
    )

    try:
        # First query to check if visualization is necessary
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Prompt: `{user_input}` \n Retrieved Context: `{retrieved_context}`"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "visualisation_flag",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "visualisation_necessary": {
                                "type": "boolean",
                                "description": "Indicates whether visualization is necessary or not."
                            }
                        },
                        "required": ["visualisation_necessary"],
                        "additionalProperties": False
                    }
                }
            },
            temperature=0,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        print(chat_completion.choices[0].message.content)
        if ChartFlag.model_validate_json(chat_completion.choices[0].message.content).visualisation_necessary:
            # Visualization is necessary; determine the type
            visualisation_format = "{\"Type\": chart_type, \"Method\": function(), \"Description\": description}"
            system_prompt = (
                f"Given the prompt: `{user_input}` and the metadata below, determine the best type of data visualization. "
                f"The JSON format: {visualisation_format}. \n"
                f"The list of choices for the responses are available in {json.dumps(chart_types)}. It provides the types of charts available, their corresponding methods, and descriptions. "
                f"Return the choice JSON which is most suitable. {dataframes_description}."
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Prompt: `{user_input}` \n Retrieved Context: `{retrieved_context}`"}
                ],
                model="gpt-4o",
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "visualisation_format",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "Type": {
                                    "type": "string",
                                    "description": "The type of chart, such as bar, line, pie, etc."
                                },
                                "Method": {
                                    "type": "string",
                                    "description": "A method or function that pertains to the visualization."
                                },
                                "Description": {
                                    "type": "string",
                                    "description": "A description of the visualization and its purpose."
                                }
                            },
                            "required": ["Type", "Method", "Description"],
                            "additionalProperties": False
                        }
                    }
                },
                temperature=0,
                max_completion_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            print(chat_completion.choices[0].message.content)
            return ChartType.model_validate_json(chat_completion.choices[0].message.content)
        else:
            return None
    except Exception as e:
        print(e)
        return None
