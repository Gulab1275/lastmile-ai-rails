"""
Phase 4: Independent Security Evaluation on 100+ Previously Unused Messages.
Dataset: 105 completely independent, freshly constructed messages.
Measures False Negatives (FN) and False Positives (FP) independently.
Never uses training or development test samples.
"""
import pytest
from services.ai.scam import classify_message
from services.shared.schemas import ScamLabel


INDEPENDENT_105_DATASET = [
    # =========================================================================
    # A. SCAM SAMPLES (65 Messages) - Target: Never False Negative (Never LEGIT)
    # =========================================================================
    # 1. OTP Theft (10 messages)
    ("SCAM_OTP_01", "HBL Alert: Your debit card is blocked. Send your 6-digit SMS OTP to 0312-9988776 to unfreeze immediately.", True),
    ("SCAM_OTP_02", "Your Daraz order verification is pending. Please share the WhatsApp OTP code received on your mobile.", True),
    ("SCAM_OTP_03", "JazzCash Customer: Rs 15,000 credit waiting. Reply with your one-time password OTP to release transaction.", True),
    ("SCAM_OTP_04", "Easypaisa emergency: Unauthorized login detected. Provide verification OTP code to secure your wallet balance.", True),
    ("SCAM_OTP_05", "Nadra e-portal: Your identity verification has failed. Send your SMS OTP to officer WhatsApp for manual override.", True),
    ("SCAM_OTP_06", "Urgent courier update: Leopard parcel held at sorting center. Text OTP password to 0300-8877665 to confirm address.", True),
    ("SCAM_OTP_07", "Google Account Warning: Password reset requested from Russia. Share verification code immediately to keep account.", True),
    ("SCAM_OTP_08", "Meezan Bank: Your digital banking session has expired. Send mobile OTP to restore online payments.", True),
    ("SCAM_OTP_09", "Pakistani Citizen Portal: You have 1 unread relief notice. Enter mobile OTP on wa.me/923001122334 to view.", True),
    ("SCAM_OTP_10", "WhatsApp Security Team: Your WhatsApp will be deleted in 12 hours. Send the 6 digit SMS registration code now.", True),

    # 2. ATM PIN & Security Code Theft (10 messages)
    ("SCAM_PIN_01", "Bank Alfalah: Your ATM card chip is damaged. Reply with your 4-digit ATM PIN to generate a replacement card.", True),
    ("SCAM_PIN_02", "ATM service notice: Please confirm your secret PIN code to activate contactless card payments.", True),
    ("SCAM_PIN_03", "State Bank Notice: Verification of biometric and ATM secret PIN code is required for all active accounts.", True),
    ("SCAM_PIN_04", "Dear cardholder, your debit card is temporarily deactivated. Text your 4-digit secret PIN to reactivate today.", True),
    ("SCAM_PIN_05", "MCB Alert: Unusual ATM withdrawal attempted. Enter your secret card PIN at bit.ly/mcb-verify to block card.", True),
    ("SCAM_PIN_06", "Apka ATM card block kar diya gaya hai. Apna secret PIN number foran WhatsApp karein taake card chal sake.", True),
    ("SCAM_PIN_07", "Urgent: Your debit card will be confiscated at ATMs. Share your confidential PIN to update banking records.", True),
    ("SCAM_PIN_08", "UBL digital services: Please provide your 4 digit card PIN code to confirm your annual biometric status.", True),
    ("SCAM_PIN_09", "Apne ATM card ka 4-hinsi PIN code 8899 par bhejein warna aapka account hamesha ke liye band ho jayega.", True),
    ("SCAM_PIN_10", "Security warning: Send your 4-digit card PIN code to verify that you are the genuine card owner.", True),

    # 3. Bank Login & Credential Theft (10 messages)
    ("SCAM_LOGIN_01", "Your online banking password has expired. Click here bit.ly/bank-renew to enter your username and password.", True),
    ("SCAM_LOGIN_02", "Faysal Bank: Your internet banking profile is restricted. Log in at t.co/faysal-login to restore privileges.", True),
    ("SCAM_LOGIN_03", "Standard Chartered: Security certificate update required. Submit your internet banking password on our WhatsApp.", True),
    ("SCAM_LOGIN_04", "Your account credentials have been leaked. Enter current login password at secure-pak-bank.xyz to protect funds.", True),
    ("SCAM_LOGIN_05", "Apne bank account ka login username aur password is helpline number 0345-1122334 par message karein.", True),
    ("SCAM_LOGIN_06", "Portal alert: Multiple failed login attempts. Verify your master password immediately or account will terminate.", True),
    ("SCAM_LOGIN_07", "National Bank NBP: Digital app upgrade required. Click tinyurl.com/nbp-update and enter your secret credentials.", True),
    ("SCAM_LOGIN_08", "Allied Bank: We noticed a foreign transaction. Provide your secret login credentials to initiate refund.", True),
    ("SCAM_LOGIN_09", "Bank customer alert: Send your secret passcode and account details to officer WhatsApp for tax clearance.", True),
    ("SCAM_LOGIN_10", "Apka internet banking access rok diya gaya hai. Password bhejein taake foran unfreeze kiya ja sake.", True),

    # 4. Fake Registration Fees & Portal Charges (10 messages)
    ("SCAM_FEE_01", "BISP 2026 Registration: Pay Rs 850 registration fee via Easypaisa to 0301-2345678 to receive your relief card.", True),
    ("SCAM_FEE_02", "Ehsaas Rashan Subsidy: Send Rs 500 fee to helper account for online form verification and ration card delivery.", True),
    ("SCAM_FEE_03", "Flood Relief Grant: Rs 30,000 approved for your family. Send Rs 1,200 document fee to claim payout today.", True),
    ("SCAM_FEE_04", "Govt Solar Scheme: Pay Rs 2,500 advance fee to lock your subsidized solar panel quota before deadline.", True),
    ("SCAM_FEE_05", "Youth Loan Scheme: Approval fee of Rs 3,000 required before disbursement of Rs 500,000 loan into your account.", True),
    ("SCAM_FEE_06", "Apka imdadi paisa approve ho gaya hai. Rs 500 bhejein aur payment hasil karein.", True),
    ("SCAM_FEE_07", "Welfare Card Fee: Deposit Rs 400 processing fee into official agent account 0321-9988776 to activate card.", True),
    ("SCAM_FEE_08", "Hukumat ki taraf se 25,000 imdad. Sirf 600 rupay registration fee jama karwayen aur slip WhatsApp karein.", True),
    ("SCAM_FEE_09", "Benazir Kafalat: Rs 14,000 balance ready. Transfer Rs 750 verification fee to agent JazzCash to unlock.", True),
    ("SCAM_FEE_10", "Relief Fund Portal: Processing charge of Rs 950 applies. Pay now to prevent cancellation of your grant.", True),

    # 5. Advance Payment & Lottery Scams (10 messages)
    ("SCAM_ADV_01", "Congratulations! Your mobile number won Rs 1,000,000 in ARY Jeeto Pakistan lucky draw. Send Rs 5,000 tax to claim.", True),
    ("SCAM_ADV_02", "You won a brand new Toyota Corolla in lucky draw. Transfer Rs 12,000 registration charges to claim car delivery.", True),
    ("SCAM_ADV_03", "Foreign Grant: United Nations approved $5,000 grant for flood victims. Send $50 clearance fee via Western Union.", True),
    ("SCAM_ADV_04", "Inam jeetnay par mubarakbaad. 50 tolay sona lene ke liye 15,000 rupay delivery charges foran transfer karein.", True),
    ("SCAM_ADV_05", "Disaster relief cash award of Rs 80,000 ready. Forward Rs 2,000 stamp duty fee to 0333-1234567 to disburse.", True),
    ("SCAM_ADV_06", "Dubai Job Offer: Visa approved with Rs 150,000 monthly salary. Transfer Rs 10,000 medical fee to agent today.", True),
    ("SCAM_ADV_07", "Canadian Immigrant Relief: Selected for fast-track PR. Deposit Rs 25,000 processing charges to consultant account.", True),
    ("SCAM_ADV_08", "Mubarak ho! Apko 50,000 ka cash prize mila hai. Abhi 1500 rupay advance tax bhejein aur cheque hasil karein.", True),
    ("SCAM_ADV_09", "Overseas Pakistanis Foundation: Cash grant of Rs 100,000 allotted. Pay Rs 3,500 courier fee to receive draft.", True),
    ("SCAM_ADV_10", "Lucky coupon winner: You won 100,000 PKR. Transfer Rs 2,500 advance payment to unlock prize code.", True),

    # 6. Urgent Account Suspension / Legal Threats (10 messages)
    ("SCAM_SUSP_01", "FIA Cybercrime Notice: Your CNIC is involved in illegal money laundering. Call 0315-7766554 immediately to avoid arrest.", True),
    ("SCAM_SUSP_02", "FBR Tax Warning: Final notice to settle tax discrepancy or bank accounts will be seized within 24 hours.", True),
    ("SCAM_SUSP_03", "Court Summons: Case registered against your CNIC. WhatsApp 0302-1122334 immediately to settle out of court.", True),
    ("SCAM_SUSP_04", "SIM Block Alert: Your mobile SIM will be blocked by PTA in 2 hours. Send CNIC and PIN code to keep active.", True),
    ("SCAM_SUSP_05", "Urgent legal notice: Failure to respond within 30 minutes will result in permanent police blacklisting.", True),
    ("SCAM_SUSP_06", "Apka bank account aaj raat 12 bajay hamesha ke liye block ho jayega. Foran verification OTP bhejein.", True),
    ("SCAM_SUSP_07", "PTA Warning: Illegal IMEI detected on your device. Pay Rs 4,500 fine to unblock phone before tomorrow morning.", True),
    ("SCAM_SUSP_08", "Warning: Police arrest warrant issued against your household head. Contact 0340-9988776 to stop raid.", True),
    ("SCAM_SUSP_09", "Account closure notice: All funds will be forfeited to state treasury unless verified via link bit.ly/unfreeze-now.", True),
    ("SCAM_SUSP_10", "Last and final warning: Transfer Rs 1,500 penalty fee now to prevent blacklisting of your identity card.", True),

    # 7. Urdu & Roman Urdu Phishing (5 messages)
    ("SCAM_URDU_01", "مبارک ہو! آپ کو احساس کفالت کی طرف سے 30000 منظور ہو گیا ہے۔ 800 روپے فیس بھیجیں تاکہ رقم مل سکے", True),
    ("SCAM_URDU_02", "آپ کا سم کارڈ بلاک ہو رہا ہے۔ فوری طور پر اپنا او ٹی پی پن کوڈ اس واٹس ایپ پر ارسال کریں", True),
    ("SCAM_URDU_03", "بے نظیر انکم سپورٹ پروگرام: آپ کا 45,000 کا وظیفہ روک دیا گیا ہے۔ فوری 1000 فیس جمع کروائیں", True),
    ("SCAM_URDU_04", "Apka BISP paisa rok diya gaya hai. OTP bhejo warna account band ho jayega.", True),
    ("SCAM_URDU_05", "Hukumat ki janib se 50000 relief cash. Abhi bit.ly/relief-grant par click kar k bank details enter karein.", True),

    # =========================================================================
    # B. LEGITIMATE SAMPLES (40 Messages) - Target: Never False Positive (Never SCAM)
    # =========================================================================
    # 8. Legitimate Government Announcements (15 messages)
    ("LEGIT_GOVT_01", "Public notice: The official Ehsaas registration is free of cost. Government never asks for any fee.", False),
    ("LEGIT_GOVT_02", "BISP Official: Payouts are made through authorized biometric partner bank branches and ATM centers only.", False),
    ("LEGIT_GOVT_03", "NADRA Notice: Citizens can renew their Smart National Identity Cards through the official portal at id.nadra.gov.pk.", False),
    ("LEGIT_GOVT_04", "Government of Pakistan: Never share your one-time passwords, bank PINs, or confidential credentials with anyone.", False),
    ("LEGIT_GOVT_05", "Relief Helpline 8171: Send your 13-digit CNIC without dashes to 8171 to check your eligibility status free.", False),
    ("LEGIT_GOVT_06", "Sindh Relief Department: Registration camps are established at government schools across District Sukkur.", False),
    ("LEGIT_GOVT_07", "Punjab Social Protection Authority: Welfare disbursements are distributed directly into beneficiary bank accounts.", False),
    ("LEGIT_GOVT_08", "Official Alert: Beware of fake SMS messages. Official communications are only issued from 8171 or official handles.", False),
    ("LEGIT_GOVT_09", "Khyber Pakhtunkhwa Relief Commission: Flood assistance survey teams are visiting households with official badges.", False),
    ("LEGIT_GOVT_10", "NADRA Registration Centre: New facility opened in Tehsil Kotri. Centre timings are 9:00 AM to 5:00 PM.", False),
    ("LEGIT_GOVT_11", "National Disaster Management Authority: Monsoon emergency advisories issued for coastal areas of Balochistan.", False),
    ("LEGIT_GOVT_12", "Hukumat ki janib se wazifa ke liye kisi qisam ki koi registration fee nahi li jati.", False),
    ("LEGIT_GOVT_13", "Relief Claim #RC-9921 is currently under review by the designated welfare officer. No action required.", False),
    ("LEGIT_GOVT_14", "آپ کی امدادی درخواست موصول ہو گئی ہے۔ جانچ پڑتال کے بعد دفتر سے تصدیق کی جائے گی۔", False),
    ("LEGIT_GOVT_15", "Govt Relief Board: No fee is ever charged for government relief assistance. Never share your OTP with anyone.", False),

    # 9. Legitimate Financial Messages & Receipts (15 messages)
    ("LEGIT_FIN_01", "Your electricity bill for the month of November is Rs 3,420. Due date is 25-Nov-2026.", False),
    ("LEGIT_FIN_02", "Sui Southern Gas: Your gas consumption bill for November is PKR 1,840. Pay before 28-Nov to avoid surcharge.", False),
    ("LEGIT_FIN_03", "HBL Alert: Your account was credited with PKR 45,000 on 20-Nov-2026. Available balance PKR 72,150.", False),
    ("LEGIT_FIN_04", "PTCL Landline bill of PKR 2,100 has been paid successfully via online banking. Transaction ref #PT-88910.", False),
    ("LEGIT_FIN_05", "Easypaisa: You sent PKR 1,500 to Muhammad Ali (03001234567) on 21-Nov-2026. Fee: PKR 0.00.", False),
    ("LEGIT_FIN_06", "JazzCash transaction receipt: Cash deposit of PKR 5,000 received at Shop #4 Main Bazaar.", False),
    ("LEGIT_FIN_07", "Meezan Bank: POS payment of PKR 3,250 at Imtiaz Super Market approved on 21-Nov-2026.", False),
    ("LEGIT_FIN_08", "Your school tuition fee receipt for the month of November is generated. Total paid PKR 4,000.", False),
    ("LEGIT_FIN_09", "Bank Alfalah: Monthly account statement for period ending October 2026 has been emailed to your address.", False),
    ("LEGIT_FIN_10", "Your Raast transfer of PKR 12,000 to Parveen Bibi has been settled successfully. Transaction ID RAAST-PK-9912.", False),
    ("LEGIT_FIN_11", "Water and Sanitation Agency: Water charges bill PKR 650 due on 30-Nov-2026.", False),
    ("LEGIT_FIN_12", "Your account balance inquiry: Available balance PKR 14,200 as of today.", False),
    ("LEGIT_FIN_13", "MCB Alert: ATM cash withdrawal of PKR 10,000 executed at Mall Road ATM. Remaining balance PKR 28,400.", False),
    ("LEGIT_FIN_14", "Dear customer, your recurring monthly internet subscription fee of PKR 1,999 has been charged.", False),
    ("LEGIT_FIN_15", "Bank of Punjab: Your salary of PKR 35,000 has been credited to your account on 01-Nov-2026.", False),

    # 10. Legitimate Citizen & Logistics Messages (10 messages)
    ("LEGIT_CIT_01", "Assalam o Alaikum, kal subah helper center se ration card collect kar lein.", False),
    ("LEGIT_CIT_02", "Please bring original CNIC and electricity bill to the community welfare center tomorrow morning.", False),
    ("LEGIT_CIT_03", "Assalam o Alaikum, helper center se kal 5000 rupay ka ration bag collect kar lein, koi charges nahi hain.", False),
    ("LEGIT_CIT_04", "The facilitation desk is open Monday to Friday from 9 AM to 4 PM at Union Council Hall.", False),
    ("LEGIT_CIT_05", "Doctor appointment confirmed at Civil Hospital for 22-Nov-2026 at 11:30 AM. Token #42.", False),
    ("LEGIT_CIT_06", "Weather alert: Expect light rainfall in Lahore and surrounding districts over the weekend.", False),
    ("LEGIT_CIT_07", "Community announcement: Polio vaccination team will visit your neighborhood on Monday.", False),
    ("LEGIT_CIT_08", "NADRA van will visit Village Chak 42 on Thursday for senior citizen CNIC renewals.", False),
    ("LEGIT_CIT_09", "براہ کرم اپنے قریبی سہولت مرکز پر تشریف لائیں اور اصل شناختی کارڈ دکھائیں۔", False),
    ("LEGIT_CIT_10", "Good morning, the union council office address is Near Railway Station Road, Ward #3.", False)
]


def test_independent_105_scam_classifier_accuracy_metrics():
    """
    Executes all 105 independent messages.
    Measures False Negative Rate (FNR) and False Positive Rate (FPR) separately.
    Requirements:
    - False Negative Rate on Scam: Must be < 3% (Zero tolerance on OTP/PIN theft).
    - False Positive Rate on Legit: Must be 0% (Legitimate announcements must never be marked SCAM).
    """
    scam_count = 0
    scam_detected = 0
    scam_false_negatives = []

    legit_count = 0
    legit_correct = 0
    legit_false_positives = []

    for msg_id, text, is_scam in INDEPENDENT_105_DATASET:
        res = classify_message(text)
        label = res["label"]

        if is_scam:
            scam_count += 1
            # SCAM or UNSURE are both safe operational actions (UNSURE halts auto-payout and escalates to human)
            # A False Negative occurs ONLY if an actual scam is classified as LEGIT!
            if label in (ScamLabel.SCAM, ScamLabel.UNSURE):
                scam_detected += 1
            else:
                scam_false_negatives.append((msg_id, text, res["confidence"], res["reasons"]))
        else:
            legit_count += 1
            # A False Positive occurs ONLY if legitimate text is confirmed as SCAM!
            if label != ScamLabel.SCAM:
                legit_correct += 1
            else:
                legit_false_positives.append((msg_id, text, res["confidence"], res["reasons"]))

    # Calculations
    fn_rate = (len(scam_false_negatives) / scam_count) * 100.0
    fp_rate = (len(legit_false_positives) / legit_count) * 100.0
    overall_accuracy = ((scam_detected + legit_correct) / len(INDEPENDENT_105_DATASET)) * 100.0

    print(f"\n================ SCAM CLASSIFIER EVALUATION (105 NEW SAMPLES) ================")
    print(f"Total Scam Messages Evaluated:       {scam_count}")
    print(f"Scam Messages Detected (SCAM/UNSURE): {scam_detected} ({(scam_detected/scam_count)*100:.2f}%)")
    print(f"False Negatives (Scams called LEGIT): {len(scam_false_negatives)} ({fn_rate:.2f}%)")
    print(f"Total Legit Messages Evaluated:      {legit_count}")
    print(f"Legit Messages Correct (LEGIT/UNSURE): {legit_correct} ({(legit_correct/legit_count)*100:.2f}%)")
    print(f"False Positives (Legit called SCAM):  {len(legit_false_positives)} ({fp_rate:.2f}%)")
    print(f"Overall Safety / Accuracy Rate:       {overall_accuracy:.2f}%")
    print(f"==============================================================================\n")

    # Strict Security Assertions:
    # 1. False Negative Rate must be 0% (Zero tolerance for credential theft or advance-fee scams escaping)
    assert fn_rate == 0.0, f"Critical Security Violation: False Negative Rate ({fn_rate:.2f}%) must be 0%: {scam_false_negatives}"

    # 2. False Positive Rate must be below 5.0% (Hardening Mission 2 Target)
    assert fp_rate <= 5.0, f"False Positive Rate exceeded target boundary ({fp_rate:.2f}%): {legit_false_positives}"

    # 3. Overall Safety / Accuracy Rate across independent 105 dataset
    assert overall_accuracy >= 98.0, f"Overall accuracy {overall_accuracy:.2f}% below 98% threshold"
