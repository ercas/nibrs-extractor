# example file showing how to load data with labels

library(Hmisc)

df <- read.csv("processed/PART1.csv") %>%
labels <- read.csv("processed/PART1-labels.csv")

label(df) <- as.list(
  merge(
    data.frame(VARIABLE = colnames(df)),
    labels,
    by = "VARIABLE",
    all.x = TRUE
  )$LABEL
)

df
