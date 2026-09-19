import os

import numpy as np
import pandas as pd
import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Input,
    LSTM,
    Dense,
    Dropout,
    TimeDistributed
)
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau
)
from tensorflow.keras.optimizers import Adam

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from utils import (
    DATASET_PATH,
    MODEL_PATH,
    FEATURE_COLUMNS,
    load_dataset,
    clean_dataset,
    create_sequences,
    fit_scaler,
    transform_sequences,
    save_scaler,
    save_feature_information,
    save_threshold
)


# ============================================================
# SETTINGS
# ============================================================

RANDOM_STATE = 42

EPOCHS = 30

BATCH_SIZE = 32

THRESHOLD = 0.50


# ============================================================
# REPRODUCIBILITY
# ============================================================

np.random.seed(RANDOM_STATE)

tf.random.set_seed(RANDOM_STATE)


# ============================================================
# DISPLAY HEADER
# ============================================================

print("\n")
print("=" * 70)
print("                 ENDOCARE - LSTM TRAINING")
print("=" * 70)


# ============================================================
# STEP 1 - LOAD DATASET
# ============================================================

print("\n")
print("=" * 70)
print("STEP 1 - Loading Dataset")
print("=" * 70)

df = load_dataset(
    DATASET_PATH
)


print("\n")
print("=" * 70)
print("First 5 Rows of Dataset")
print("=" * 70)

print(
    df.head()
)


print("\nDataset Shape:")

print(
    df.shape
)


# ============================================================
# STEP 2 - CLEAN DATASET
# ============================================================

print("\n")
print("=" * 70)
print("STEP 2 - Cleaning Dataset")
print("=" * 70)

df = clean_dataset(
    df
)


print("\nCleaned Dataset Shape:")

print(
    df.shape
)


# ============================================================
# STEP 3 - CREATE 5 MONTH SEQUENCES
# ============================================================

print("\n")
print("=" * 70)
print("STEP 3 - Creating 5-Month LSTM Sequences")
print("=" * 70)

X, y, patient_ids = create_sequences(
    df
)


print("\nFinal sequence information:")

print(
    "X shape:",
    X.shape
)

print(
    "y shape:",
    y.shape
)


# ============================================================
# STEP 4 - PATIENT LEVEL TRAIN / VALIDATION / TEST SPLIT
# ============================================================

print("\n")
print("=" * 70)
print("STEP 4 - Patient-Level Data Split")
print("=" * 70)


# One label per patient is required for stratification.
#
# We use the patient's majority diagnosis only for
# splitting the data.
#
# The actual LSTM still learns all 5 monthly labels.

patient_split_labels = (
    y.mean(axis=1) >= 0.50
).astype(int)


# First:
# 80% temporary
# 20% test

(
    X_temp,
    X_test,
    y_temp,
    y_test,
    ids_temp,
    ids_test,
    split_labels_temp,
    split_labels_test
) = train_test_split(

    X,
    y,
    patient_ids,
    patient_split_labels,

    test_size=0.20,

    random_state=RANDOM_STATE,

    stratify=patient_split_labels
)


# From remaining 80%:
# 75% training
# 25% validation
#
# Final:
# 60% train
# 20% validation
# 20% test

(
    X_train,
    X_val,
    y_train,
    y_val,
    ids_train,
    ids_val,
    split_labels_train,
    split_labels_val
) = train_test_split(

    X_temp,
    y_temp,
    ids_temp,
    split_labels_temp,

    test_size=0.25,

    random_state=RANDOM_STATE,

    stratify=split_labels_temp
)


print(
    "\nTraining patients:",
    len(X_train)
)

print(
    "Validation patients:",
    len(X_val)
)

print(
    "Testing patients:",
    len(X_test)
)


# ============================================================
# STEP 5 - SCALE DATA
# ============================================================

print("\n")
print("=" * 70)
print("STEP 5 - Feature Scaling")
print("=" * 70)


X_train_scaled, scaler = fit_scaler(
    X_train
)

X_val_scaled = transform_sequences(
    X_val,
    scaler
)

X_test_scaled = transform_sequences(
    X_test,
    scaler
)


print(
    "Feature scaling completed."
)


# Save scaler

save_scaler(
    scaler
)

save_feature_information()

save_threshold(
    THRESHOLD
)


# ============================================================
# STEP 6 - CREATE LSTM MODEL
# ============================================================

print("\n")
print("=" * 70)
print("STEP 6 - Creating LSTM Model")
print("=" * 70)


number_of_features = len(
    FEATURE_COLUMNS
)


model = Sequential([

    Input(
        shape=(
            5,
            number_of_features
        )
    ),

    LSTM(
        32,
        return_sequences=True
    ),

    Dropout(
        0.20
    ),

    LSTM(
        16,
        return_sequences=True
    ),

    Dropout(
        0.20
    ),

    TimeDistributed(
        Dense(
            1,
            activation="sigmoid"
        )
    )
])


model.compile(

    optimizer=Adam(
        learning_rate=0.001
    ),

    loss="binary_crossentropy",

    metrics=[
        "accuracy"
    ]
)


print("\nModel architecture:")

model.summary()


# ============================================================
# STEP 7 - TRAIN MODEL
# ============================================================

print("\n")
print("=" * 70)
print("STEP 7 - Training Model")
print("=" * 70)


early_stopping = EarlyStopping(

    monitor="val_loss",

    patience=6,

    restore_best_weights=True
)


reduce_lr = ReduceLROnPlateau(

    monitor="val_loss",

    factor=0.5,

    patience=3,

    min_lr=0.00001
)


history = model.fit(

    X_train_scaled,

    y_train[..., np.newaxis],

    validation_data=(

        X_val_scaled,

        y_val[..., np.newaxis]

    ),

    epochs=EPOCHS,

    batch_size=BATCH_SIZE,

    callbacks=[

        early_stopping,

        reduce_lr

    ],

    verbose=1
)


# ============================================================
# STEP 8 - SAVE MODEL
# ============================================================

print("\n")
print("=" * 70)
print("STEP 8 - Saving Model")
print("=" * 70)


model.save(
    MODEL_PATH
)


print(
    f"\nLSTM model saved successfully as:"
)

print(
    MODEL_PATH
)


# ============================================================
# STEP 9 - TEST MODEL
# ============================================================

print("\n")
print("=" * 70)
print("STEP 9 - Testing Model")
print("=" * 70)


test_predictions = model.predict(
    X_test_scaled,
    verbose=0
)


# Shape:
# (patients, 5, 1)

test_probabilities = (
    test_predictions.squeeze(-1)
)


test_month_predictions = (
    test_probabilities >= THRESHOLD
).astype(int)


# ============================================================
# MONTH-LEVEL EVALUATION
# ============================================================

y_test_flat = y_test.reshape(-1)

pred_test_flat = (
    test_month_predictions.reshape(-1)
)


monthly_accuracy = accuracy_score(
    y_test_flat,
    pred_test_flat
)

monthly_precision = precision_score(
    y_test_flat,
    pred_test_flat,
    zero_division=0
)

monthly_recall = recall_score(
    y_test_flat,
    pred_test_flat,
    zero_division=0
)

monthly_f1 = f1_score(
    y_test_flat,
    pred_test_flat,
    zero_division=0
)


print("\n")
print("=" * 70)
print("MONTH-LEVEL RESULTS")
print("=" * 70)

print(
    f"Accuracy  : {monthly_accuracy * 100:.2f}%"
)

print(
    f"Precision : {monthly_precision * 100:.2f}%"
)

print(
    f"Recall    : {monthly_recall * 100:.2f}%"
)

print(
    f"F1 Score  : {monthly_f1 * 100:.2f}%"
)


# ============================================================
# PATIENT-LEVEL MAJORITY VOTE
# ============================================================

patient_final_predictions = []

patient_actual_predictions = []


for i in range(
    len(test_month_predictions)
):

    monthly_preds = (
        test_month_predictions[i]
    )

    positive_votes = int(
        np.sum(monthly_preds)
    )

    negative_votes = 5 - positive_votes

    if positive_votes >= 3:

        final_prediction = 1

    else:

        final_prediction = 0

    patient_final_predictions.append(
        final_prediction
    )

    actual_months = y_test[i]

    actual_positive_votes = int(
        np.sum(actual_months)
    )

    if actual_positive_votes >= 3:

        actual_final = 1

    else:

        actual_final = 0

    patient_actual_predictions.append(
        actual_final
    )


patient_accuracy = accuracy_score(

    patient_actual_predictions,

    patient_final_predictions
)


patient_precision = precision_score(

    patient_actual_predictions,

    patient_final_predictions,

    zero_division=0
)


patient_recall = recall_score(

    patient_actual_predictions,

    patient_final_predictions,

    zero_division=0
)


patient_f1 = f1_score(

    patient_actual_predictions,

    patient_final_predictions,

    zero_division=0
)


print("\n")
print("=" * 70)
print("PATIENT-LEVEL RESULTS")
print("=" * 70)

print(
    f"Accuracy  : {patient_accuracy * 100:.2f}%"
)

print(
    f"Precision : {patient_precision * 100:.2f}%"
)

print(
    f"Recall    : {patient_recall * 100:.2f}%"
)

print(
    f"F1 Score  : {patient_f1 * 100:.2f}%"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(

    patient_actual_predictions,

    patient_final_predictions
)


print("\nConfusion Matrix:")

print(
    cm
)


print("\nClassification Report:")

print(
    classification_report(

        patient_actual_predictions,

        patient_final_predictions,

        target_names=[
            "Low Risk",
            "Higher Risk"
        ],

        zero_division=0
    )
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n")
print("=" * 70)
print("             TRAINING COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nFiles created:")

print(
    "1. endocare_lstm.keras"
)

print(
    "2. endocare_scaler.pkl"
)

print(
    "3. feature_names.json"
)

print(
    "4. prediction_threshold.json"
)

print("\nYou can now run:")

print(
    "python test_predict.py"
)

print(
    "=" * 70
)