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
    categoric_data = prep["categoric_data"]
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
                value = eta(categoric_data[var_j], numeric_data[var_i])

            elif type_i == "categorical" and type_j == "numeric":
                value = eta(categoric_data[var_i], numeric_data[var_j])

            elif type_i == "categorical" and type_j == "categorical":
                value = cramers_v(categoric_data[var_i], categoric_data[var_j])

            else:
                value = np.nan

            correlation_matrix[i][j] = value
            correlation_matrix[j][i] = value

    values =[[safe_float(v) for v in row] for row in correlation_matrix]
    return correlation_matrix, columns, values


def numerical_stats_table(file_path: str):
    """
    Output: summary table of descriptive statistics for each numerical variable
    """
    print("Stats Table for file:", file_path)
    print("Step 1: Loading data...")
    df = pd.read_csv(file_path)
    prep = prepare_frame(df)

    print("Step 2: Preprocessing...")
    columns = prep["columns"]
    numeric_cols = prep["numeric_cols"]
    numeric_data = prep["numeric_data"]

    print("Step 3: Calculating Numerical Statistics Table...")
    q = numeric_data.quantile([0.10, 0.25, 0.75, 0.90])
    stats_matrix= pd.DataFrame()
    stats_matrix["count"] = numeric_data.count().astype(int)
    stats_matrix["mean"] = numeric_data.mean()
    stats_matrix["var"] = numeric_data.var()
    stats_matrix["std dev"] = numeric_data.std()
    stats_matrix["range"] = numeric_data.max() - numeric_data.min()
    stats_matrix["min"] = numeric_data.min()
    stats_matrix["p10"] = q.loc[0.10]
    stats_matrix["p25"] = q.loc[0.25]
    stats_matrix["median"] = numeric_data.median()
    stats_matrix["p75"] = q.loc[0.75]
    stats_matrix["p90"] = q.loc[0.90]
    stats_matrix["max"] = numeric_data.max()
    stats_matrix["skew"] = numeric_data.skew()
    stats_matrix["kurt"] = numeric_data.kurt()

    print("Step 4: Returning Statistics Table...")
    values = [[safe_float(v) for v in row] for row in stats_matrix.transpose().to_numpy().tolist()]
    return stats_matrix, numeric_cols, values


# def categorical_stats_table(file_path: str):
#     """
#     Output: summary table of descriptive statistics for each numerical variable
#     """
#     print("Stats Table for file:", file_path)
#     print("Step 1: Loading data...")
#     df = pd.read_csv(file_path)
#     prep = prepare_frame(df)

#     print("Step 2: Preprocessing")
#     categoric_data = prep["categoric_data"]

#     print("Step 3: Calculating Categorical Statistics Table...")
#     return


if __name__ == "__main__":
    # correlation_matrix, columns, values = heatmap("student_data.csv")
    # print(correlation_matrix)
    numerical_stats_table("student_data.csv")