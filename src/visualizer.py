import numpy as np
import pandas as pd
import igraph as ig
from pyvis.network import Network
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

SIMILARITY_THRESHOLD = 0.5


def get_edge_color(score, min_val=0.50, max_val=0.90):
    """Single-score version, kept for external compatibility."""
    relative_score = max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))
    r = int(200 * relative_score)
    g = int(200 * (1 - relative_score))
    b = int(200 * (1 - relative_score))
    return f"#{r:02x}{g:02x}{b:02x}"


def _get_edge_colors_vectorized(scores: np.ndarray, min_val=0.50, max_val=0.90) -> list[str]:
    """Compute hex color strings for an entire array of scores at once."""
    relative = np.clip((scores - min_val) / (max_val - min_val), 0.0, 1.0)
    r = (200 * relative).astype(np.uint8)
    # green and blue channels are mirrored
    gb = (200 * (1.0 - relative)).astype(np.uint8)
    return [f"#{ri:02x}{gbi:02x}{gbi:02x}" for ri, gbi in zip(r, gb)]


def build_igraph_graph(file_path, threshold=SIMILARITY_THRESHOLD, max_len=1000):
    print("Step 1: Loading data...")
    df = pd.read_csv(file_path).head(max_len)

    node_id_col = df.columns[0]
    print("Node ID:", node_id_col)
    df = df.set_index(node_id_col)

    print("Step 2: Preprocessing...")
    df_numeric = df.select_dtypes(include=[np.number]).copy().dropna()

    if df_numeric.empty:
        raise ValueError("No numeric data available after preprocessing.")

    scaler = StandardScaler()
    normalized_data = scaler.fit_transform(df_numeric)

    print("Step 3: Calculating similarity matrix...")
    similarity_matrix = cosine_similarity(normalized_data)

    node_ids = df_numeric.index.astype(str).tolist()
    n = len(node_ids)

    print("Step 4: Building igraph graph...")

    # --- Vectorized edge extraction (replaces O(n²) Python loop) ---
    # Get flat indices for the upper triangle (i < j pairs only)
    i_idx, j_idx = np.triu_indices(n, k=1)
    scores = similarity_matrix[i_idx, j_idx]          # all upper-tri scores at once

    mask = scores >= threshold                          # boolean filter, no Python loop
    rows = i_idx[mask]
    cols = j_idx[mask]
    edge_scores = scores[mask].astype(np.float64)

    edges = list(zip(rows.tolist(), cols.tolist()))
    weights = edge_scores.tolist()
    widths = [5.0] * len(edges)
    colors = _get_edge_colors_vectorized(edge_scores, min_val=0.50, max_val=0.65)
    titles = [f"Similarity: {s:.2f}" for s in edge_scores]   # unavoidably a loop, but fast

    g = ig.Graph()
    g.add_vertices(n)
    g.vs["name"] = node_ids
    g.vs["label"] = node_ids

    if edges:
        g.add_edges(edges)
        g.es["weight"] = weights
        g.es["width"] = widths
        g.es["color"] = colors
        g.es["title"] = titles

    print(f"Graph built: {g.vcount()} nodes and {g.ecount()} edges.")
    return g


def igraph_to_pyvis(g, output_filename):
    print("Step 5: Generating visualization...")

    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

    node_names = g.vs["name"]
    node_labels = g.vs["label"]
    for name, label in zip(node_names, node_labels):
        net.add_node(name, label=label, title=name)

    # Resolve edge attributes once, outside the loop
    edge_attrs = set(g.edge_attributes())
    ec = g.ecount()

    weights = g.es["weight"] if "weight" in edge_attrs else [1.0] * ec
    widths  = g.es["width"]  if "width"  in edge_attrs else [1.0] * ec
    colors  = g.es["color"]  if "color"  in edge_attrs else ["#cccccc"] * ec
    titles  = g.es["title"]  if "title"  in edge_attrs else [""] * ec

    # Single call to get all (source, target) index pairs
    edgelist = g.get_edgelist()

    for (src, tgt), w, wd, c, t in zip(edgelist, weights, widths, colors, titles):
        net.add_edge(
            node_names[src],
            node_names[tgt],
            value=float(w),
            width=float(wd),
            color=c,
            title=t,
        )

    net.show_buttons(filter_=["physics"])
    net.save_graph(output_filename)
    return output_filename


def main(file_path, output_filename):
    g = build_igraph_graph(file_path)
    return igraph_to_pyvis(g, output_filename)


if __name__ == "__main__":
    main("healthcare.csv", "output_graph.html")