# Part 2 - Q&A Notes

* remove redundant/unnecessary features
  * if correlation is low -> just remove feature (fine for project)
  * not only linear
  * 10 features might lead to really good result -> reverse engineer their generation
  * we have not data leakage in project
  * golden tipps:
    * something highly predicive
    * find out its correlations
* combine/transform features
  * better to generalize/learn for model
  * new features e.g. from date new col with is_weekday
* goal
  * more efficient
  * interpretability
* analyse
  * pairgrid/correlation matrix plot
* models
  * randomforest can select important featues
    * others might be influenced by noise in data (e.g. NN)
    * if CMAR, imputation not important -> otherwise not
  * tensorflow for more flexibility
  * XGBoost
    * can use categorical (must be configured)
    * feature scaling does not improve performance
  * check out a few different models for project
    * a tree, a simple, ...
    * why I would want to use a specific model -> reason (explainability, accuracy, simplicity, ...)
    * not highest accuracy needed
  * mlpregression (nn)
* burnout features
  * risk_level did most of the prediction work (check in random forest)
  * suspicious -> probably estimated after diagnosis -> label leakage
  * high correlation
  * after removal -> prediction got worse
* tabpfn
* important for exercise:
  * baselines!!!
  * which models did we try
  * how did we evaluate
