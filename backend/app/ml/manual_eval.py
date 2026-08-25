"""
Manual out-of-distribution test set: hand-written messages that were NOT
generated from the dataset templates, used to sanity-check that the model
generalizes rather than memorizing template phrasing. This is separate
from the automated train/val/test split in train_text_model.py and is
meant to be run manually after training/retraining.

Run:  python -m app.ml.manual_eval
"""
from app.ml.inference import predict_text

SCAM_CASES = [
    ("banking_scam", "Your account with us shows irregular login attempts from an unknown device last night. For your safety we've limited some features until you confirm it was really you through the link we sent."),
    ("upi_payment_scam", "Sir maine aapko galti se 5000 bhej diya hai UPI se, please scan the QR and send it back, urgent hai"),
    ("job_scam", "We reviewed your profile and would like to offer you a home-based data entry role paying well above market rate. To lock in your seat for training, a small one-time registration is needed before we onboard you."),
    ("investment_scam", "Made 3x return in two weeks with this new signal group, several of us are already in, thinking of adding more, you interested in taking a look?"),
    ("delivery_scam", "Your item is currently held at the sorting facility because of an unpaid handling charge. Settle it today to avoid the shipment being sent back to origin."),
    ("lottery_scam", "You've been randomly selected among this month's active users to receive a cash reward. Fill in a few quick details to have it processed to your account."),
    ("account_takeover", "We noticed your recent password reset request. If that wasn't you, reply with the 6-digit code you just received so our system can cancel it before it goes through."),
]

LEGIT_CASES = [
    ("normal_bank_notification", "Your savings account was credited with your salary today. Available balance can be checked anytime in the app."),
    ("normal_delivery_notification", "Your order has left the warehouse and is expected to reach you within 2 business days. No action is needed from your end."),
    ("normal_job_message", "Thanks for applying! Our recruiting team will reach out within a week if your profile matches what we're looking for."),
    ("normal_payment_confirmation", "Payment received - thanks! Your invoice has been marked as paid and a receipt was emailed to you."),
    ("normal_promotional_message", "New season, new arrivals! Check out this week's collection in the app, free shipping on orders over $40."),
]


def run():
    print("=" * 70)
    print("SCAM examples (expect predicted_label == 'scam')")
    print("=" * 70)
    correct = 0
    for expected_type, text in SCAM_CASES:
        r = predict_text(text)
        ok = r["predicted_label"] == "scam"
        correct += ok
        print(f"\n[{'OK ' if ok else 'MISS'}] expected type: {expected_type}")
        print(f"  text: {text[:90]}...")
        print(f"  -> scam_probability={r['scam_probability']}  label={r['predicted_label']}  "
              f"predicted_type={r['scam_type']} ({r['scam_type_confidence']})")
    print(f"\nScam recall on manual set: {correct}/{len(SCAM_CASES)}")

    print("\n" + "=" * 70)
    print("LEGITIMATE examples (expect predicted_label == 'safe')")
    print("=" * 70)
    correct = 0
    for label_name, text in LEGIT_CASES:
        r = predict_text(text)
        ok = r["predicted_label"] == "safe"
        correct += ok
        print(f"\n[{'OK ' if ok else 'MISS'}] {label_name}")
        print(f"  text: {text[:90]}...")
        print(f"  -> scam_probability={r['scam_probability']}  label={r['predicted_label']}")
    print(f"\nLegit specificity on manual set: {correct}/{len(LEGIT_CASES)}")
    print("\n(False positives = legit messages misclassified as scam;")
    print(" False negatives = scam messages misclassified as safe.)")


if __name__ == "__main__":
    run()
