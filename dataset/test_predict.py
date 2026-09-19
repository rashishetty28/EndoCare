from predict import predict_patient


# ============================================================
# INPUT FUNCTION
# ============================================================

def get_integer(
    message,
    minimum=None,
    maximum=None
):

    while True:

        try:

            value = int(
                input(message)
            )

            if minimum is not None:

                if value < minimum:

                    print(
                        f"Enter a value >= {minimum}."
                    )

                    continue


            if maximum is not None:

                if value > maximum:

                    print(
                        f"Enter a value <= {maximum}."
                    )

                    continue


            return value

        except ValueError:

            print(
                "Please enter a valid integer."
            )


# ============================================================
# FLOAT INPUT
# ============================================================

def get_float(
    message,
    minimum=None,
    maximum=None
):

    while True:

        try:

            value = float(
                input(message)
            )

            if minimum is not None:

                if value < minimum:

                    print(
                        f"Enter a value >= {minimum}."
                    )

                    continue


            if maximum is not None:

                if value > maximum:

                    print(
                        f"Enter a value <= {maximum}."
                    )

                    continue


            return value

        except ValueError:

            print(
                "Please enter a valid number."
            )


# ============================================================
# YES / NO INPUT
# ============================================================

def get_binary(message):

    while True:

        value = input(
            message
        ).strip().lower()


        if value in [
            "yes",
            "y",
            "1"
        ]:

            return 1


        if value in [
            "no",
            "n",
            "0"
        ]:

            return 0


        print(
            "Please enter Yes or No."
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("\n")

    print("                 ENDOCARE")


    # ========================================================
    # PERSONAL INFORMATION
    # ========================================================

    print("\n")
    print("               PERSONAL INFORMATION")


    age = get_integer(

        "Enter Age: ",

        minimum=18,

        maximum=100

    )


    height_cm = get_float(

        "Enter Height (cm): ",

        minimum=100,

        maximum=220

    )


    weight_kg = get_float(

        "Enter Weight (kg): ",

        minimum=20,

        maximum=200

    )


    # ========================================================
    # MONTHLY INFORMATION
    # ========================================================

    monthly_data = []


    for month in range(1, 6):

        print("\n")

        print(
            f"MONTH {month} INFORMATION"
        )



        menstrual_pain = get_integer(

            "Menstrual Pain Level (0-10): ",

            minimum=0,

            maximum=10

        )


        pain_duration = get_integer(

            "Pain Duration (days): ",

            minimum=1,

            maximum=31

        )


        heavy_bleeding = get_binary(

            "Heavy Menstrual Bleeding? (Yes/No): "

        )


        irregularity = get_binary(

            "Menstrual Irregularity? (Yes/No): "

        )


        pelvic_pain = get_integer(

            "Pelvic Pain Level (0-10): ",

            minimum=0,

            maximum=10

        )


        infertility = get_binary(

            "Infertility? (Yes/No): "

        )


        monthly_data.append({

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


    # ========================================================
    # CALL MODEL
    # ========================================================

    print("\n")
    print("              ANALYZING PATIENT DATA")


    result = predict_patient(

        age=age,

        height_cm=height_cm,

        weight_kg=weight_kg,

        monthly_data=monthly_data

    )



    print("\n")
  

    print(
        f"Calculated BMI: "
        f"{result['bmi']:.1f}"
    )

  


    print("\n")
   
    print("              5-MONTH RISK RESULTS")
  


    for month_result in result[
        "monthly_results"
    ]:

        month = month_result[
            "month"
        ]

        risk = month_result[
            "risk_percentage"
        ]

        prediction = month_result[
            "prediction"
        ]


        print(
            f"\nMonth {month}"
        )

        print(
            f"Risk Probability : "
            f"{risk:.2f}%"
        )

        print(
            f"Prediction       : "
            f"{prediction}"
        )



    print("\n")
    print("                 FINAL RESULT")


    print(
        "\nMonthly Higher-Risk Votes : "
        f"{result['positive_votes']} / 5"
    )


    print(
        "Monthly Lower-Risk Votes  : "
        f"{result['negative_votes']} / 5"
    )


    print(
        f"\nAverage 5-Month Risk      : "
        f"{result['average_risk']:.2f}%"
    )


    print(
        "\nFINAL PREDICTION          : "
        f"{result['final_prediction']}"
    )


    print("\n")
  




if __name__ == "__main__":

    main()