import pandas as pd
import numpy as np
from stats_utils import *


def heatmap(file_path: str):
    """
    Output: an n x n matrix of correlation metrics for each pair of variables
    """
    print("Heatmap for file:", file_path)
    print("\nStep 1: Loading data...")
    df = pd.read_csv(file_path)
    prep = prepare_frame(df)
    
    print("\nStep 2: Preprocessing...")
    # currently segregating data by numeric vs non-numeric
    columns = prep["columns"]
    column_types = prep["column_types"]
    numeric_data = prep["numeric_data"]
    categorical_data = prep["categorical_data"]
    skipped_cols = prep["skipped_cols"]

    n = len(columns)
    correlation_matrix = np.full((n, n), np.nan, dtype=float)

    for i, var_i in enumerate(columns):
        type_i = column_types[var_i]

        for j in range(i, n):
            var_j = columns[j]
            type_j = column_types[var_j]

            if var_i == var_j:
                value = 1.0

            elif type_i == "skipped" or type_j == "skipped":
                value = 0.0

            elif type_i == "numeric" and type_j == "numeric":
                value = spearman(numeric_data[var_i], numeric_data[var_j])

            elif type_i == "numeric" and type_j == "categorical":
                value = eta(categorical_data[var_j], numeric_data[var_i])

            elif type_i == "categorical" and type_j == "numeric":
                print("x", var_i, categorical_data[var_i])
                print("y", var_j, numeric_data[var_j])
                value = eta(categorical_data[var_i], numeric_data[var_j])

            elif type_i == "categorical" and type_j == "categorical":
                value = cramers_v(categorical_data[var_i], categorical_data[var_j])

            else:
                value = np.nan

            correlation_matrix[i][j] = value
            correlation_matrix[j][i] = value

    values =[[safe_float(v) for v in row] for row in correlation_matrix]
    return correlation_matrix, columns, values


def stats_table(file_path: str):
    """
    Output: summary table of descriptive statistics for each (numerical) variable
    """

    print("Stats Table for file:", file_path)
    print("Step 1: Loading data...")
    df = pd.read_csv(file_path)

    print("Step 2: Preprocessing...")
    # again, segregate the numeric and non-numeric
    df_numeric = df.select_dtypes(include=[np.number]).copy()
    df_catagoric = df.select_dtypes(exclude=[np.number]).copy()

    print("Step 3: Calculating Statistics Table...")
    def ptp(x: pd.Series): return x.max() - x.min()
    def p10(x: pd.Series): return x.quantile(0.10)
    def p25(x: pd.Series): return x.quantile(0.25)
    def p75(x: pd.Series): return x.quantile(0.75)
    def p90(x: pd.Series): return x.quantile(0.90)
    def mode(x: pd.Series): return x.mode()[0]
    stats_matrix = df_numeric.agg(
        [
            "count",
            "mean",
            "var",
            "std",
            ptp,
            "min",
            p10,
            p25,
            "median",
            p75,
            p90,
            "max",
            "skew",
            "kurt"
        ]
    )
    columns = stats_matrix.columns.tolist()
    values = [[safe_float(v) for v in row] for row in stats_matrix.values.tolist()]

    print("Step 4: Returning Statistics Table...")
    return (stats_matrix, columns, values)



if __name__ == "__main__":
    correlation_matrix, columns, values = heatmap("student_data.csv")
    print(correlation_matrix)
    # stats_table("healthcare.csv")