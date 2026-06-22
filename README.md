# Statistical Analysis Project

## How to use:

to use, clone the repo and download the required dependencies:

`pip install pandas numpy flask scikit-learn scipy igraph`

i think that's it and then those packages will install like 20 more because that's what they do.

anyways if it works you can run

`flask --app app.py run`

and then go to the link it gives you (for me, 127.0.0.1:5500) and drag-and-drop a .csv file and then bam.

it will give you:

1. A heatmap / matrix of correlation values across numerical and categorical data for 2-variable analysis
2. A bunch of 1-variable data for each numerical column (haven't added categorical analysis yet).

## Heatmap:

the correlations work as follows:

- Numerical vs Numerical -> use Spearman's r
- Numerical vs Categorical -> use the Eta Coefficient
- Categorical vs Categorical -> use Cramer's (biased) V

i still have yet to add more correlation analysis, like making Cramer's V unbiased unless it is Binary vs Binary categorical data.

if you click on a cell in the heatmap, it will draw some graphs depending on the type of data

- On the Diagonal (one variable) -> draws a histogram for the variable
- Numerical vs Numerical -> probably a Scatterplot and Density Plot
- Numerical vs Categorical -> Bar Chart and Violin Plot and some other thing
- Categorical vs Categorical -> Mosaic Plot

# Numerical Data Table
for the 1-variable table of statistics (which only works for numerical data so far...), here's what it gives:

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

the last two values are just things that Pandas can do so i added them but i don't know the statistical theory behind them lol.

# TODO:

I still want to make some improvements:
1. Categorical data table
2. Add Cramer's Unbiased V for the proper data
3. Investigate other correlation types (Kendall's Tau, etc.)
4. Make it look less HIDEOUS
5. Add a dedicated Variable 1 vs. Variable 2 section that has more than just what each heatmap cell has
    - like the other correlation types
    - like bigger graphs and list descriptive stats for each variable
    - stuff like that