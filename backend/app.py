import os
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS


# ============================================================
# FIND DATASET / PYTHON MODEL FOLDER
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "dataset")
)

# Make dataset folder available to Python
if DATASET_DIR not in sys.path:
    sys.path.insert(0, DATASET_DIR)

# IMPORTANT:
# Your predict.py and utils.py use relative paths such as:
# endocare_lstm.keras
# endocare_scaler.pkl
# prediction_threshold.json
#
# Therefore, change the working directory to the dataset folder.
os.chdir(DATASET_DIR)


# ============================================================
# IMPORT EXISTING LSTM PREDICTION FUNCTION
# ============================================================

try:

    from predict import predict_patient

    print("=" * 70)
    print("ENDOCARE BACKEND")
    print("=" * 70)
    print("predict.py imported successfully!")
    print("LSTM prediction system connected successfully!")
    print("=" * 70)

except Exception as error:

    print("=" * 70)
    print("ERROR WHILE IMPORTING PREDICTION SYSTEM")
    print("=" * 70)
    print(str(error))
    print("=" * 70)

    raise


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Allow React frontend to communicate with Flask
CORS(app)


# ============================================================
# HOME / SERVER TEST ROUTE
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "EndoCare LSTM Backend is running.",
        "endpoint": "/predict"
    })


# ============================================================
# PREDICTION ROUTE
# ============================================================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        # ----------------------------------------------------
        # GET JSON DATA FROM REACT
        # ----------------------------------------------------

        data = request.get_json()

        if data is None:

            return jsonify({
                "status": "error",
                "message": "No JSON data received."
            }), 400


        # ----------------------------------------------------
        # PERSONAL INFORMATION
        # ----------------------------------------------------

        if "age" not in data:
            return jsonify({
                "status": "error",
                "message": "Age is required."
            }), 400

        if "height_cm" not in data:
            return jsonify({
                "status": "error",
                "message": "Height is required."
            }), 400

        if "weight_kg" not in data:
            return jsonify({
                "status": "error",
                "message": "Weight is required."
            }), 400


        age = float(data["age"])
        height_cm = float(data["height_cm"])
        weight_kg = float(data["weight_kg"])


        # ----------------------------------------------------
        # VALIDATE PERSONAL INFORMATION
        # ----------------------------------------------------

        if age < 18 or age > 100:

            return jsonify({
                "status": "error",
                "message": "Age must be between 18 and 100."
            }), 400


        if height_cm < 100 or height_cm > 220:

            return jsonify({
                "status": "error",
                "message": "Height must be between 100 cm and 220 cm."
            }), 400


        if weight_kg < 20 or weight_kg > 200:

            return jsonify({
                "status": "error",
                "message": "Weight must be between 20 kg and 200 kg."
            }), 400


        # ----------------------------------------------------
        # GET MONTHLY DATA
        # ----------------------------------------------------

        if "monthly_data" not in data:

            return jsonify({
                "status": "error",
                "message": "Monthly data is required."
            }), 400


        monthly_data = data["monthly_data"]


        # Exactly 5 months are required
        if not isinstance(monthly_data, list):

            return jsonify({
                "status": "error",
                "message": "monthly_data must be a list."
            }), 400


        if len(monthly_data) != 5:

            return jsonify({
                "status": "error",
                "message": "Exactly 5 months of data are required."
            }), 400


        # ----------------------------------------------------
        # REQUIRED MONTHLY FEATURES
        # ----------------------------------------------------

        required_monthly_fields = [

            "Menstrual_Pain_Level",

            "Pain_Duration",

            "Heavy_Menstrual_Bleeding",

            "Menstrual_Irregularity",

            "Pelvic_Pain_Level",

            "Infertility"

        ]


        # ----------------------------------------------------
        # VALIDATE EACH MONTH
        # ----------------------------------------------------

        cleaned_monthly_data = []


        for month_index, month_data in enumerate(
            monthly_data,
            start=1
        ):

            if not isinstance(month_data, dict):

                return jsonify({
                    "status": "error",
                    "message":
                        f"Month {month_index} data must be an object."
                }), 400


            # Check all required fields
            for field in required_monthly_fields:

                if field not in month_data:

                    return jsonify({
                        "status": "error",
                        "message":
                            f"{field} is missing for Month {month_index}."
                    }), 400


            # ------------------------------------------------
            # CONVERT VALUES TO NUMERIC
            # ------------------------------------------------

            try:

                menstrual_pain = int(
                    month_data["Menstrual_Pain_Level"]
                )

                pain_duration = int(
                    month_data["Pain_Duration"]
                )

                heavy_bleeding = int(
                    month_data["Heavy_Menstrual_Bleeding"]
                )

                irregularity = int(
                    month_data["Menstrual_Irregularity"]
                )

                pelvic_pain = int(
                    month_data["Pelvic_Pain_Level"]
                )

                infertility = int(
                    month_data["Infertility"]
                )

            except (ValueError, TypeError):

                return jsonify({
                    "status": "error",
                    "message":
                        f"Invalid numeric value in Month {month_index}."
                }), 400


            # ------------------------------------------------
            # VALIDATE RANGES
            # ------------------------------------------------

            if menstrual_pain < 0 or menstrual_pain > 10:

                return jsonify({
                    "status": "error",
                    "message":
                        f"Menstrual pain must be 0-10 in Month {month_index}."
                }), 400


            if pain_duration < 1 or pain_duration > 31:

                return jsonify({
                    "status": "error",
                    "message":
                        f"Pain duration must be 1-31 days in Month {month_index}."
                }), 400


            if heavy_bleeding not in [0, 1]:

                return jsonify({
                    "status": "error",
                    "message":
                        f"Heavy bleeding must be 0 or 1 in Month {month_index}."
                }), 400


            if irregularity not in [0, 1]:

                return jsonify({
                    "status": "error",
                    "message":
                        f"Menstrual irregularity must be 0 or 1 in Month {month_index}."
                }), 400


            if pelvic_pain < 0 or pelvic_pain > 10:

                return jsonify({
                    "status": "error",
                    "message":
                        f"Pelvic pain must be 0-10 in Month {month_index}."
                }), 400


            if infertility not in [0, 1]:

                return jsonify({
                    "status": "error",
                    "message":
                        f"Infertility must be 0 or 1 in Month {month_index}."
                }), 400


            # ------------------------------------------------
            # STORE CLEANED MONTHLY DATA
            # ------------------------------------------------

            cleaned_monthly_data.append({

                "Menstrual_Pain_Level":
                    menstrual_pain,

                "Pain_Duration":
                    pain_duration,

                "Heavy_Menstrual_Bleeding":
                    heavy_bleeding,

                "Menstrual_Irregularity":
                    irregularity,

                "Pelvic_Pain_Level":
                    pelvic_pain,

                "Infertility":
                    infertility

            })


        # ====================================================
        # CALL EXISTING LSTM MODEL
        # ====================================================

        result = predict_patient(

            age=age,

            height_cm=height_cm,

            weight_kg=weight_kg,

            monthly_data=cleaned_monthly_data

        )


        # ====================================================
        # PREPARE RESPONSE
        # ====================================================

        response = {

            "status": "success",

            # BMI is calculated by utils.py
            "bmi": result["bmi"],

            "monthly_results":
                result["monthly_results"],

            "positive_votes":
                result["positive_votes"],

            "negative_votes":
                result["negative_votes"],

            "average_risk":
                result["average_risk"],

            "final_prediction":
                result["final_prediction"]

        }


        return jsonify(response), 200


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except FileNotFoundError as error:

        return jsonify({

            "status": "error",

            "message": str(error)

        }), 500


    except Exception as error:

        print("\nPrediction Error:")
        print(str(error))

        return jsonify({

            "status": "error",

            "message": str(error)

        }), 500


# ============================================================
# RUN FLASK SERVER
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("          ENDOCARE FLASK BACKEND SERVER")
    print("=" * 70)
    print("Server URL:")
    print("http://127.0.0.1:5000")
    print("\nPrediction API:")
    print("http://127.0.0.1:5000/predict")
    print("=" * 70)
    print("\n")

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True, use_reloader=False

    )