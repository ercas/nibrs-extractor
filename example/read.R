# example file showing how to load data with labels

library(Hmisc)

df <- read.csv("processed/PART1.csv.gz")
labels <- read.csv("processed/PART1-labels.csv.gz")

label(df) <- as.list(
  merge(
    data.frame(VARIABLE = colnames(df)),
    labels,
    by = "VARIABLE",
    all.x = TRUE
  )$LABEL
)

df
