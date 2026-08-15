
***
# Statistics API Project (The Old Version)
***

# Introduction

This codebase is my first attempt at making a statistical analysis API. I was mainly hoping for the project to have lots of ways to visualize the data, but it didn't end up being quite as good as I'd hoped. Still, I'll keep this repository alive and public, and I'll try to clean it up as well. This project includes:

1. A Data Visualization tool
2. A Heatmap
3. A Numerical Data Table

***
# Usage

### Local Setup:

1. Clone the API: `git clone https://github.com/Matthew07/Statistics-API` and `cd Statistics-API`
2. Make virtual environment: `python -m venv venv` or `uv venv`
3. Install dependencies `pip install -r requirements.txt` or `uv pip install -r requirements.txt`
4. Start server `flask --app app.py run`

### Data Visualizer:

This tool is really not that cool - it just puts all observations in a graph and positions them by similarity. It's also really laggy and can't scale up well at all. If you try to use it, you might end up waiting for quite a bit.

### Heatmap:

The Heatmap is just an $n \times n$ grid with certain correlation values between all pairs of data. Because there can be *numerical* and *categorical* data, the default correlation statistics are:

1. *Numeric vs Numeric*: **Spearman's $r$**
2. *Numeric vs Categoric*: **The Eta Coefficient**
3. *Categoric vs Categoric*: **Cramer's Biased $V$**

I still have yet to add more correlation analysis, like making Cramer's V unbiased unless it is Binary vs Binary categorical data. 

One good feature with this old API is that when you click on a cell in the Heatmap, it will create graphs for the data depending on what type of cell it is:

- *On the Diagonal (one variable)* -> **Histogram**
- *Numeric vs Numeric* -> **Scatterplot** and **Density Plot**
- *Numeric vs Categoric* -> **Bar Chart** and **Violin Plot**
- *Categoric vs Categoric* -> **Mosaic Plot**

### Numerical Data Table:

For all numerical variables, the following statistics will be computed:

1. Count
2. Mean
3. Variance
4. Standard Deviation
5. Range
6. Minimum
7. 10th Percentile
8. 25th Percentile
9. Median
10. 75th Percentile
11. 90th Percentile
12. Maximum
13. Skewness (idk)
14. Kurtois (idk)

***
# Future Improvements

### Categorical Data Table

There's one for the *numerical* variables, but not for the *categorical* variables. 

### Other Statistics:

Adding more correlations like *Kendall's Tau* would be helpful.

***
## The End!