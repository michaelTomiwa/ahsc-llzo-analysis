# =========================================================
# AHSC vs LLZO Analysis (FROM CSV FILES)
# Includes:
# - summaries
# - statistical comparison
# - plots
# - Random Forest model (replacement for PD model)
# =========================================================

# ---------------------------
# 1. Install & load packages
# ---------------------------
packages <- c("readr", "dplyr", "ggplot2", "randomForest", "stringr")

installed <- rownames(installed.packages())
for (p in packages) {
  if (!(p %in% installed)) install.packages(p)
}

library(readr)
library(dplyr)
library(ggplot2)
library(randomForest)
library(stringr)

# ---------------------------
# 2. Load your CSV files
# ---------------------------
ahsc <- read_csv("ahsc_cleaned.csv")
llzo <- read_csv("llzo_cleaned.csv")

ahsc$Dataset <- "AHSC"
llzo$Dataset <- "LLZO"

combined <- bind_rows(ahsc, llzo)

# ---------------------------
# 3. Create folders
# ---------------------------
if (!dir.exists("results")) dir.create("results")
if (!dir.exists("plots")) dir.create("plots")

# ---------------------------
# 4. Summary statistics
# ---------------------------
summary_stats <- combined %>%
  group_by(Dataset) %>%
  summarise(
    Potential_mean = mean(Potential_Window_V, na.rm = TRUE),
    Capacitance_mean = mean(Capacitance_or_Capacity, na.rm = TRUE),
    Stability_mean = mean(Cycling_Stability_percent, na.rm = TRUE),
    Conductivity_mean = mean(Ionic_Conductivity_numeric, na.rm = TRUE)
  )

write_csv(summary_stats, "results/summary_stats.csv")

# ---------------------------
# 5. Statistical comparison
# ---------------------------
wilcox_results <- list()

vars <- c("Potential_Window_V",
          "Capacitance_or_Capacity",
          "Cycling_Stability_percent",
          "Ionic_Conductivity_numeric")

for (v in vars) {
  test <- wilcox.test(combined[[v]] ~ combined$Dataset)
  
  wilcox_results[[v]] <- data.frame(
    Variable = v,
    p_value = test$p.value
  )
}

wilcox_df <- bind_rows(wilcox_results)
write_csv(wilcox_df, "results/wilcoxon_tests.csv")

# ---------------------------
# 6. Boxplots
# ---------------------------
for (v in vars) {
  p <- ggplot(combined, aes(x = Dataset, y = .data[[v]], fill = Dataset)) +
    geom_boxplot() +
    theme_minimal() +
    labs(title = paste(v, "Comparison"))
  
  ggsave(paste0("plots/", v, "_boxplot.png"), p)
}

# ---------------------------
# 7. Histograms
# ---------------------------
for (v in vars) {
  p <- ggplot(combined, aes(x = .data[[v]], fill = Dataset)) +
    geom_histogram(alpha = 0.5, bins = 30) +
    facet_wrap(~Dataset) +
    theme_minimal()
  
  ggsave(paste0("plots/", v, "_hist.png"), p)
}

# ---------------------------
# 8. RANDOM FOREST MODEL (AHSC)
# ---------------------------
if ("Specific_Power_W_kg" %in% names(ahsc)) {
  
  model_data <- ahsc %>%
    select(Specific_Power_W_kg,
           Potential_Window_V,
           Capacitance_or_Capacity,
           Cycling_Stability_percent,
           Ionic_Conductivity_numeric) %>%
    na.omit()
  
  set.seed(123)
  
  train_index <- sample(1:nrow(model_data), 0.8*nrow(model_data))
  train <- model_data[train_index, ]
  test  <- model_data[-train_index, ]
  
  rf_model <- randomForest(
    Specific_Power_W_kg ~ .,
    data = train,
    ntree = 500,
    importance = TRUE
  )
  
  # Predictions
  pred <- predict(rf_model, test)
  
  # Metrics
  rmse <- sqrt(mean((test$Specific_Power_W_kg - pred)^2))
  r2 <- cor(test$Specific_Power_W_kg, pred)^2
  
  metrics <- data.frame(RMSE = rmse, R2 = r2)
  write_csv(metrics, "results/rf_metrics.csv")
  
  # Importance plot
  png("plots/rf_importance.png")
  varImpPlot(rf_model)
  dev.off()
  
  # Predicted vs observed
  p <- ggplot(data.frame(obs=test$Specific_Power_W_kg, pred=pred),
              aes(x=obs, y=pred)) +
    geom_point() +
    geom_abline(slope=1, intercept=0, linetype="dashed") +
    theme_minimal()
  
  ggsave("plots/rf_pred_vs_obs.png", p)
}

# ---------------------------
# 9. Save combined dataset
# ---------------------------
write_csv(combined, "results/combined_data.csv")

cat("Analysis complete. Check results/ and plots/ folders.")

