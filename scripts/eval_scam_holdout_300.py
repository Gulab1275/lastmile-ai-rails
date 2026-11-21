"""
Task 4: Brand-New Independent 300-Message Holdout Benchmark for Scam Classifier.
Evaluates the probabilistic scam & phishing classifier on a fresh 300-message holdout corpus:
- 150 Fraudulent / Phishing messages (Nastaliq Urdu, Roman Urdu, English, OTP/PIN theft, advance-fee, account closure)
- 120 Legitimate messages (Official announcements, utility bills, salary/remittances, anti-scam advisories)
- 30 Ambiguous messages requiring human officer review (Saying 'I am not sure')

Computes:
1. 3-class confusion matrix (True vs Predicted for SCAM, LEGIT, UNSURE)
2. Recall on Scam (must be >= 95%)
3. Precision on Scam (must be >= 90%)
4. False Positive Rate on Legit (must be <= 5%)
5. False Negative Rate on Scam (must be <= 5%)
6. Rate of UNSURE routed to Human Review (for both Scam and Legit)
7. OTP/PIN Credential Theft Recall (must be 100.0%)
"""
import sys
import os
import json
from collections import defaultdict

# Ensure repo root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.ai.scam import classify_message
from services.shared.schemas import ScamLabel

# ==============================================================================
# 300 BRAND-NEW HOLDOUT MESSAGES
# ==============================================================================

HOLDOUT_300 = [
    # --------------------------------------------------------------------------
    # Category 1: Nastaliq Urdu Fraudulent Relief Solicitations (30 Scam)
    # --------------------------------------------------------------------------
    ("مبارک ہو! آپ کا احساس ایمرجنسی ریلیف فنڈ 25,000 روپے منظور ہو گیا ہے۔ فوری 1000 روپے فیس جمع کروائیں تاکہ رقم بھیجی جا سکے۔", "SCAM"),
    ("بے نظیر کفالت پروگرام: آپ کے نام 35,000 روپے کی مالی امداد جاری کر دی گئی ہے۔ رقم وصول کرنے کے لیے ابھی 1500 رجسٹریشن فیس ادا کریں۔", "SCAM"),
    ("وزیراعظم ریلیف پیکج 2026: آپ کے شناختی کارڈ پر 50,000 روپے منظور ہو چکے ہیں۔ فوری واٹس ایپ پر رابطہ کر کے فائل چارجز ادا کریں۔", "SCAM"),
    ("سیلاب متاثرین ریلیف فنڈ: آپ کو حکومت کی طرف سے 40,000 روپے کی گرانٹ دی جا رہی ہے۔ فائل پروسیسنگ فیس 1200 روپے ایزی پیسہ کریں۔", "SCAM"),
    ("حکومتی راشن پروگرام: آپ کو 6 ماہ کا مفت راشن اور 20,000 نقد دیا جا رہا ہے۔ کارڈ ایکٹیویشن فیس 800 روپے فوری جمع کریں۔", "SCAM"),
    ("احساس تعلیمی وظائف: آپ کے بچوں کا 30,000 روپے کا وظیفہ آ گیا ہے۔ تصدیقی فیس 1000 روپے فوری بھیجیں۔", "SCAM"),
    ("قومی بچت ایمرجنسی سکیم: قرعہ اندازی میں آپ کا 1 لاکھ روپے کا انعام نکلا ہے۔ ٹیکس چارجز 5000 فوری جمع کروائیں۔", "SCAM"),
    ("بے نظیر سپورٹ: آپ کی ماہانہ قسط 14,000 روپے روک دی گئی ہے۔ بحالی کے لیے 700 روپے سروس چارجز ادا کریں۔", "SCAM"),
    ("وزیراعلیٰ یوتھ لون سکیم: آپ کا 2 لاکھ روپے کا بلاسود قرضہ پاس ہو گیا ہے۔ سیکورٹی ڈیپازٹ 3000 روپے ابھی بھیجیں۔", "SCAM"),
    ("حکومت سندھ راشن کارڈ: آپ کا راشن کارڈ بن گیا ہے۔ ہوم ڈلیوری چارجز 650 روپے ایڈوانس ادا کریں۔", "SCAM"),
    ("احساس ایمرجنسی کیش: 25,000 کی منظوری کے لیے اس لنک پر فارم پر کریں اور 500 فیس جمع کریں bit.ly/ehsaas2026", "SCAM"),
    ("بینظیر انکم سپورٹ 8171: مبارک ہو آپ کا امدادی چیک تیار ہے۔ ڈاک خرچہ 450 روپے جائز کیش کریں۔", "SCAM"),
    ("نادرا ریلیف رجسٹریشن: اپنا نام بی آئی ایس پی لسٹ میں شامل کروانے کے لیے 1500 روپے فیس 03001234567 پر بھیجیں۔", "SCAM"),
    ("حکومتی کسان ریلیف پیکیج: کسانوں کے لیے 50,000 کھاد سبسڈی جاری۔ کلیم کرنے کے لیے 2000 ایڈوانس چارجز دیں۔", "SCAM"),
    ("رمضان ریلیف فنڈ: خصوصی امدادی پیکج 15,000 روپے حاصل کرنے کے لیے 600 روپے فوری ٹرانسفر کریں۔", "SCAM"),
    ("قومی ریلیف ٹرسٹ: آپ کے خاندان کے لیے 45,000 امداد منظور۔ ریلیز کروانے کے لیے 1800 پروسیسنگ فیس ادا کریں۔", "SCAM"),
    ("بی آئی ایس پی وظیفہ 2026: اپنے بلاک شدہ فنڈز 30,000 روپے حاصل کرنے کے لیے فوری رابطہ کریں اور فیس جمع کریں۔", "SCAM"),
    ("وزیراعظم یوتھ اسکل فنڈ: ماہانہ 25,000 وظیفہ حاصل کریں۔ رجسٹریشن فیس 1200 روپے فوری بھیجیں۔", "SCAM"),
    ("احساس نشوونما: بچوں کے غذائی فنڈ کی رقم 18,000 منظور۔ فوری ریلیز کے لیے 900 روپے بینک ٹرانسفر کریں۔", "SCAM"),
    ("بے نظیر لیبر ویلفیئر فنڈ: مزدور بھائیوں کے لیے 35,000 کی مالی گرانٹ۔ چالان فیس 1000 جمع کروائیں۔", "SCAM"),
    ("سندھ پیپلز ریلیف پروگرام: گھریلو اخراجات کے لیے 28,000 منظور۔ تصدیق کے لیے 750 روپے جائز کیش کریں۔", "SCAM"),
    ("بلوچستان ریلیف ایمرجنسی: سردی کی گرانٹ 22,000 حاصل کرنے کے لیے ابھی 1100 ڈاک خرچ ارسال کریں۔", "SCAM"),
    ("خیبر پختونخوا امدادی سکیم: 30,000 نقد کی ترسیل کے لیے ایڈوانس ٹیکس 1500 روپے جمع کروائیں۔", "SCAM"),
    ("پنجاب خدمت کارڈ: آپ کی خصوصی امداد 40,000 روپے جاری۔ ایکٹیویشن کوڈ حاصل کرنے کے لیے 850 روپے فیس بھیجیں۔", "SCAM"),
    ("احساس لائیو اسٹاک فنڈ: مویشی پال کسانوں کے لیے 60,000 گرانٹ۔ رجسٹریشن فیس 2500 روپے ادا کریں۔", "SCAM"),
    ("حکومت پاکستان خصوصی معذور امداد: 50,000 روپے کی ویلفیئر گرانٹ منظور۔ پراسیسنگ فیس 1200 جمع کریں۔", "SCAM"),
    ("نادرا ڈیتھ سرٹیفکیٹ ویلفیئر گرانٹ: بیواؤں کے لیے 40,000 روپے منظور۔ 1000 رجسٹریشن فیس دیں۔", "SCAM"),
    ("قومی آفات مینجمنٹ: بارش اور طوفان کا معاوضہ 35,000 تیار ہے۔ کلیرنس فیس 1400 روپے ادا کریں۔", "SCAM"),
    ("بے نظیر اسکالرشپ لسٹ 2026: طلبہ کے لیے 20,000 وظیفہ۔ ڈرافٹ فیس 600 روپے فوری بھیجیں۔", "SCAM"),
    ("احساس ہنر مند پروگرام: مفت سلائی مشین اور 25,000 نقد۔ کورئیر فیس 950 روپے فوری جمع کروائیں۔", "SCAM"),

    # --------------------------------------------------------------------------
    # Category 2: Roman Urdu Advance Fee & Money Transfer Scams (30 Scam)
    # --------------------------------------------------------------------------
    ("Aapko Hukumat ki taraf se 30,000 ka imdadi paisa approve ho gaya hai. Abhi 1000 fee jama karein to payment release hogi.", "SCAM"),
    ("Muaziz sarif, aapka BISP ka 35000 ka wazifa aya hua hai, 1500 advance tax send karein taake paisa transfer ho sake.", "SCAM"),
    ("Ehsaas Program 2026: 25000 cash grant hasil karne k liye foran 800 rupay registration fee jazzcash karein.", "SCAM"),
    ("Apka 40000 relief check tayyar hai. Dispatch k liye 650 courier charges is number pe foran bhejein.", "SCAM"),
    ("Mubarak ho! Apka ration card aur 15000 emergency cash approve hua hai. 500 processing fee transfer karein.", "SCAM"),
    ("Benazir Kafalat: Apke cnic par 28000 aya hai, clearance fee 1200 rupay easypaisa karein foran.", "SCAM"),
    ("Disaster relief fund: 50,000 cash transfer k liye 2000 government tax jama karwayen.", "SCAM"),
    ("PM Relief Package: Aapka 35000 cash grant qualify ho chuka hai. 1000 fee bhejein aur claim karein.", "SCAM"),
    ("Apka monthly wazifa block hai. Unblock karwane k liye 750 rupay service fee ada karein.", "SCAM"),
    ("Ehsaas Emergency Cash: Rs 25000 approve. Pay Rs 500 verification fee to 03001234567 immediately.", "SCAM"),
    ("Assalam o alaikum, BISP office se bol raha hun, apka 45000 aya hai, 1500 file charges foran bhejo.", "SCAM"),
    ("Hukumat ki janib se 50000 ka muawza manzoor. 1800 stamp duty fee jama karwayen.", "SCAM"),
    ("Apka flood relief fund 30000 aya hai. 900 rupees advance fee send karein release k liye.", "SCAM"),
    ("Benazir income support 8171: 25000 k liye 700 rupay delivery charges ada karein.", "SCAM"),
    ("Ehsaas Taleemi Wazifa: Bachon ka 24000 aya hai, 1000 admission fee bhejein foran.", "SCAM"),
    ("Apka kamyab jawan loan 100,000 pass ho gaya hai. 3000 processing charges transfer karein.", "SCAM"),
    ("Muaziz shehri, ration subsidy 10000 hasil karne k liye 400 card fee jazzcash karein.", "SCAM"),
    ("BISP relief payment: 32000 transfer karne k liye 1100 service charges jama karein.", "SCAM"),
    ("Ehsaas Kafalat: Apka 14000 wazifa release hone wala hai, 500 bank charges bhejein.", "SCAM"),
    ("Sarkari imdadi scheme: 40000 emergency fund k liye 1400 challan fee foran jama karain.", "SCAM"),
    ("Apka housing subsidy 50000 aya hai. 2000 token fee pay karein aur ghar bethe paisa lein.", "SCAM"),
    ("Benazir financial aid: 35000 claim karein. Sirf 850 registration charges bhejein.", "SCAM"),
    ("Ehsaas Rashan: 6 mahine ka ration aur 15000 cash. 600 delivery fee send karein.", "SCAM"),
    ("Apka labour card 25000 grant approve. 750 activation fee foran bhejein.", "SCAM"),
    ("Flood compensation 40000 approved. Pay 1500 verification fee to receive payment.", "SCAM"),
    ("BISP double kist 28000 aya hai. 1000 clearance tax jama karwayen abhi.", "SCAM"),
    ("Ehsaas winter relief: 20000 cash grant k liye 650 charges bhejo.", "SCAM"),
    ("PM Youth grant 30000 qualified. Send 1200 fee to officer on WhatsApp.", "SCAM"),
    ("Apka NADRA relief grant 35000 pass ho gaya. 950 file fee easypaisa karein.", "SCAM"),
    ("Sindh relief scheme: 25000 transfer k liye 800 registration charges bhejein foran.", "SCAM"),

    # --------------------------------------------------------------------------
    # Category 3: English Fake Grants, Disaster Payouts & Lotteries (30 Scam)
    # --------------------------------------------------------------------------
    ("Congratulations! You have been selected for World Bank Pakistan Flood Relief Grant of $1,000. Send $25 processing fee to claim.", "SCAM"),
    ("UN Emergency Relief Agency: You are entitled to PKR 75,000 financial support. Transfer PKR 2,500 clearance tax to release funds.", "SCAM"),
    ("Government Public Relief: Your national cash aid of Rs 50,000 is approved. Click bit.ly/claim-grant-26 and pay Rs 1000 fee.", "SCAM"),
    ("You won PKR 500,000 in the Ehsaas 2026 Annual Lucky Draw! Deposit PKR 10,000 government tax to claim your cash award.", "SCAM"),
    ("International Humanitarian Relief: You have a pending disbursement of Rs 60,000. Submit Rs 1,500 administrative fee now.", "SCAM"),
    ("Official Notification: Pakistan Relief Trust has credited Rs 40,000 to your CNIC. Pay Rs 1,200 stamp duty to unfreeze.", "SCAM"),
    ("You have been awarded the Prime Minister Special Relief Grant of Rs 100,000. Contact our agent and send Rs 3,000 processing fee.", "SCAM"),
    ("National Welfare Fund: Rs 35,000 emergency grant approved for your family. Send Rs 850 courier charges to receive payment.", "SCAM"),
    ("Congratulations! Your mobile number won 2nd prize in Government Welfare Lottery. Deposit Rs 5,000 registration fee.", "SCAM"),
    ("BISP Global Partner Fund: Eligible citizens receive Rs 50,000 cash aid. Transfer Rs 1,800 audit charges to claim immediately.", "SCAM"),
    ("Disaster Payout Notification: Claim your approved grant of Rs 45,000. Send Rs 1,500 transfer fee to agent WhatsApp.", "SCAM"),
    ("Emergency Cash Disbursement: Rs 30,000 allocated to your household. Pay Rs 700 bank transaction fee to release.", "SCAM"),
    ("Federal Relief Authority: Your flood damage compensation of Rs 80,000 is approved. Send Rs 2,500 filing fee today.", "SCAM"),
    ("Asian Development Relief: Pakistan rural support grant of Rs 55,000 approved. Remit Rs 1,750 processing charges.", "SCAM"),
    ("Congratulations! You won Rs 150,000 in Benazir Lucky Draw. Send Rs 4,500 advance fee to receive full amount.", "SCAM"),
    ("PM Youth Relief Initiative: You are selected for Rs 40,000 grant. Pay Rs 1,200 verification fee via JazzCash.", "SCAM"),
    ("National Poverty Alleviation: Rs 35,000 approved for your household. Send Rs 900 document fees to proceed.", "SCAM"),
    ("Urgent Relief Disbursement: Rs 25,000 grant awaits your collection. Pay Rs 600 activation charges immediately.", "SCAM"),
    ("Global Charity Coalition: Rs 65,000 flood grant assigned to your CNIC. Transfer Rs 2,000 government levy to receive funds.", "SCAM"),
    ("You are among 100 lucky citizens selected for Rs 100,000 relief prize. Deposit Rs 3,500 claim fee today.", "SCAM"),
    ("BISP Special Ramadan Aid: Rs 30,000 approved for your family. Send Rs 800 delivery fee to dispatcher.", "SCAM"),
    ("Government Small Business Grant: Rs 75,000 sanctioned for your CNIC. Transfer Rs 2,200 loan guarantee fee.", "SCAM"),
    ("UNHCR Community Support: Rs 50,000 assistance package ready. Remit Rs 1,600 clearance fee to release.", "SCAM"),
    ("National Ration Subsidy: Rs 20,000 cash aid approved. Pay Rs 500 card fee to bit.ly/ration-apply", "SCAM"),
    ("Emergency Medical Relief Fund: Rs 45,000 sanctioned. Pay Rs 1,400 verification fee to release hospital grant.", "SCAM"),
    ("You won Rs 200,000 in Prime Minister Relief Lucky Draw. Send Rs 5,000 tax charges to claim prize.", "SCAM"),
    ("Kafalat Cash Disbursement: Rs 35,000 approved. Transfer Rs 1,000 handling fee to bank account 01928374.", "SCAM"),
    ("Pakistan Welfare Board: Rs 40,000 emergency grant approved. Send Rs 1,300 clearance charges immediately.", "SCAM"),
    ("Congratulations! You are selected for Overseas Pakistanis Relief Grant of Rs 60,000. Send Rs 1,800 fee.", "SCAM"),
    ("Disaster Assistance Payout: Rs 30,000 ready for bank deposit. Remit Rs 750 release fee today.", "SCAM"),

    # --------------------------------------------------------------------------
    # Category 4: OTP and PIN Credential Theft (30 Scam) - MUST BE 100% DETECTED
    # --------------------------------------------------------------------------
    ("BISP 8171: Apka 25,000 wazifa aya hai. Verification k liye apna OTP code foran bhejein.", "SCAM"),
    ("Ehsaas Emergency Alert: Please share your 6-digit OTP code to confirm your relief grant disbursement.", "SCAM"),
    ("آپ کا بی آئی ایس پی کا 25000 آ گیا ہے، ابھی اپنا پن کوڈ واٹس ایپ کریں تاکہ رقم آپ کے اکاؤنٹ میں ٹرانسفر ہو سکے۔", "SCAM"),
    ("Dear citizen, your relief wallet is suspended. Send your ATM PIN immediately to restore access.", "SCAM"),
    ("NADRA Verification: Your CNIC registration requires security confirmation. Reply with your one-time password OTP.", "SCAM"),
    ("اپنا ون ٹائم پاسورڈ (OTP) فوری میسج کریں ورنہ آپ کا امدادی اکاؤنٹ 24 گھنٹے میں بند کر دیا جائے گا۔", "SCAM"),
    ("Bank Alfalah Alert: Enter your 4-digit secret PIN code to receive your government relief payment.", "SCAM"),
    ("JazzCash Relief: Your Rs 14,000 Kafalat payment is waiting. Reply with the 4-digit PIN you just received.", "SCAM"),
    ("Easypaisa Security: Send your login PIN code to authorize government emergency subsidy transfer.", "SCAM"),
    ("بینک مینیجر: آپ کا احساس اکاؤنٹ ان بلاک کرنے کے لیے اپنے موبائل پر آنے والا کوڈ اور پاسورڈ بتائیں۔", "SCAM"),
    ("Security Alert: We noticed unauthorized login on your relief wallet. Share your verification OTP to secure it.", "SCAM"),
    ("BISP payment confirmation: Send your login password and OTP code to receive Rs 35,000 grant.", "SCAM"),
    ("Aapke mobile par 6 digit ka OTP aya hoga, foran batayein taake 25000 aapke account me bhej sakein.", "SCAM"),
    ("Dear customer, your bank account will be blocked today. Please send your OTP password now.", "SCAM"),
    ("Security Alert: Suspicious login detected. Reply with your 6-digit PIN code to secure your account.", "SCAM"),
    ("Your account is temporarily locked. Share your verification OTP code immediately to restore access.", "SCAM"),
    ("حکومتی وظیفہ ٹرانسفر: اپنے موبائل پر موصول ہونے والا پن نمبر فوری بھیجیں تاکہ رقم اکاؤنٹ میں منتقل ہو سکے۔", "SCAM"),
    ("Relief Fund Support: Please reply with your secret ATM PIN number to verify your identity.", "SCAM"),
    ("Muaziz Sarif, apna 4-hadsati secret PIN kisi ko mat batayein sirf is official number par reply karein.", "SCAM"),
    ("BISP Verification Unit: Share your CNIC and SMS verification code OTP to release your Rs 30,000 aid.", "SCAM"),
    ("Urgent: Your relief application is approved. Provide your mobile banking passcode to verify payment.", "SCAM"),
    ("آپ کے شناختی کارڈ پر 40 ہزار کی امداد آئی ہے، تصدیق کے لیے ابھی اپنا سیکیورٹی کوڈ بتائیں۔", "SCAM"),
    ("HBL Konnect Relief: Reply with the OTP received on your SIM to confirm cash withdrawal.", "SCAM"),
    ("BISP Kafalat 8171: Send your 4-digit PIN to our helpline agent on WhatsApp to collect stipend.", "SCAM"),
    ("Dear user, send your one time verification password (OTP) to process your urgent cash grant.", "SCAM"),
    ("اپنے احساس کفالت کارڈ کا خفیہ پن کوڈ درج کریں تاکہ رقم فوری بھیجی جا سکے۔", "SCAM"),
    ("Govt Relief Disbursement: Reply with your credential verification code to unlock funds.", "SCAM"),
    ("Apna easypaisa account PIN verify karwayen wrna apka relief payment cancel hojaye ga.", "SCAM"),
    ("Bank alert: To confirm government relief deposit of Rs 25,000, send your card PIN code.", "SCAM"),
    ("Emergency aid verification: Forward the 6-digit code received via SMS to complete transfer.", "SCAM"),

    # --------------------------------------------------------------------------
    # Category 5: Account Suspension & High-Pressure Intimidation Scams (30 Scam)
    # --------------------------------------------------------------------------
    ("URGENT: Your BISP relief account has been frozen due to suspicious activity. Contact immediately to restore.", "SCAM"),
    ("آخری انتباہ: آپ کا شناختی کارڈ فوری بلاک کیا جا رہا ہے۔ جرمانے سے بچنے کے لیے ابھی رابطہ کریں۔", "SCAM"),
    ("Your relief grant will be permanently forfeited if not claimed within 2 hours. Call 03009988776 immediately.", "SCAM"),
    ("Warning: Legal action will be initiated against your CNIC for unclaimed government funds. Resolve immediately.", "SCAM"),
    ("Apka Ehsaas account foran band kiya ja raha hai. Last date today! Unblock karwane k liye foran contact karein.", "SCAM"),
    ("Final Notice: Your relief disbursement of Rs 35,000 expires tonight. Immediate response required.", "SCAM"),
    ("آپ کا بینک اکاؤنٹ عارضی طور پر معطل کر دیا گیا ہے۔ بحالی کے لیے ابھی اس لنک پر کلک کریں bit.ly/bank-fix", "SCAM"),
    ("URGENT NOTICE: Government audit team found irregularities in your claim. Settle immediately to avoid arrest.", "SCAM"),
    ("Apka CNIC block ho raha hai. Foran apna bank PIN verify karein wrna account band hojaye ga.", "SCAM"),
    ("Account Suspension Alert: Your relief payment wallet is deactivated. Call our emergency helpline now.", "SCAM"),
    ("Hurry! Only 5 relief grants remaining in your union council. Apply immediately at tinyurl.com/pak-relief-26", "SCAM"),
    ("آخری تاریخ آج ہے! اگر آپ نے آج رجسٹریشن نہ کروائی تو آپ کو آئندہ کبھی حکومتی امداد نہیں ملے گی۔", "SCAM"),
    ("Immediate action required: Your pending grant of Rs 50,000 will be cancelled at midnight.", "SCAM"),
    ("FBR & Relief Audit: Fine of Rs 15,000 imposed on your CNIC. Contact officer immediately to waive.", "SCAM"),
    ("Apka relief allowance freeze kar diya gaya hai. Foran 800 unfreeze fee transfer karein.", "SCAM"),
    ("Final warning: Your identity verification has failed. Complete online check within 1 hour or account closed.", "SCAM"),
    ("فوری نوٹس: آپ کا راشن کارڈ معطل ہو گیا ہے۔ بحالی کے لیے فوری رابطہ کریں ورنہ راشن بند کر دیا جائے گا۔", "SCAM"),
    ("Your relief stipend is placed on hold by treasury. Urgent verification required to avoid cancellation.", "SCAM"),
    ("Account closed alert: Your relief fund transfer failed. Click bit.ly/unfreeze-aid to update bank details.", "SCAM"),
    ("Police and FIA notice: Your CNIC is flagged for illegal relief claim. Settle with officer immediately.", "SCAM"),
    ("Apka BISP wazifa hamesha k liye khatam ho raha hai. Bachane k liye abhi contact karein.", "SCAM"),
    ("URGENT: Last chance to receive Rs 25,000 disaster relief grant. Deadline expires in 30 minutes.", "SCAM"),
    ("انتباہ: آپ کا کفالت اکاؤنٹ بلاک کر دیا گیا ہے۔ ان بلاک کے لیے فوری طور پر رابطہ کریں۔", "SCAM"),
    ("Court Notice: Fine issued against your CNIC for duplicate relief claim. Call emergency desk immediately.", "SCAM"),
    ("Your relief payment file is being archived. Respond immediately to keep your benefit active.", "SCAM"),
    ("Apka account permanently suspend ho chuka hai. Reactivate karne k liye foran call karein.", "SCAM"),
    ("Urgent security alert: Unauthorized attempt to withdraw your relief cash. Act immediately to secure.", "SCAM"),
    ("آخری موقع: حکومت کا خصوصی پیکیج حاصل کرنے کے لیے ابھی کال کریں۔ بعد میں کوئی درخواست قبول نہیں ہوگی۔", "SCAM"),
    ("Your relief aid of Rs 30,000 is marked for return to treasury. Claim within 4 hours immediately.", "SCAM"),
    ("Warning: Unverified CNIC detected. Relief benefits suspended. Update immediately at tinyurl.com/cnic-fix", "SCAM"),

    # --------------------------------------------------------------------------
    # Category 6: Legitimate Government Relief Announcements & Status (30 Legit)
    # --------------------------------------------------------------------------
    ("محکمہ ریلیف و بحالی: آپ کی امدادی درخواست موصول ہو گئی ہے۔ جانچ پڑتال کے بعد دفتر سے تصدیق کی جائے گی۔", "LEGIT"),
    ("BISP 8171: Your application for Benazir Kafalat has been recorded. Tracking ID: 991823. Check status at 8171.bisp.gov.pk", "LEGIT"),
    ("حکومت سندھ: سیلاب متاثرین کی رجسٹریشن کا آغاز تحصیل سطح کے سہولت مراکز پر ہو چکا ہے۔ اصل شناختی کارڈ ہمراہ لائیں۔", "LEGIT"),
    ("Relief Claim #RC-9921 is currently under review by the designated welfare officer. No action required.", "LEGIT"),
    ("بینظیر انکم سپورٹ پروگرام: نئی قسط کی ادائیگی قریبی نامزد ادائیگی مرکز یا بینک سے شناختی کارڈ دکھا کر حاصل کریں۔", "LEGIT"),
    ("NADRA Public Notice: Mobile registration vans are visiting Badin and Thatta districts this week for free CNIC renewal.", "LEGIT"),
    ("محکمہ بہبود آبادی: خصوصی افراد کے لیے امدادی وظائف کی فہرست ضلعی دفتر میں آویزاں کر دی گئی ہے۔", "LEGIT"),
    ("Government of Pakistan: National Socio-Economic Registry (NSER) survey teams are visiting households. Survey is free.", "LEGIT"),
    ("آپ کی کفالت درخواست کی جانچ پڑتال مکمل ہو چکی ہے۔ تفصیلات کے لیے قریبی بے نظیر دفتر تشریف لائیں۔", "LEGIT"),
    ("Federal Relief Board: Verification of flood damage compensation forms is underway. Field officers will inspect sites.", "LEGIT"),
    ("احساس راشن پروگرام: راشن سبسڈی حاصل کرنے کے لیے اپنا شناختی کارڈ نمبر 8171 پر ایس ایم ایس کریں۔", "LEGIT"),
    ("Government Relief Secretariat: Eligible families can visit designated distribution points from Monday to Friday.", "LEGIT"),
    ("محکمہ کسان بہبود: کسان کارڈ ہولڈرز کے لیے کھاد سبسڈی اسکیم کا شیڈول جاری کر دیا گیا ہے۔", "LEGIT"),
    ("BISP Official: Monthly stipend disbursements for Q4 2026 will commence from the 1st of next month through biometric ATMs.", "LEGIT"),
    ("حکومت پاکستان: غربت مٹاؤ پروگرام کے تحت مفت تکنیکی کورسز میں داخلے شروع ہو گئے ہیں۔", "LEGIT"),
    ("Provincial Disaster Management Authority: Monsoon relief camps established across 12 union councils. Medical aid available.", "LEGIT"),
    ("آپ کا ریلیف کیس نمبر 8821 آفیسر کو تفویض کر دیا گیا ہے۔ تصدیقی کال 051 پر مشتمل سرکاری نمبر سے آئے گی۔", "LEGIT"),
    ("National Disaster Relief: Compensation cheques will be distributed directly by Deputy Commissioner office.", "LEGIT"),
    ("حکومت خیبر پختونخوا: بے روزگار نوجوانوں کے لیے بلاسود قرضوں کے فارم بینک آف خیبر سے مفت حاصل کریں۔", "LEGIT"),
    ("Welfare Directorate: Biometric reverification is scheduled for citizens whose thumb impressions failed at ATM.", "LEGIT"),
    ("بینظیر تعلیمی وظائف: اسکول حاضری 70 فیصد سے زائد ہونے پر وظیفہ خودکار طور پر اکاؤنٹ میں شامل ہو جائے گا۔", "LEGIT"),
    ("Official Helpline Notice: Call 0800-26477 toll-free for all inquiries related to government cash relief assistance.", "LEGIT"),
    ("محکمہ زراعت: زرعی ایمرجنسی پروگرام کے تحت بیجوں کی تقسیم بلا معاوضہ کی جائے گی۔", "LEGIT"),
    ("State Bank of Pakistan: Microfinance banks are authorized to disburse government relief cash with zero deductions.", "LEGIT"),
    ("آپ کی شکایت نمبر 44102 کا ازالہ کر دیا گیا ہے۔ مزید معلومات کے لیے ضلعی شکایت پورٹل پر رجوع کریں۔", "LEGIT"),
    ("Ehsaas Nashonuma: Registration for pregnant and lactating mothers is open at basic health units.", "LEGIT"),
    ("حکومتی اعلان: ریلیف پروگرام سے متعلق کسی بھی شکایت کے لیے وزیراعظم سٹیزن پورٹل پر اندراج کروائیں۔", "LEGIT"),
    ("Disaster Recovery Cell: Reconstruction grants will be credited directly to verified bank accounts after joint survey.", "LEGIT"),
    ("نادرا سینٹر کراچی: شہریوں کی سہولت کے لیے میگا سینٹرز ہفتے میں 6 دن چوبیس گھنٹے کھلے ہیں۔", "LEGIT"),
    ("Ministry of Poverty Alleviation: Comprehensive eligibility criteria published on official portal poverty.gov.pk", "LEGIT"),

    # --------------------------------------------------------------------------
    # Category 7: Legitimate Utility Bills & Fee Receipts (30 Legit)
    # --------------------------------------------------------------------------
    ("Your electricity bill for the month of November is Rs 3,420. Due date is 25-Nov-2026. Payable at any authorized bank.", "LEGIT"),
    ("Sui Southern Gas: Your gas consumption charges bill for consumer #982103 is PKR 1,150. Due date: 28-Nov-2026.", "LEGIT"),
    ("K-Electric Bill Alert: Account 040001234567. Current bill PKR 4,890. Payment received on 18-Nov: PKR 4,890. Balance: 0.", "LEGIT"),
    ("Water and Sanitation Agency (WASA): Water charges bill PKR 650 due on 30-Nov-2026. Please pay before due date.", "LEGIT"),
    ("PTCL Landline & Broadband: Bill for telephone #021-34567890 is PKR 2,850. Due date: 22-Nov-2026. Online receipt generated.", "LEGIT"),
    ("Your school tuition fee receipt for the month of November is generated. Total paid PKR 4,000. Balance PKR 0.00.", "LEGIT"),
    ("آپ کا بجلی کا بل برائے ماہ نومبر مبلغ 2,450 روپے ہے۔ آخری تاریخ 26 نومبر ہے۔ بروقت بل ادا کریں۔", "LEGIT"),
    ("LESCO Bill: Consumer 1928374. Amount payable within due date: PKR 3,820. Amount after due date: PKR 4,100.", "LEGIT"),
    ("SSGC Gas Bill: Consumer #881920. Total charges bill PKR 920. Paid successfully via 1Link. Receipt #10928.", "LEGIT"),
    ("Karachi Water Board: Consumer #40291. Water and sewerage charges bill PKR 850 due on 27-Nov-2026.", "LEGIT"),
    ("IESCO Electricity Bill: Reference #09123849102. Bill amount PKR 5,430. Due date is 24-Nov-2026.", "LEGIT"),
    ("HESCO Power Bill: Consumer #339102. Total amount PKR 2,100 due by 29-Nov-2026. Pay at any Post Office.", "LEGIT"),
    ("آپ کا گیس کا بل واجب الادا رقم 1,340 روپے ہے۔ آخری تاریخ سے پہلے ادا کر کے جرمانے سے بچیں۔", "LEGIT"),
    ("College tuition fee payment of PKR 8,500 received. Transaction reference: FEE-NOV-9918. Fee receipt issued.", "LEGIT"),
    ("K-Electric duplicate bill: Account #040009821. Amount payable PKR 3,120. Due date is 25-Nov-2026.", "LEGIT"),
    ("PESCO Electricity Bill: Meter #88192. Current month consumption 180 units. Bill amount PKR 4,200.", "LEGIT"),
    ("GEPCO Bill Notification: Consumer #772910. Bill amount PKR 2,900 due on 23-Nov-2026. Status: Unpaid.", "LEGIT"),
    ("QESCO Bill: Reference #551920. Amount payable PKR 1,800. Due date: 30-Nov-2026.", "LEGIT"),
    ("FESCO Power: Consumer #119283. Electricity charges bill PKR 3,650 due on 27-Nov-2026.", "LEGIT"),
    ("Telenor Postpaid Bill: Account #03451234567. Total charges bill PKR 1,450. Due date is 25-Nov-2026.", "LEGIT"),
    ("Jazz Postpaid Invoice: Bill for mobile number 03009876543 is PKR 1,820. Payment due by 28-Nov-2026.", "LEGIT"),
    ("Zong Postpaid: Bill amount PKR 980 for billing cycle November 2026. Due date is 26-Nov-2026.", "LEGIT"),
    ("Ufone Bill Alert: Monthly bill PKR 1,120. Payment received with thanks. Available balance PKR 0.00.", "LEGIT"),
    ("آپ کے پانی کے کنکشن کا ماہانہ بل 400 روپے موصول ہو چکا ہے۔ رسید نمبر 88291 ہے۔", "LEGIT"),
    ("Hospital consultation fee receipt: Dr. Tahir Clinic. Total paid PKR 1,500. Receipt issued to patient Parveen.", "LEGIT"),
    ("NADRA Smart Card processing fee receipt: Fee: PKR 1,500. Tracking ID: 1092837. Normal delivery in 15 days.", "LEGIT"),
    ("Driving license renewal fee receipt: Amount paid PKR 1,250. Verification complete. Token #88192.", "LEGIT"),
    ("Motorcycle token tax payment receipt: Tax paid PKR 1,000 for year 2026. Registration #KHI-8891.", "LEGIT"),
    ("Property tax challan bill: Town Municipal Corporation. Bill amount PKR 2,400 due on 31-Dec-2026.", "LEGIT"),
    ("Solid Waste Management: Sanitation fee bill PKR 300 for November 2026. Please collect receipt from collector.", "LEGIT"),

    # --------------------------------------------------------------------------
    # Category 8: Legitimate Bank Transaction Alerts & Remittances (30 Legit)
    # --------------------------------------------------------------------------
    ("Easypaisa: You sent PKR 1,500 to Muhammad Ali (03001234567) on 21-Nov-2026. Fee: PKR 0.00. New balance: PKR 8,450.", "LEGIT"),
    ("JazzCash: Rs. 2,000 sent to Fatima Bibi (03019876543) via mobile transfer. Fee: Rs 0.00. Trans ID: 09182374.", "LEGIT"),
    ("HBL Alert: Your account balance inquiry: Available balance PKR 14,200 as of today.", "LEGIT"),
    ("Meezan Bank: Inward remittance of PKR 25,000 credited to account ending 4821 on 20-Nov-2026. Reference: REM-99182.", "LEGIT"),
    ("Bank Alfalah: Monthly salary credited to your account PKR 35,000. Available balance PKR 42,100.", "LEGIT"),
    ("UBL Alert: Cash deposit received of PKR 10,000 at Gulshan branch. Updated balance PKR 18,500.", "LEGIT"),
    ("MCB Bank: ATM cash withdrawal of PKR 5,000 performed on 21-Nov-2026 at 14:32. Available balance PKR 9,200.", "LEGIT"),
    ("Allied Bank: Funds transfer of PKR 3,000 received from Tariq Mahmood. Reference: FT2632501928.", "LEGIT"),
    ("آپ کے بینک اکاؤنٹ میں ماہانہ تنخواہ 30,000 روپے منتقل کر دی گئی ہے۔ موجودہ بیلنس 35,400 روپے ہے۔", "LEGIT"),
    ("Standard Chartered: Online bill payment of PKR 3,420 to K-Electric successful. Fee: PKR 0.00.", "LEGIT"),
    ("Askari Bank: POS transaction of PKR 2,150 at Imtiaz Super Market approved on 21-Nov-2026.", "LEGIT"),
    ("Bank of Punjab: Kisan relief subsidy PKR 12,000 credited to account ending 9102. Available balance PKR 14,800.", "LEGIT"),
    ("National Bank of Pakistan (NBP): Pension credited PKR 22,500 for the month of November 2026.", "LEGIT"),
    ("Faysal Bank: Account statement summary: Total credits PKR 45,000, Total debits PKR 28,000. Balance PKR 17,000.", "LEGIT"),
    ("BankIslami: Interbank fund transfer (IBFT) of PKR 4,500 sent to Ahmed Khan. Transaction successful.", "LEGIT"),
    ("Habib Metropolitan Bank: Term deposit profit of PKR 3,200 credited to savings account ending 3381.", "LEGIT"),
    ("JS Bank: Cheque #091823 for PKR 15,000 cleared successfully. Account balance PKR 26,400.", "LEGIT"),
    ("Soneri Bank: ATM funds transfer of PKR 2,000 completed. Fee: PKR 0.00. Available balance PKR 7,900.", "LEGIT"),
    ("آپ کے ایزی پیسہ اکاؤنٹ میں 5000 روپے موصول ہوئے۔ بھیجنے والے کا نام: عبداللہ خان۔ نیا بیلنس: 8200 روپے۔", "LEGIT"),
    ("Al Baraka Bank: Standing instruction executed: Monthly savings installment PKR 2,000 transferred.", "LEGIT"),
    ("Summit Bank: Utility bill payment of PKR 1,850 completed for SSGC. Confirmation #99182.", "LEGIT"),
    ("Samba Bank: Mobile top-up of PKR 500 successful for number 03001234567. Fee: PKR 0.00.", "LEGIT"),
    ("Dubai Islamic Bank: Debit card retail transaction of PKR 1,420 approved. Balance PKR 21,300.", "LEGIT"),
    ("First Women Bank: Monthly stipend of PKR 8,000 received from Department of Social Welfare.", "LEGIT"),
    ("Sindh Bank: Government relief payment of PKR 14,000 credited to BISP beneficiary account ending 7712.", "LEGIT"),
    ("Easypaisa: Cash deposit of PKR 3,000 at retail agent shop successful. Current balance PKR 4,600.", "LEGIT"),
    ("JazzCash: Payment of PKR 850 made to WASA Hyderabad. Transaction fee: Rs 0.00.", "LEGIT"),
    ("Upaisa: Fund transfer of PKR 1,000 completed to mobile number 03339876543. Available balance PKR 2,400.", "LEGIT"),
    ("SadaPay: You received PKR 2,500 from Zainab Bibi. Money added to your account instantly.", "LEGIT"),
    ("NayaPay: PKR 1,200 sent to grocery merchant. Transaction ID: NP-881923. Fee: PKR 0.00.", "LEGIT"),

    # --------------------------------------------------------------------------
    # Category 9: Legitimate Anti-Scam Advisories (30 Legit) - Defensive OTP/Fees
    # --------------------------------------------------------------------------
    ("Govt Relief Board: No fee is ever charged for government relief assistance. Never share your OTP with anyone.", "LEGIT"),
    ("Public notice: The official Ehsaas registration is free of cost. Government never asks for any fee.", "LEGIT"),
    ("ہوشیار رہیں: حکومت پاکستان کبھی بھی امداد دینے کے لیے کوئی فیس یا او ٹی پی نہیں مانگتی۔ جعل سازوں سے ہوشیار رہیں۔", "LEGIT"),
    ("BISP Official Advisory: Never share your secret ATM PIN or OTP with any caller claiming to be from 8171.", "LEGIT"),
    ("عوامی آگاہی: بے نظیر کفالت پروگرام کے تمام مراحل مفت ہیں۔ کسی بھی شخص کو فیس یا ایڈوانس رقم مت دیں۔", "LEGIT"),
    ("State Bank Advisory: Banks never ask for your confidential PIN, password, or verification code over phone or SMS.", "LEGIT"),
    ("نادرا انتباہ: نادرا کا عملہ کبھی آپ سے شناختی کارڈ کی تجدید کے لیے فون پر پن کوڈ یا پاسورڈ نہیں مانگتا۔", "LEGIT"),
    ("FIA Cybercrime Alert: Beware of fake SMS offering lottery or flood relief funds. Do not pay any registration fee.", "LEGIT"),
    ("محکمہ پولیس: اگر کوئی شخص امدادی رقم کے نام پر فیس مانگے تو فوری 15 پر اطلاع دیں۔ یہ فراڈ ہے۔", "LEGIT"),
    ("PTA Awareness Message: Do not click unknown links or share your mobile banking PIN with anyone.", "LEGIT"),
    ("Hukumat ki janib se wazifa ke liye kisi qisam ki koi registration fee nahi li jati. Kisi ko paise na dein.", "LEGIT"),
    ("بینکنگ محتسب انتباہ: اپنا او ٹی پی یا پاسورڈ کسی کو نہ بتائیں، چاہے کال کرنے والا خود کو بینک منیجر کہے۔", "LEGIT"),
    ("Securities Commission Notice: Official relief distributions are completely free of cost. Report any fee demands.", "LEGIT"),
    ("حکومت سندھ: راشن کارڈ کے اجرا کے لیے کوئی فیس مقرر نہیں ہے۔ مفت راشن سرکاری مراکز سے حاصل کریں۔", "LEGIT"),
    ("Easypaisa Security Notice: Keep your account safe. Never share your 5-digit PIN or OTP with anyone, even Easypaisa staff.", "LEGIT"),
    ("JazzCash Public Safety: Never disclose your MPIN or SMS verification code to anyone. We never ask for it.", "LEGIT"),
    ("خبردار: بے نظیر انکم سپورٹ کے تمام پیغامات صرف 8171 سے آتے ہیں۔ کسی دوسرے نمبر سے آنے والے پیغام پر فیس نہ دیں۔", "LEGIT"),
    ("National Telecom Safety: Fraudsters send fake SMS from ordinary mobile numbers claiming relief funds. Do not respond.", "LEGIT"),
    ("عوامی اطلاع: وزیراعظم یوتھ پروگرام کی تمام درخواستیں سرکاری ویب سائٹ پر مفت جمع ہوتی ہیں۔ ایجنٹوں کو فیس نہ دیں۔", "LEGIT"),
    ("Ministry of IT Security Alert: Do not forward SMS verification codes or click shortened links in unverified messages.", "LEGIT"),
    ("BISP Warning: Registration is 100% free of charge. If anyone demands money for survey, report to toll-free helpline.", "LEGIT"),
    ("نادرا آگاہی مہم: اپنی نجی معلومات اور بائیو میٹرک تفصیلات غیر مجاز افراد کے ساتھ کبھی نہ شیئر کریں۔", "LEGIT"),
    ("Consumer Protection Council: Beware of advance-fee scams offering emergency financial assistance.", "LEGIT"),
    ("محکمہ زراعت انتباہ: کسان بھائی کسی بھی جعلی نمائندے کو کھاد سبسڈی کے لیے ایڈوانس رقم مت دیں۔", "LEGIT"),
    ("State Life Alert: Insurance claims and relief payouts do not require advance commission or cash deposits.", "LEGIT"),
    ("پی ٹی اے انتباہ: لاٹری یا انعام کے جھانسے میں آ کر کسی کو بھی پیسے یا کریڈٹ کارڈ کی معلومات نہ دیں۔", "LEGIT"),
    ("Relief Transparency Cell: All financial aid is disbursed via biometric verification with zero service charges.", "LEGIT"),
    ("بینک الفلاح آگاہی: اپنے پاسورڈ اور پن کوڈ کو محفوظ رکھیں اور کسی اجنبی کے ساتھ شیئر مت کریں۔", "LEGIT"),
    ("Federal Ombudsperson Alert: Government relief grants do not have processing charges. Report corrupt demands.", "LEGIT"),
    ("Sindh Police Cyber Cell: Never pay courier charges for prize money or government gift hampers. It is a scam.", "LEGIT"),

    # --------------------------------------------------------------------------
    # Category 10: Ambiguous / Borderline Solicitations (30 Unsure / Human Review)
    # --------------------------------------------------------------------------
    ("Assalam o Alaikum, helper center se kal 5000 rupay ka ration bag collect kar lein.", "UNSURE"),
    ("Please visit the community welfare center on Friday regarding your household documentation check.", "UNSURE"),
    ("آپ کا شناختی کارڈ نمبر 42101-1234567-1 مقامی فہرست میں شامل کیا گیا ہے۔ تصدیق کا انتظار کریں۔", "UNSURE"),
    ("Aapki relief application par inquiry pending hai, office time me call kar k status maloom karein.", "UNSURE"),
    ("Dear applicant, a field representative will visit your registered address next week for routine survey.", "UNSURE"),
    ("معزز شہری، راشن کارڈ کی تجدید کے سلسلے میں قریبی کونسلر آفس سے رابطہ کر سکتے ہیں۔", "UNSURE"),
    ("Regarding your financial assistance query, the committee will convene on the 15th of next month.", "UNSURE"),
    ("Apka token number 109 hai, subah 9 baje tehsil office tashreef layen.", "UNSURE"),
    ("Your household details have been updated in the community database. Awaiting administrative clearance.", "UNSURE"),
    ("آپ کے علاقے میں سیلاب ریلیف کی دوسری قسط کے لیے سروے فارم کا اندراج شروع ہو چکا ہے۔", "UNSURE"),
    ("Please provide an alternate contact number for your application file reference #8812.", "UNSURE"),
    ("Kal subah 10 baje helper Shazia se rabta karein family registration k hawale se.", "UNSURE"),
    ("Your request for medical assistance has been forwarded to the district health board.", "UNSURE"),
    ("محکمہ سماجی بہبود: معذور افراد کے خصوصی کارڈ کے لیے میڈیکل بورڈ کی تاریخ مقرر کر دی گئی ہے۔", "UNSURE"),
    ("The verification committee requires one additional witness signature for your claim file.", "UNSURE"),
    ("Apka cnic record verify ho raha hai, mazeed maloomat k liye portal visit karein.", "UNSURE"),
    ("Notification: Relief distribution schedule for UC-4 has been rescheduled to next Monday.", "UNSURE"),
    ("آپ کی بائیو میٹرک تصدیق پہلی کوشش میں کامیاب نہیں ہو سکی، دوبارہ کوشش کی جا سکتی ہے۔", "UNSURE"),
    ("Please verify whether your current residential address matches your CNIC permanent district.", "UNSURE"),
    ("Community elder meeting regarding local relief allocation will take place tomorrow at union council.", "UNSURE"),
    ("Aapki darkhwast ka record check kiya ja raha hai, agle hafte dobara status check karein.", "UNSURE"),
    ("Your application is queued at step 3 of the administrative evaluation pipeline.", "UNSURE"),
    ("شہریوں سے گزارش ہے کہ شناختی کارڈ کی کاپی اور بجلی کے بل کے ہمراہ دفتر تشریف لائیں۔", "UNSURE"),
    ("Disbursement timing will be communicated via official SMS once regional quota is released.", "UNSURE"),
    ("Apka family size record 5 afrad par mushtamil darj kiya gaya hai.", "UNSURE"),
    ("The social welfare inspector has scheduled a follow-up interview for case #9910.", "UNSURE"),
    ("آپ کا نام مستحقین کی عارضی فہرست میں شامل ہے، حتمی فہرست پیر کو جاری ہوگی۔", "UNSURE"),
    ("Please ensure your SIM card is registered on your own CNIC to receive future notifications.", "UNSURE"),
    ("Welfare officer Aslam will be available at the sub-center for consultation from 10am to 2pm.", "UNSURE"),
    ("آپ کی فائل میں آمدنی کا سرٹیفکیٹ مطلوب ہے، جلد از جلد دفتر جمع کروائیں۔", "UNSURE")
]


def run_holdout_evaluation():
    print("=" * 80)
    print("RAHBAR AI — SCAM CLASSIFIER INDEPENDENT 300-MESSAGE HOLDOUT BENCHMARK")
    print("=" * 80)
    print(f"Total benchmark corpus size: {len(HOLDOUT_300)} messages")
    print(f"- Fraudulent / Phishing messages: 150 (Categories 1-5)")
    print(f"- Legitimate messages:           120 (Categories 6-9)")
    print(f"- Borderline / Human Review:      30 (Category 10)")
    print("-" * 80)

    # 3-class confusion matrix: true_label -> pred_label -> count
    classes = ["SCAM", "LEGIT", "UNSURE"]
    matrix = {t: {p: 0 for p in classes} for t in classes}

    # Tracking metrics
    otp_total = 0
    otp_detected = 0

    results_details = []

    for i, (text, true_str) in enumerate(HOLDOUT_300):
        res = classify_message(text)
        pred_label = res["label"].value.upper()
        prob = res.get("scam_probability", 0.0)
        reasons = res.get("reasons", [])

        # Update 3-class matrix
        matrix[true_str][pred_label] += 1

        # Check Category 4: OTP/PIN theft recall
        is_otp_sample = (90 <= i < 120)  # Indices 90 to 119 are the 30 OTP/PIN samples
        if is_otp_sample:
            otp_total += 1
            if pred_label == "SCAM":
                otp_detected += 1

        results_details.append({
            "index": i + 1,
            "text": text[:60] + "..." if len(text) > 60 else text,
            "true_label": true_str,
            "pred_label": pred_label,
            "confidence": res.get("confidence", 0.0),
            "prob_scam": prob,
            "reasons": reasons
        })

    # Output 3-class confusion matrix
    print("\n1. THREE-CLASS CONFUSION MATRIX (Truth in Rows, Predictions in Columns):")
    print("----------------------------------------------------------------------")
    print(f"{'Ground Truth':<15} | {'Pred SCAM':<12} | {'Pred LEGIT':<12} | {'Pred UNSURE':<12} | {'Total':<8}")
    print("-" * 65)
    for t in classes:
        row_scam = matrix[t]["SCAM"]
        row_legit = matrix[t]["LEGIT"]
        row_unsure = matrix[t]["UNSURE"]
        row_total = sum(matrix[t].values())
        print(f"{t:<15} | {row_scam:<12} | {row_legit:<12} | {row_unsure:<12} | {row_total:<8}")

    # Standard Binary Fraud Detection Metrics (Never counting UNSURE as SCAM!)
    # True Positives: True SCAM predicted as SCAM
    # False Negatives: True SCAM predicted as LEGIT
    # Unsure Scam: True SCAM predicted as UNSURE
    tp = matrix["SCAM"]["SCAM"]
    fn = matrix["SCAM"]["LEGIT"]
    unsure_scam = matrix["SCAM"]["UNSURE"]
    total_scam = sum(matrix["SCAM"].values())

    # True Negatives: True LEGIT predicted as LEGIT
    # False Positives: True LEGIT predicted as SCAM
    # Unsure Legit: True LEGIT predicted as UNSURE
    tn = matrix["LEGIT"]["LEGIT"]
    fp = matrix["LEGIT"]["SCAM"]
    unsure_legit = matrix["LEGIT"]["UNSURE"]
    total_legit = sum(matrix["LEGIT"].values())

    total_pred_scam = matrix["SCAM"]["SCAM"] + matrix["LEGIT"]["SCAM"] + matrix["UNSURE"]["SCAM"]

    recall_scam = (tp / total_scam) * 100.0 if total_scam else 0.0
    precision_scam = (tp / total_pred_scam) * 100.0 if total_pred_scam else 0.0
    fnr = (fn / total_scam) * 100.0 if total_scam else 0.0
    fpr = (fp / total_legit) * 100.0 if total_legit else 0.0
    unsure_rate_scam = (unsure_scam / total_scam) * 100.0 if total_scam else 0.0
    unsure_rate_legit = (unsure_legit / total_legit) * 100.0 if total_legit else 0.0
    otp_recall = (otp_detected / otp_total) * 100.0 if otp_total else 0.0

    print("\n2. EMPIRICAL PERFORMANCE METRICS:")
    print("----------------------------------------------------------------------")
    print(f"Scam Recall (True Positives / Total Scams):   {recall_scam:6.2f}% ({tp}/{total_scam})")
    print(f"Scam Precision (True Positives / Pred Scams): {precision_scam:6.2f}% ({tp}/{total_pred_scam})")
    print(f"False Negative Rate (Missed Scams -> Legit):   {fnr:6.2f}% ({fn}/{total_scam})")
    print(f"False Positive Rate (Legit blocked as Scam):  {fpr:6.2f}% ({fp}/{total_legit})")
    print(f"Scam Routed to Human Review (UNSURE):         {unsure_rate_scam:6.2f}% ({unsure_scam}/{total_scam})")
    print(f"Legit Routed to Human Review (UNSURE):        {unsure_rate_legit:6.2f}% ({unsure_legit}/{total_legit})")
    print(f"OTP/PIN Credential Theft Detection Recall:    {otp_recall:6.2f}% ({otp_detected}/{otp_total})")
    print("----------------------------------------------------------------------")

    # Safety Gate Assertions
    print("\n3. PRODUCTION GATE PASS/FAIL CRITERIA:")
    otp_pass = (otp_recall == 100.0)
    recall_pass = (recall_scam >= 95.0)
    precision_pass = (precision_scam >= 90.0)
    fpr_pass = (fpr <= 5.0)
    fnr_pass = (fnr <= 5.0)

    print(f"[{'PASS' if otp_pass else 'FAIL'}] OTP/PIN Recall == 100.0% (Actual: {otp_recall:.1f}%)")
    print(f"[{'PASS' if recall_pass else 'FAIL'}] Scam Recall >= 95.0% (Actual: {recall_scam:.1f}%)")
    print(f"[{'PASS' if precision_pass else 'FAIL'}] Scam Precision >= 90.0% (Actual: {precision_scam:.1f}%)")
    print(f"[{'PASS' if fpr_pass else 'FAIL'}] False Positive Rate <= 5.0% (Actual: {fpr:.1f}%)")
    print(f"[{'PASS' if fnr_pass else 'FAIL'}] False Negative Rate <= 5.0% (Actual: {fnr:.1f}%)")

    all_passed = otp_pass and recall_pass and precision_pass and fpr_pass and fnr_pass
    print("=" * 80)
    print(f"OVERALL TASK 4 GATE DECISION: {'PASSED' if all_passed else 'FAILED'}")
    print("=" * 80)

    # Save results to JSON file for report documentation
    report_data = {
        "benchmark_size": len(HOLDOUT_300),
        "confusion_matrix": matrix,
        "metrics": {
            "recall_scam": round(recall_scam, 2),
            "precision_scam": round(precision_scam, 2),
            "fnr": round(fnr, 2),
            "fpr": round(fpr, 2),
            "unsure_rate_scam": round(unsure_rate_scam, 2),
            "unsure_rate_legit": round(unsure_rate_legit, 2),
            "otp_recall": round(otp_recall, 2)
        },
        "gate_status": "PASSED" if all_passed else "FAILED"
    }

    out_path = os.path.join(os.path.dirname(__file__), "scam_holdout_300_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"Saved evaluation results to {out_path}")

    return all_passed


if __name__ == "__main__":
    success = run_holdout_evaluation()
    sys.exit(0 if success else 1)
