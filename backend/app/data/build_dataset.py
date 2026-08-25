"""
Builds a labeled dataset of scam / legitimate text messages for training
the text classification model.

v2 changes (fixing keyword-shortcut overfitting from v1):
  - Every category now has templates in multiple REGISTERS: short SMS,
    casual WhatsApp-style, and longer email-style - so the model can't
    just learn "long message = scam" or "short = safe" etc.
  - Scam templates deliberately include a mix of "soft" phrasing (no
    urgency words, no "click", no "OTP") alongside "hard" phrasing
    (classic urgency/threat language), so the model has to learn actual
    scam intent/structure rather than a handful of trigger words.
  - Legitimate templates deliberately reuse the exact same trigger words
    scams use ("urgent", "bank", "OTP", "payment", "verify", "job",
    "delivery", "investment", "click", "account") in ordinary, benign
    contexts, so the model can't shortcut on vocabulary alone.
  - Exact-duplicate rows are removed after generation.
  - Rows are NOT pre-split here; splitting into train/val/test happens
    in train_text_model.py so this file stays a pure data source.
"""
import csv
import random
import os

random.seed(42)

OUT_PATH = os.path.join(os.path.dirname(__file__), "labeled_dataset.csv")

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Bank of America",
         "Chase Bank", "Wells Fargo", "PNB", "Kotak Mahindra", "Citibank"]
NAMES = ["Rahul", "Priya", "John", "Sarah", "Amit", "Neha", "David", "Emma",
         "Vikram", "Anjali", "Meera", "Tom", "Sana", "Karan"]
AMOUNTS = ["Rs 9,999", "Rs 49,999", "$500", "$2,450", "Rs 1,00,000", "$9,999",
           "Rs 25,000", "$150", "Rs 3,200", "$75"]
LINKS = ["bit.ly/verify-now", "secure-update-bank.com", "http://acc0unt-verify.in",
         "paytm-cashback-offer.xyz", "amaz0n-delivery-track.com",
         "hdfcbank-kyc-update.net", "irs-refund-claim.info",
         "linkedin-jobs-apply.co", "instagram-verify-account.live",
         "myaccount-securehelp.top"]
DEADLINES = ["within 24 hours", "in the next 2 hours", "by today 6 PM",
             "immediately", "within 30 minutes", "before midnight",
             "by tomorrow", "this week", "before the offer closes"]
COMPANIES = ["Amazon", "FedEx", "DHL", "Flipkart", "India Post", "UPS", "Blue Dart"]
JOB_TITLES = ["Data Entry Executive", "Online Form Filling Agent",
              "Part-Time Content Reviewer", "Work From Home Assistant",
              "Social Media Assistant", "Customer Support Associate"]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chicago", "New York", "Pune", "Austin"]


def fill(t):
    return (t.replace("{bank}", random.choice(BANKS))
             .replace("{name}", random.choice(NAMES))
             .replace("{amount}", random.choice(AMOUNTS))
             .replace("{link}", random.choice(LINKS))
             .replace("{deadline}", random.choice(DEADLINES))
             .replace("{company}", random.choice(COMPANIES))
             .replace("{job}", random.choice(JOB_TITLES))
             .replace("{city}", random.choice(CITIES)))


SCAM_TEMPLATES = {
    "banking_scam": [
        "Dear customer, your {bank} account has been temporarily suspended due to unusual activity. Verify your identity {deadline} at {link} to avoid permanent block.",
        "ALERT: Your {bank} debit card will be blocked {deadline}. Click {link} and enter your card number, CVV and PIN to reactivate.",
        "{bank} here. We noticed a login from a new device on your account. If this wasn't you, please confirm your details at {link}.",
        "Hi, this is regarding your {bank} account review. Kindly complete the pending verification at {link} at your convenience.",
        "{bank}: A/C temp. locked. Re-verify at {link}",
        "Hey it's {name} from {bank} support, saw some odd activity on your account, can you just confirm your card details here {link}?",
        "Dear Valued Customer,\n\nAs part of our routine security review, we have identified irregular activity associated with your {bank} account. To ensure uninterrupted access to your banking services, we kindly request you to complete a short identity verification process {deadline}.\n\nPlease proceed here: {link}\n\nThank you for your cooperation.\nCustomer Care Team",
    ],
    "upi_payment_scam": [
        "You have received {amount} via UPI. To claim, open {link} and enter your UPI PIN to confirm receipt.",
        "URGENT: Your Paytm/GPay account will be deactivated {deadline}. Verify by entering UPI PIN at {link}",
        "{name}, I think I sent you {amount} by mistake on UPI, could you refund it by scanning this code and entering your PIN? {link}",
        "hey is this your number? sent {amount} to you by accident on gpay, pls send back using this link {link}",
        "Notice: A pending cashback of {amount} is linked to your wallet. Complete the claim process by linking your UPI PIN here: {link} before {deadline}.",
    ],
    "phishing": [
        "Your Microsoft 365 password expires {deadline}. Click {link} to keep the same password and avoid data loss.",
        "Someone tried to sign in to your account. If this wasn't you, verify your identity here: {link}",
        "hi, noticed a sign in from {city} on your account just now, wasn't sure if that was you? check here {link}",
        "Your mailbox has reached its storage limit and new messages may not be delivered. Free up space or upgrade your plan here: {link}",
        "Account team: please review the recent access request on your file and confirm ownership at {link} when you get a chance.",
    ],
    "job_scam": [
        "Congratulations {name}! You are shortlisted for {job} with {amount}/day. Register now by paying a refundable deposit at {link}",
        "Work from home, earn {amount} weekly! No experience needed. Message us on WhatsApp and pay a small registration fee to start.",
        "Hi {name}, thanks for your interest in the {job} role. To finalize onboarding, please send a one-time kit/training fee of {amount} to the link below and we'll get you started. {link}",
        "hey saw ur resume online, we're hiring for {job}, pay is good, just need a small deposit to activate ur offer letter, interested?",
        "HR Team: Your application for {job} has been approved. Send your bank details and a processing fee of {amount} to activate your offer letter.",
        "Dear Candidate,\n\nWe are pleased to inform you that you have been selected for the position of {job} at our {city} branch. To proceed with your appointment, a refundable security deposit of {amount} is required.\n\nRegards,\nHiring Team",
    ],
    "investment_scam": [
        "Turn {amount} into {amount} in 7 days! Join our exclusive crypto trading group now: {link}. Guaranteed returns, limited seats!",
        "Our AI trading bot has a 98% win rate. Invest {amount} today and double it in a week. DM now for the link.",
        "{name}, I made {amount} in a month with this stock tip group, thought you might be interested too, here's the link if you want to check it out {link}",
        "hey have you heard about this new trading platform? my cousin doubled his savings in {deadline}, group link is {link} if u wanna join",
        "We are pleased to introduce an exclusive investment opportunity offering consistent 30-40% monthly returns, backed by our proprietary trading algorithm. Minimum investment {amount}. Learn more at {link}.",
    ],
    "lottery_scam": [
        "Congratulations! Your number has won {amount} in the international lottery. Send your bank details to {link} to claim your prize {deadline}.",
        "You've been selected as the lucky winner of the {company} anniversary lottery worth {amount}. Claim now at {link}",
        "hii, ur number got picked in our {deadline} giveaway, u won {amount}, just fill this form to claim {link}",
        "We are delighted to inform you that your mobile number has been selected in our periodic lucky draw and you are entitled to a cash prize of {amount}. Kindly complete the claim form at {link}.",
        "CLAIM NOW: Your mobile number has won {amount} in the WhatsApp lucky draw. Contact our agent immediately at {link}",
    ],
    "delivery_scam": [
        "{company}: Your package could not be delivered due to an incomplete address. Update your details and pay a redelivery fee at {link}",
        "Your parcel is on hold at customs. Pay a clearance fee of {amount} at {link} to release it {deadline}.",
        "hi, courier attempted delivery of your parcel today but no one was home, small redelivery charge applies, pls confirm address and pay here {link}",
        "{company} Delivery: We attempted delivery but failed. Reschedule and confirm your address at {link} within {deadline} or the parcel will be returned.",
        "Dear Customer,\n\nYour recent order is currently held at our {city} facility due to an outstanding customs duty of {amount}. Please settle this amount at your earliest convenience to release your shipment.\n\n{link}\n\n{company} Logistics",
    ],
    "govt_impersonation": [
        "This is an official notice from the Income Tax Department. You have a pending refund of {amount}. Verify your PAN and bank details at {link}",
        "SOCIAL SECURITY ADMINISTRATION: Your SSN has been suspended due to suspicious activity. Call back immediately or your assets will be frozen.",
        "hello this is regarding a case filed under your number, please contact our office at the earliest to avoid further action",
        "This is to inform you that a tax refund of {amount} has been processed in your favor. Kindly confirm your account details at {link} to receive the amount.",
        "Notice from IRS: You owe {amount} in unpaid taxes. Failure to pay {deadline} will result in legal action. Pay now at {link}",
    ],
    "romance_scam": [
        "{name}, I feel such a deep connection with you even though we've never met. I'm stuck at customs and need {amount} to come see you, please help.",
        "My darling, I love you so much. I'm currently deployed overseas and need {amount} for an emergency medical fee before I can be discharged.",
        "I know we just started talking but I really feel like you understand me. Something came up with my visa paperwork, would you be able to help with {amount}? I'll pay you back I promise.",
        "hey love, missing you so much today. quick thing, customs is holding a package with gifts for you and I just need {amount} to release it, can you help?",
        "Sweetheart, I wanted to visit you next month but my card is having issues here, could you send {amount} so I can book the flight, I'll pay you back the moment I land.",
    ],
    "tech_support_scam": [
        "WARNING: Your computer has been infected with a virus. Call our Microsoft certified technician immediately at the number on screen to fix it.",
        "Your Windows license has expired and your device is at risk. Download this tool from {link} to renew immediately.",
        "Hi, this is Apple Support following up on a ticket regarding unusual activity on your iCloud account, could you confirm your Apple ID password so we can secure it for you?",
        "hey noticed some weird pop-ups mentioned in your last message, might be a virus, best to call the support number on your screen right away",
        "Your antivirus subscription has expired, your PC is unprotected. Call now and pay {amount} to renew and remove detected threats.",
    ],
    "account_takeover": [
        "Your Instagram account will be permanently deleted {deadline} due to a copyright violation. Verify your account and password at {link} to appeal.",
        "We detected a login attempt to your Facebook account from an unrecognized device. Confirm your password at {link} immediately or lose access.",
        "hey, is this you trying to log into whatsapp on a new phone? if it wasn't, just forward me the code you got so I can cancel it",
        "hi this is regarding your recent account review, we just need you to confirm your password to keep things active",
        "Your account has violated our community guidelines and will be suspended. Verify your identity and password within {deadline} at {link}",
    ],
    "other": [
        "Hi, this is {name} from customer support. We need to confirm your identity, please share the OTP sent to your phone.",
        "Free {amount} recharge for the first 100 users! Click {link} and share with 10 friends to claim.",
        "Your subscription payment of {amount} failed. Update your card details immediately at {link} to avoid service interruption.",
        "hey just checking, did you get the code we sent? need it to finish setting up your reward",
        "Limited time offer: Get {amount} cashback on your next purchase, just verify your card details at {link}",
    ],
}

SAFE_TEMPLATES = [
    "Hi {name}, are we still meeting for lunch tomorrow at 1pm?",
    "Your OTP for login is 483920. Do not share this with anyone. Valid for 10 minutes.",
    "{bank}: Your account was credited with {amount} on 12-Aug-2026. Available balance: {amount}. Thank you for banking with us.",
    "Reminder: Your electricity bill of {amount} is due on 25th. Pay via the official app or website to avoid late fees.",
    "{company}: Your order has been shipped and is expected to arrive by Thursday. Track it in the app under 'My Orders'.",
    "Hey {name}, don't forget we have the team meeting at 10am tomorrow. Bring your laptop, it's kind of urgent we finalize the slides.",
    "Your monthly statement for {bank} is now available in the mobile app under Statements.",
    "Thanks for your payment of {amount}. Your subscription has been renewed until next year.",
    "{name}: Can you send me the report before end of day? It's urgent, the client meeting got moved up. Thanks!",
    "Your appointment with Dr. Mehta is confirmed for Friday at 4:30 PM. Reply CONFIRM to keep this slot.",
    "Happy birthday {name}! Hope you have an amazing day. Let's catch up this weekend.",
    "{company} delivery update: Your package is out for delivery and will arrive today between 2-6 PM.",
    "Your flight PNR is confirmed. Departure 10:45 AM, Gate 14. Check in online to save time at the airport.",
    "Reminder: Your gym membership renews automatically next week for {amount}. No action needed.",
    "{name}, here are the notes from today's class. Let me know if you have questions.",
    "Your prescription is ready for pickup at the pharmacy. Store hours are 9 AM to 9 PM.",
    "Welcome to the team! Your first day orientation for the {job} role starts Monday at 9 AM in the {city} office.",
    "This is a reminder that your library book is due back in 3 days.",
    "Your ride is arriving in 3 minutes. Look for a white sedan, license plate ending in 47.",
    "Congrats on completing the course! Your certificate has been emailed to you.",
    "Click here to view your boarding pass for tomorrow's flight: myairline.com/mybookings (official airline site).",
    "Hi {name}, just a heads up your bank statement shows a pending investment SIP deduction of {amount} on the 5th as usual, nothing to action.",
    "Team, quick reminder to submit your expense reports by end of week, HR needs them for the {city} office audit.",
    "{name}, following up on our call, the delivery for the {city} office supplies should reach by Friday as planned.",
    "Your account password was changed successfully. If you did not make this change, contact support from the app's Help section.",
    "Investment update: your quarterly mutual fund statement is now available to download from the {bank} portal.",
    "Hey, did you get a chance to look at the job posting I sent? No rush, just checking in whenever you're free.",
    "hey are you around this weekend? thinking of heading to {city} for a short trip",
    "quick one - can you approve the {amount} invoice on the portal when you get a sec, no rush",
    "{name}: dinner at 8 tonight? same place as last time",
    "Your package delivery has been rescheduled to tomorrow per your request. No action needed.",
    "Reminder: performance review meeting with your manager is scheduled for {deadline} in {city} office, room 4B.",
    "hey loved catching up yesterday, let's plan that trip properly soon",
    "Your {bank} card ending 4521 was used for a purchase of {amount} at a local store today.",
]


def build():
    rows = set()
    for scam_type, templates in SCAM_TEMPLATES.items():
        for t in templates:
            for _ in range(14):
                filled = fill(t)
                rows.add((filled, 1, scam_type))
    for t in SAFE_TEMPLATES:
        for _ in range(40):
            filled = fill(t)
            rows.add((filled, 0, "safe"))

    rows = list(rows)
    random.shuffle(rows)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label", "scam_type"])
        w.writerows(rows)

    n_scam = sum(1 for r in rows if r[1] == 1)
    n_safe = sum(1 for r in rows if r[1] == 0)
    print(f"Wrote {len(rows)} unique rows to {OUT_PATH}")
    print(f"  scam: {n_scam}  safe: {n_safe}  (ratio {n_scam/max(n_safe,1):.2f})")


if __name__ == "__main__":
    build()
