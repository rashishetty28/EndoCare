import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "EndoCare_Dataset.xlsx"

MODEL_PATH = "endocare_lstm.keras"
SCALER_PATH = "endocare_scaler.pkl"
FEATURES_PATH = "feature_names.json"
THRESHOLD_PATH = "prediction_threshold.json"


# ============================================================
# FEATURES USED BY THE LSTM
# ============================================================

FEATURE_COLUMNS = [
    "Month",
    "Age",
    "BMI",
    "Menstrual_Pain_Level",
    "Pain_Duration",
    "Heavy_Menstrual_Bleeding",
    "Menstrual_Irregularity",
    "Pelvic_Pain_Level",
    "Infertility"
]

TARGET_COLUMN = "Diagnosis"


# ============================================================
# REQUIRED DATASET COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "Patient_ID",
    "Month",
    "Age",
    "Height_cm",
    "Weight_kg",
    "BMI",
    "Menstrual_Pain_Level",
    "Pain_Duration",
    "Heavy_Menstrual_Bleeding",
    "Menstrual_Irregularity",
    "Pelvic_Pain_Level",
    "Infertility",
    "Diagnosis"
]


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(file_path=DATASET_PATH):

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"\nDataset not found:\n{file_path}\n"
            f"\nMake sure {DATASET_PATH} is in the same folder as train.py."
        )

    print("Loading dataset...")

    # Excel file
    df = pd.read_excel(file_path)

    print("Dataset loaded successfully.")

    return df


# ============================================================
# CLEAN DATASET
# ============================================================

def clean_dataset(df):

    print("\nCleaning dataset...")

    # Remove accidental index column if present
    unwanted_columns = [
        "index",
        "Unnamed: 0"
    ]

    for column in unwanted_columns:
        if column in df.columns:
            df = df.drop(columns=[column])

    # Check required columns
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "\nMissing columns in dataset:\n"
            + "\n".join(missing_columns)
            + "\n\nActual columns found:\n"
            + "\n".join(df.columns.tolist())
        )

    # Keep only expected columns
    df = df[REQUIRED_COLUMNS].copy()

    # Convert numerical columns
    numerical_columns = [
        "Month",
        "Age",
        "Height_cm",
        "Weight_kg",
        "BMI",
        "Menstrual_Pain_Level",
        "Pain_Duration",
        "Heavy_Menstrual_Bleeding",
        "Menstrual_Irregularity",
        "Pelvic_Pain_Level",
        "Infertility",
        "Diagnosis"
    ]

    for column in numerical_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove rows containing missing values
    before = len(df)

    df = df.dropna().copy()

    removed = before - len(df)

    if removed > 0:
        print(f"Removed {removed} rows containing missing values.")
    else:
        print("No missing values found.")

    # Convert Patient_ID to string
    df["Patient_ID"] = df["Patient_ID"].astype(str)

    # Sort properly
    df = df.sort_values(
        ["Patient_ID", "Month"]
    ).reset_index(drop=True)

    # Basic validation
    if len(df) == 0:
        raise ValueError(
            "Dataset contains no usable rows after cleaning."
        )

    # Diagnosis must be 0 or 1
    invalid_diagnosis = ~df["Diagnosis"].isin([0, 1])

    if invalid_diagnosis.any():
        raise ValueError(
            "Diagnosis column must contain only 0 and 1."
        )

    # Check months
    invalid_month = ~df["Month"].isin([1, 2, 3, 4, 5])

    if invalid_month.any():
        raise ValueError(
            "Month column must contain values from 1 to 5."
        )

    print("Dataset cleaned successfully.")

    return df


# ============================================================
# VALIDATE FIVE-MONTH PATIENT DATA
# ============================================================

def validate_patient_sequences(df):

    valid_patients = []
    invalid_patients = []

    for patient_id, patient_df in df.groupby("Patient_ID"):

        months = sorted(
            patient_df["Month"].astype(int).tolist()
        )

        if len(patient_df) == 5 and months == [1, 2, 3, 4, 5]:

            valid_patients.append(patient_id)

        else:

            invalid_patients.append(patient_id)

    return valid_patients, invalid_patients


# ============================================================
# CREATE LSTM SEQUENCES
# ============================================================

def create_sequences(df):

    print("\nCreating 5-month patient sequences...")

    X = []
    y = []
    patient_ids = []

    valid_patients, invalid_patients = validate_patient_sequences(df)

    print(
        f"Patients with complete 5-month data: "
        f"{len(valid_patients)}"
    )

    if invalid_patients:
        print(
            f"Patients skipped because they do not have "
            f"exactly 5 months: {len(invalid_patients)}"
        )

    for patient_id in valid_patients:

        patient_df = df[
            df["Patient_ID"] == patient_id
        ].sort_values("Month")

        features = patient_df[
            FEATURE_COLUMNS
        ].values.astype(np.float32)

        labels = patient_df[
            TARGET_COLUMN
        ].values.astype(np.float32)

        # Expected shape:
        # features = (5, 9)
        # labels   = (5,)
        if features.shape != (5, len(FEATURE_COLUMNS)):
            continue

        if labels.shape != (5,):
            continue

        X.append(features)
        y.append(labels)
        patient_ids.append(patient_id)

    if len(X) == 0:
        raise ValueError(
            "\nNo valid 5-month patient sequences were created."
        )

    X = np.array(X, dtype=np.float32)

    y = np.array(y, dtype=np.float32)

    print(
        f"Created sequences for {len(X)} patients."
    )

    print(
        f"X shape: {X.shape}"
    )

    print(
        f"y shape: {y.shape}"
    )

    return X, y, np.array(patient_ids)


# ============================================================
# SCALE LSTM INPUT
# ============================================================

def fit_scaler(X_train):

    print("\nFitting feature scaler...")

    scaler = StandardScaler()

    number_of_patients = X_train.shape[0]

    number_of_months = X_train.shape[1]

    number_of_features = X_train.shape[2]

    # Convert:
    # (patients, months, features)
    #
    # to:
    # (patients * months, features)

    X_2d = X_train.reshape(
        -1,
        number_of_features
    )

    scaler.fit(X_2d)

    X_scaled = scaler.transform(
        X_2d
    )

    X_scaled = X_scaled.reshape(
        number_of_patients,
        number_of_months,
        number_of_features
    )

    return X_scaled, scaler


def transform_sequences(X, scaler):

    number_of_patients = X.shape[0]

    number_of_months = X.shape[1]

    number_of_features = X.shape[2]

    X_2d = X.reshape(
        -1,
        number_of_features
    )

    X_scaled = scaler.transform(
        X_2d
    )

    X_scaled = X_scaled.reshape(
        number_of_patients,
        number_of_months,
        number_of_features
    )

    return X_scaled


# ============================================================
# SAVE SCALER
# ============================================================

def save_scaler(scaler):

    joblib.dump(
        scaler,
        SCALER_PATH
    )

    print(
        f"Scaler saved as: {SCALER_PATH}"
    )


# ============================================================
# SAVE FEATURE INFORMATION
# ============================================================

def save_feature_information():

    with open(
        FEATURES_PATH,
        "w"
    ) as file:

        json.dump(
            FEATURE_COLUMNS,
            file,
            indent=4
        )

    print(
        f"Feature information saved as: {FEATURES_PATH}"
    )


# ============================================================
# SAVE THRESHOLD
# ============================================================

def save_threshold(threshold=0.50):

    with open(
        THRESHOLD_PATH,
        "w"
    ) as file:

        json.dump(
            {
                "threshold": threshold
            },
            file,
            indent=4
        )

    print(
        f"Prediction threshold saved as: "
        f"{THRESHOLD_PATH}"
    )


# ============================================================
# LOAD SCALER
# ============================================================

def load_scaler():

    if not os.path.exists(SCALER_PATH):

        raise FileNotFoundError(
            "\nScaler not found."
            "\nPlease run train.py first."
        )

    return joblib.load(
        SCALER_PATH
    )


# ============================================================
# CALCULATE BMI
# ============================================================

def calculate_bmi(height_cm, weight_kg):

    height_m = height_cm / 100.0

    if height_m <= 0:

        raise ValueError(
            "Height must be greater than zero."
        )

    bmi = weight_kg / (height_m ** 2)

    return round(bmi, 1)


# ============================================================
# PREPARE USER DATA FOR LSTM
# ============================================================

def prepare_user_sequence(
    age,
    height_cm,
    weight_kg,
    monthly_data
):

    if len(monthly_data) != 5:

        raise ValueError(
            "Exactly 5 months of data are required."
        )

    bmi = calculate_bmi(
        height_cm,
        weight_kg
    )

    sequence = []

    for month_number in range(1, 6):

        month_data = monthly_data[
            month_number - 1
        ]

        row = [

            month_number,

            age,

            bmi,

            month_data[
                "Menstrual_Pain_Level"
            ],

            month_data[
                "Pain_Duration"
            ],

            month_data[
                "Heavy_Menstrual_Bleeding"
            ],

            month_data[
                "Menstrual_Irregularity"
            ],

            month_data[
                "Pelvic_Pain_Level"
            ],

            month_data[
                "Infertility"
            ]
        ]

        sequence.append(row)

    sequence = np.array(
        sequence,
        dtype=np.float32
    )

    # Shape:
    # (1, 5, 9)

    sequence = np.expand_dims(
        sequence,
        axis=0
    )

    return sequence, bmi