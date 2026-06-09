import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pandas.api.types import is_numeric_dtype
from scipy.stats import spearmanr
import math
import json


def safe_float(v):
    if v is None or pd.isna(v):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError, OverflowError):
        return None
    return None if math.isnan(f) else round(f, 5)


def _pair_count(a, b):
    return int((pd.notna(a) & pd.notna(b)).sum())


def _finalize(fig, title, x_title=None, y_title=None):
    fig.update_layout(
        title=title,
        height=500,
        margin={"l": 50, "r": 50, "t": 70, "b": 50},
        hovermode="closest",
        legend={"orientation": "h"},
    )
    if x_title is not None:
        fig.update_xaxes(title=x_title)
    if y_title is not None:
        fig.update_yaxes(title=y_title)
    return fig


def _dropdown(fig, buttons, active=0):
    fig.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                showactive=True,
                active=active,
                x=0.01,
                y=1.15,
                xanchor="left",
                yanchor="top",
                buttons=buttons,
            )
        ]
    )
    return fig


def _numeric_same_variable(x, col_name):
    x = pd.to_numeric(x, errors="coerce").dropna()
    count = len(x)

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=x,
            name="Histogram",
            visible=True,
            opacity=0.85,
        )
    )
    fig.add_trace(
        go.Box(
            y=x,
            name="Box",
            visible=False,
            boxmean=True,
        )
    )
    fig.add_trace(
        go.Violin(
            y=x,
            name="Violin",
            visible=False,
            box_visible=True,
            meanline_visible=True,
        )
    )

    buttons = [
        dict(
            label="Histogram",
            method="update",
            args=[
                {"visible": [True, False, False]},
                {
                    "title": f"{col_name}",
                    "xaxis": {"title": col_name, "visible": True},
                    "yaxis": {"title": "Count", "visible": True},
                },
            ],
        ),
        dict(
            label="Box",
            method="update",
            args=[
                {"visible": [False, True, False]},
                {
                    "title": f"{col_name}",
                    "xaxis": {"title": "", "visible": False},
                    "yaxis": {"title": col_name, "visible": True},
                },
            ],
        ),
        dict(
            label="Violin",
            method="update",
            args=[
                {"visible": [False, False, True]},
                {
                    "title": f"{col_name}",
                    "xaxis": {"title": "", "visible": False},
                    "yaxis": {"title": col_name, "visible": True},
                },
            ],
        ),
    ]

    _dropdown(fig, buttons, active=0)
    _finalize(fig, f"{col_name}", x_title=col_name, y_title="Count")
    return count, fig


def _numeric_numeric(x, y, x_col, y_col):
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    mask = x.notna() & y.notna()
    x = x[mask]
    y = y[mask]
    count = len(x)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="Scatter",
            visible=True,
            marker={"size": 7},
        )
    )
    fig.add_trace(
        go.Histogram2dContour(
            x=x,
            y=y,
            name="Density",
            visible=False,
            contours={"coloring": "heatmap"},
            showscale=True,
        )
    )

    buttons = [
        dict(
            label="Scatter",
            method="update",
            args=[
                {"visible": [True, False]},
                {
                    "title": f"{y_col} vs {x_col}",
                    "xaxis": {"title": x_col},
                    "yaxis": {"title": y_col},
                },
            ],
        ),
        dict(
            label="Density",
            method="update",
            args=[
                {"visible": [False, True]},
                {
                    "title": f"Density: {y_col} vs {x_col}",
                    "xaxis": {"title": x_col},
                    "yaxis": {"title": y_col},
                },
            ],
        ),
    ]

    _dropdown(fig, buttons, active=0)
    _finalize(fig, f"{y_col} vs {x_col}", x_title=x_col, y_title=y_col)
    return count, fig


def _numeric_categorical(cat, num, cat_col, num_col):
    cat = pd.Series(cat, copy=False)
    num = pd.to_numeric(num, errors="coerce")
    mask = cat.notna() & num.notna()
    cat = cat[mask]
    num = num[mask]
    count = len(num)

    if count == 0:
        fig = go.Figure()
        _finalize(fig, f"{num_col} vs {cat_col}")
        return count, fig

    means = num.groupby(cat, sort=False).mean()
    order = means.index.tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Box(
            x=cat,
            y=num,
            name="Box",
            visible=True,
        )
    )
    fig.add_trace(
        go.Violin(
            x=cat,
            y=num,
            name="Violin",
            visible=False,
            box_visible=True,
            meanline_visible=True,
        )
    )
    fig.add_trace(
        go.Bar(
            x=means.index.tolist(),
            y=means.values.tolist(),
            name="Mean",
            visible=False,
        )
    )

    buttons = [
        dict(
            label="Box",
            method="update",
            args=[
                {"visible": [True, False, False]},
                {
                    "title": f"{num_col} by {cat_col}",
                    "xaxis": {"title": cat_col, "categoryorder": "array", "categoryarray": order},
                    "yaxis": {"title": num_col},
                },
            ],
        ),
        dict(
            label="Violin",
            method="update",
            args=[
                {"visible": [False, True, False]},
                {
                    "title": f"{num_col} by {cat_col}",
                    "xaxis": {"title": cat_col, "categoryorder": "array", "categoryarray": order},
                    "yaxis": {"title": num_col},
                },
            ],
        ),
        dict(
            label="Mean Bar",
            method="update",
            args=[
                {"visible": [False, False, True]},
                {
                    "title": f"Mean {num_col} by {cat_col}",
                    "xaxis": {"title": cat_col, "categoryorder": "array", "categoryarray": order},
                    "yaxis": {"title": f"Mean {num_col}"},
                },
            ],
        ),
    ]

    _dropdown(fig, buttons, active=0)
    _finalize(fig, f"{num_col} by {cat_col}", x_title=cat_col, y_title=num_col)
    return count, fig


def _mosaic_categorical_categorical(x, y, x_col, y_col):
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    count = len(df)

    ct = pd.crosstab(df["x"], df["y"])
    if ct.empty:
        fig = go.Figure()
        _finalize(fig, f"{y_col} vs {x_col}")
        return count, fig

    row_totals = ct.sum(axis=1)
    total = row_totals.sum()

    # color palette for y-levels
    palette = px.colors.qualitative.Plotly
    y_levels = ct.columns.tolist()
    color_map = {lvl: palette[i % len(palette)] for i, lvl in enumerate(y_levels)}

    fig = go.Figure()

    # Use invisible dummy traces for legend
    for lvl in y_levels:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker={"size": 12, "color": color_map[lvl]},
                name=str(lvl),
                showlegend=True,
                visible=True,
            )
        )

    shapes = []
    annotations = []

    x_left = 0.0
    x_names = ct.index.tolist()

    for x_lvl in x_names:
        x_width = row_totals.loc[x_lvl] / total if total > 0 else 0
        row = ct.loc[x_lvl]
        row_total = row.sum()

        y_bottom = 0.0
        for y_lvl in y_levels:
            cell = row[y_lvl]
            h = (cell / row_total) if row_total > 0 else 0

            shapes.append(
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=x_left,
                    x1=x_left + x_width,
                    y0=y_bottom,
                    y1=y_bottom + h,
                    line={"color": "white", "width": 1},
                    fillcolor=color_map[y_lvl],
                )
            )

            if cell > 0:
                annotations.append(
                    dict(
                        x=x_left + x_width / 2,
                        y=y_bottom + h / 2,
                        xref="paper",
                        yref="paper",
                        text=str(int(cell)),
                        showarrow=False,
                        font={"size": 11, "color": "white"},
                    )
                )

            y_bottom += h

        annotations.append(
            dict(
                x=x_left + x_width / 2,
                y=-0.06,
                xref="paper",
                yref="paper",
                text=str(x_lvl),
                showarrow=False,
                font={"size": 11},
            )
        )

        x_left += x_width

    annotations.append(
        dict(
            x=-0.03,
            y=0.5,
            xref="paper",
            yref="paper",
            text=y_col,
            textangle=-90,
            showarrow=False,
            font={"size": 11},
        )
    )

    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        title=f"Mosaic: {y_col} vs {x_col}",
        xaxis={"visible": False, "range": [0, 1]},
        yaxis={"visible": False, "range": [0, 1]},
        height=500,
        margin={"l": 60, "r": 30, "t": 80, "b": 80},
        legend={"orientation": "h"},
    )

    return count, fig


def two_variable(file_path: str, x_col: str, y_col: str):
    """
    Returns:
        (x_col, y_col, count, figure_json)
    """
    df = pd.read_csv(file_path)

    if x_col not in df.columns or y_col not in df.columns:
        raise KeyError(f"Missing column: {x_col} or {y_col}")

    x = df[x_col]
    y = df[y_col]

    x_is_num = is_numeric_dtype(x)
    y_is_num = is_numeric_dtype(y)

    if x_col == y_col:
        if x_is_num:
            count, fig = _numeric_same_variable(x, x_col)
        else:
            # Same categorical variable: a count bar chart is usually more useful
            counts = x.dropna().value_counts(sort=False)
            count = int(counts.sum())

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=counts.index.tolist(),
                        y=counts.values.tolist(),
                        name="Count",
                    )
                ]
            )
            _finalize(fig, f"{x_col}", x_title=x_col, y_title="Count")

        figure = json.loads(fig.to_json())
        return x_col, y_col, count, figure

    if x_is_num and y_is_num:
        count, fig = _numeric_numeric(x, y, x_col, y_col)
        figure = json.loads(fig.to_json())
        return x_col, y_col, count, figure

    if x_is_num and not y_is_num:
        # flip so categorical is on x-axis
        count, fig = _numeric_categorical(y, x, y_col, x_col)
        figure = json.loads(fig.to_json())
        return x_col, y_col, count, figure

    if not x_is_num and y_is_num:
        count, fig = _numeric_categorical(x, y, x_col, y_col)
        figure = json.loads(fig.to_json())
        return x_col, y_col, count, figure

    count, fig = _mosaic_categorical_categorical(x, y, x_col, y_col)
    figure = json.loads(fig.to_json())
    return x_col, y_col, count, figure