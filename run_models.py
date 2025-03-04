#!/bin/bash

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score
from sklearn.datasets import dump_svmlight_file
from random import randint
import pyltr


def elastic_net_model(X_train, y_train, X_test, y_test):
    regr = ElasticNet(random_state=0, alpha=0.00001, l1_ratio=0.2)
    trained_model_en = regr.fit(X_train, y_train)
    y_pred_enet = trained_model_en.predict(X_test)
    r2_score_enet = r2_score(y_test, y_pred_enet)
    print("r^2 on test data : %f" % r2_score_enet)


def store_output(Epred_r, new_test_set):
    predictions_df = pd.DataFrame(Epred_r)
    submiss_test_set = pd.DataFrame(new_test_set["srch_id"])
    submiss_test_set.columns = ["srch_id"]
    submiss_test_set["ranking"] = predictions_df
    submiss_test_set["prop_id"] = new_test_set["prop_id"]
    # Group by search id and sort by ranking!
    print("\nSorting the ranking...\n")
    test_set_submission_result = submiss_test_set.groupby(["srch_id"]).apply(
        lambda x: x.sort_values(["ranking"], ascending=False)).reset_index(drop=True)
    print("\nStore the predictions...\n")
    test_set_submission_result = test_set_submission_result.drop("ranking", axis=1)
    # store the file to submit!
    test_set_submission_result.to_csv("RESULT_to_submit.csv", index=False)


def lambda_mart(Train_features, Train_scores, Train_qids, Val_features, Val_scores, Val_qids, stop, num_estim):
   
    metric = pyltr.metrics.NDCG(k=5)
    monitor = pyltr.models.monitors.ValidationMonitor(Val_features, Val_scores, Val_qids, metric=metric,
                                                      stop_after=stop)
    model = pyltr.models.LambdaMART(
        metric=metric,
        n_estimators=num_estim,
        max_features=0.5,
        learning_rate=0.02,
        query_subsample=0.5,
        max_leaf_nodes=10,
        min_samples_leaf=64,
        verbose=1,
    )
    # fit lambdaMART
    model.fit(Train_features, Train_scores, Train_qids, monitor=monitor)
    return model


def main():
    print("Open the files...")
    # import the train and validation set in the SVMlight format
    full_train = open("C://Users//Dennis//Documents//Bioinformatics//Data_mining//Data_mining_assignment_2//Secondattempt//Full_train_lm_split.txt")
    full_valid = open("C://Users//Dennis//Documents//Bioinformatics//Data_mining//Data_mining_assignment_2//Secondattempt//Full_validation_lm_split.txt")
    full_test = open("C://Users//Dennis//Documents//Bioinformatics//Data_mining//Data_mining_assignment_2//Secondattempt//Preprocessed_test_set.txt")

    # load test set in normal format
    print("Load the normal test set...")
    path = "C://Users//Dennis//Documents//Bioinformatics//Data_mining//Data_mining_assignment_2//Secondattempt//"
    new_test_set = pd.read_csv(path + "/New_test_set_full.csv")
    new_test_set = new_test_set.drop(["Unnamed: 0"], axis=1)

    # split in scores, feature and search_ids
    print("Load the SVMlight train set...")
    Train_features, Train_scores, Train_qids, _ = pyltr.data.letor.read_dataset(full_train)
    print("Load the SVMlight validation set...")
    Val_features, Val_scores, Val_qids, _ = pyltr.data.letor.read_dataset(full_valid)
    print("Load the SVMlight test set...")
    Test_features_r, Test_scores_r, Test_qids_r, _ = pyltr.data.letor.read_dataset(full_test)

    full_test.close()
    full_train.close()
    full_valid.close()

    # PARAMETERS of LambdaMART
    stop = 100  # after how many equal score (no imporvement) stop
    num_estimators = 2000  # number of trees to use. HIGHER it is LONGER IT takes to run the script

    print("\nStart training of LambdaMART...\n")
    trained_model = lambda_mart(Train_features, Train_scores, Train_qids, Val_features, Val_scores, Val_qids, stop,
                                num_estimators)
    # predict scores for ranking
    print("\nMaking the predictions...\n")
    Epred_test = trained_model.predict(Test_features_r)
    # store the prediction to file
    store_output(Epred_test, new_test_set)
    print("Feature importances: \n")
    print(trained_model.feature_importances_)
    print("Estimators fitted: \n")
    print(trained_model.estimators_fitted_)


if __name__ == "__main__":
    main()
