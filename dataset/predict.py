import os
import json
import numpy as np
import tensorflow as tf

from utils import (
    MODEL_PATH,
    load_scaler,
    prepare_user_sequence
)


# ============================================================
# LOAD MODEL
# ============================================================

def load_endocare_model():

    if not os.path.exists(
        MODEL_PATH
    ):

        raise FileNotFoundError(

            "\nLSTM model not found."

            "\nPlease run train.py first."

        )

    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    return model


# ============================================================
# LOAD THRESHOLD
# ============================================================

def load_threshold():

    threshold_file = (
        "prediction_threshold.json"
    )

    if os.path.exists(
        threshold_file
    ):

        with open(
            threshold_file,
            "r"
        ) as file:

            data = json.load(file)

        return float(
            data["threshold"]
        )

    return 0.50


# ============================================================
# PREDICT PATIENT
# ============================================================

def predict_patient(
    age,
    height_cm,
    weight_kg,
    monthly_data
):

    # --------------------------------------------------------
    # Load model and scaler
    # --------------------------------------------------------

    model = load_endocare_model()

    scaler = load_scaler()

    threshold = load_threshold()


    # --------------------------------------------------------
    # Prepare user sequence
    # --------------------------------------------------------

    sequence, bmi = prepare_user_sequence(

        age=age,

        height_cm=height_cm,

        weight_kg=weight_kg,

        monthly_data=monthly_data

    )


    # --------------------------------------------------------
    # Scale sequence
    # --------------------------------------------------------

    original_shape = sequence.shape

    sequence_2d = sequence.reshape(
        -1,
        original_shape[-1]
    )


    sequence_scaled = scaler.transform(
        sequence_2d
    )


    sequence_scaled = sequence_scaled.reshape(
        original_shape
    )


    # --------------------------------------------------------
    # LSTM prediction
    # --------------------------------------------------------

    prediction = model.predict(
        sequence_scaled,
        verbose=0
    )


    # Prediction shape:
    #
    # (1, 5, 1)

    monthly_probabilities = (
        prediction[0, :, 0]
    )


    # --------------------------------------------------------
    # Convert probabilities to monthly predictions
    # --------------------------------------------------------

    monthly_results = []

    monthly_labels = []


    for month_number in range(1, 6):

        probability = float(
            monthly_probabilities[
                month_number - 1
            ]
        )


        risk_percentage = (
            probability * 100
        )


        if probability >= threshold:

            label = "Higher Risk"

            prediction_value = 1

        else:

            label = "Lower Risk"

            prediction_value = 0


        monthly_labels.append(
            prediction_value
        )


        monthly_results.append({

            "month": month_number,

            "probability": probability,

            "risk_percentage": risk_percentage,

            "prediction": label

        })


    # --------------------------------------------------------
    # FINAL MAJORITY VOTE
    # --------------------------------------------------------

    positive_votes = sum(
        monthly_labels
    )

    negative_votes = (
        5 - positive_votes
    )


    if positive_votes >= 3:

        final_prediction = (
            "Higher Risk"
        )

    else:

        final_prediction = (
            "Lower Risk"
        )


    # --------------------------------------------------------
    # Average risk
    # --------------------------------------------------------

    average_risk = (
        sum(
            result["risk_percentage"]
            for result in monthly_results
        )
        / 5
    )


    return {

        "bmi": bmi,

        "monthly_results":
            monthly_results,

        "positive_votes":
            positive_votes,

        "negative_votes":
            negative_votes,

        "average_risk":
            average_risk,

        "final_prediction":
            final_prediction

    }