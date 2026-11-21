"""
Comprehensive 300-Message Independent Scam Evaluation for Pre-Production Gate.
Zero overlap with training or previous test datasets.
Evaluates 150 SCAM vs 150 LEGIT across 10 distinct operational categories.
Computes a pure 3-class confusion matrix (SCAM, LEGIT, UNSURE) without conflating UNSURE as SCAM.
"""
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.ai.scam import classify_message
from services.shared.schemas import ScamLabel

EVALUATION_DATASET: List[Tuple[str, str, str]] = [
    # =========================================================================
    # 1. SCAM: OTP THEFT (30 Messages)
    # =========================================================================
    ("BISP Relief Portal: Your monthly subsidy Rs. 14,000 is waiting. Send the 6-digit OTP received on your mobile to 0312-9988776 to confirm deposit.", "SCAM", "OTP_THEFT"),
    ("Dear citizen, your Ehsaas card has been approved. Please reply with the SMS OTP code sent by NADRA to activate instant funds.", "SCAM", "OTP_THEFT"),
    ("Muaziz Sarif, aapka ration subsidy pin generate hogaya hai. Apne number par aya hua OTP foran share karein ta k rashan mil sakay.", "SCAM", "OTP_THEFT"),
    ("Benazir Emergency Cash: Aap k bank account mein 25000 muntaqil karne k liye OTP code darkar hai. Abhi text karein.", "SCAM", "OTP_THEFT"),
    ("Flood Relief 2026: Rs 50,000 sanction letter issued. Enter the one-time password (OTP) sent to your phone to release draft.", "SCAM", "OTP_THEFT"),
    ("NADRA Verification Desk: Confirm your CNIC renewal by sending the verification OTP code you just received on WhatsApp.", "SCAM", "OTP_THEFT"),
    ("HBL Konnect Relief: Apke wallet se 12000 cash out karne k liye OTP password forward karein.", "SCAM", "OTP_THEFT"),
    ("Kamyab Jawan Scheme: Loan disbursement of 100,000 ready. Forward your banking OTP to agent Tariq 0345-1234567 immediately.", "SCAM", "OTP_THEFT"),
    ("Govt Disaster Cell: Payout is blocked due to unverified mobile number. Share OTP received right now to unfreeze.", "SCAM", "OTP_THEFT"),
    ("Bank Alfalah Relief Desk: Your emergency flood voucher requires OTP authentication. Reply with 4-digit code.", "SCAM", "OTP_THEFT"),
    ("UBL Omni: Apka Ehsaas cash warrant release ho gaya hai. Code 6 digits OTP foran send karein.", "SCAM", "OTP_THEFT"),
    ("Zakat Committee Punjab: 20,000 aid approved. Share the SMS verification code received from server.", "SCAM", "OTP_THEFT"),
    ("Federal Relief Program: Urgent security check. Provide the one time passcode received on your SIM to prevent cancellation.", "SCAM", "OTP_THEFT"),
    ("Sindh Relief Commission: Token 4409 approved. To receive direct transfer, verify OTP code sent to your handset.", "SCAM", "OTP_THEFT"),
    ("KPK Ehsaas Kafalat: Wazifa Rs 10,500 pending. Forward OTP message received from 8171 fake gateway to agent.", "SCAM", "OTP_THEFT"),
    ("Balochistan Drought Assistance: Payout scheduled today. Kindly submit the received OTP to helpline WhatsApp.", "SCAM", "OTP_THEFT"),
    ("PM Youth Laptop & Cash Scheme: Claim voucher Rs 35,000. Send your phone OTP to portal operator.", "SCAM", "OTP_THEFT"),
    ("JazzCash Relief Transfer: Rs 18,000 received in escrow. Provide the 6-digit OTP code to complete crediting.", "SCAM", "OTP_THEFT"),
    ("EasyPaisa Grant: Government grant of 15000 is ready. Type your OTP code here to claim immediately.", "SCAM", "OTP_THEFT"),
    ("آپ کی بینظیر کفالت کی رقم تیار ہے۔ فوری تصدیقی او ٹی پی کوڈ اس نمبر پر ارسال کریں تاکہ رقم منتقل کی جا سکے۔", "SCAM", "OTP_THEFT"),
    ("حکومت پاکستان احساس پروگرام: آپ کو پچیس ہزار روپے کا فنڈ دیا جا رہا ہے۔ موبائل پر موصول ہونے والا او ٹی پی کوڈ بتائیں۔", "SCAM", "OTP_THEFT"),
    ("نیشنل ڈیزاسٹر ریلیف: امدادی رقم جاری کرنے کے لیے بینک کا تصدیقی او ٹی پی فوری بھیجیں۔", "SCAM", "OTP_THEFT"),
    ("آپ کا راشن ریلیف پیکج روک دیا گیا ہے۔ اپنا او ٹی پی شیئر کریں تاکہ تصدیق مکمل ہو۔", "SCAM", "OTP_THEFT"),
    ("بینک الحبیب بی آئی ایس پی ڈیسک: 12000 روپے نکلوانے کے لیے او ٹی پی میسج فارورڈ کریں۔", "SCAM", "OTP_THEFT"),
    ("Apka BISP wazifa transfer ruk gya hai. Meharbani farma kar OTP code reply karein warna application radd hojaye gi.", "SCAM", "OTP_THEFT"),
    ("Ehsaas Nashonuma Program: Cash grant Rs 8000 ready. Confirm your eligibility by giving 6-digit OTP.", "SCAM", "OTP_THEFT"),
    ("Ministry of Poverty Alleviation: Token generated. Verify your SIM by sending received OTP code.", "SCAM", "OTP_THEFT"),
    ("Citizen Relief Portal: Confirm your identity for Rs 22,000 direct benefit. Send OTP to supervisor.", "SCAM", "OTP_THEFT"),
    ("Emergency Cash Assistance: Your CNIC matched lucky database. Share verification OTP code immediately.", "SCAM", "OTP_THEFT"),
    ("سوشل ویلفیئر فنڈ: آپ کے اکاؤنٹ میں بارہ ہزار روپے بھیجے جا رہے ہیں۔ فوری اپنا او ٹی پی بتائیں۔", "SCAM", "OTP_THEFT"),

    # =========================================================================
    # 2. SCAM: PIN THEFT (30 Messages)
    # =========================================================================
    ("BISP ATM Alert: Your ATM card for BISP kafalat is locked. Reply with your 4-digit ATM PIN to unlock and withdraw 10,500.", "SCAM", "PIN_THEFT"),
    ("JazzCash Security Department: Your account is scheduled for closure. Send your JazzCash MPIN to keep it active.", "SCAM", "PIN_THEFT"),
    ("EasyPaisa Customer Care: Relief fund 20,000 cannot be credited without wallet secret PIN. Send PIN now.", "SCAM", "PIN_THEFT"),
    ("HBL Relief Gateway: To disburse flood assistance of Rs 30,000, verify your debit card ATM PIN immediately.", "SCAM", "PIN_THEFT"),
    ("Apna ATM PIN code 0301-4455667 par send karein ta k aapka Benazir card chalu ho sakay.", "SCAM", "PIN_THEFT"),
    ("UBL Digital: Urgent security audit for welfare grant. Provide your mobile banking PIN code.", "SCAM", "PIN_THEFT"),
    ("Allied Bank Kafalat: Enter your 4-digit card PIN to authenticate Rs 15,000 government payment.", "SCAM", "PIN_THEFT"),
    ("Meezan Bank Relief Cell: Confirm your Islamic Relief payment. Send your ATM PIN to agent Farhan.", "SCAM", "PIN_THEFT"),
    ("Apka EasyPaisa account suspend hone wala hai. Foran apna 5 digit PIN bhejein ta k account chal sake.", "SCAM", "PIN_THEFT"),
    ("National Bank of Pakistan: BISP beneficiary must submit secret PIN code for biometric bypass.", "SCAM", "PIN_THEFT"),
    ("Bank of Punjab: Khidmat card funds ready. Enter ATM PIN on this portal to withdraw money.", "SCAM", "PIN_THEFT"),
    ("Askari Bank Relief: Provide debit card secret PIN to release military welfare compensation grant.", "SCAM", "PIN_THEFT"),
    ("Bank Alfalah: Your Ehsaas wallet requires PIN reset. Send your old PIN and new PIN to customer officer.", "SCAM", "PIN_THEFT"),
    ("Nayapay Welfare Transfer: Send your 4-digit transaction PIN to receive government subsidy.", "SCAM", "PIN_THEFT"),
    ("Sadapay Relief Allowance: Verify your security PIN code with our helpline officer to claim stipend.", "SCAM", "PIN_THEFT"),
    ("بینظیر انکم سپورٹ: اپنے اے ٹی ایم کارڈ کا پن کوڈ بتائیں تاکہ نیا وظیفہ کارڈ فعال کیا جا سکے۔", "SCAM", "PIN_THEFT"),
    ("جاز کیش ہیلپ لائن: آپ کا اکاؤنٹ فوری بند کیا جا رہا ہے۔ اپنا خفیہ ایم پن کوڈ یہاں درج کریں۔", "SCAM", "PIN_THEFT"),
    ("ایزی پیسہ تصدیق: امدادی فنڈ 25 ہزار روپے حاصل کرنے کے لیے اپنا 5 ہندسی پن کوڈ میسج کریں۔", "SCAM", "PIN_THEFT"),
    ("حبیب بینک ریلیف ڈیسک: اے ٹی ایم پن کوڈ بتائیں تاکہ بائیو میٹرک کے بغیر رقم نکالی جا سکے۔", "SCAM", "PIN_THEFT"),
    ("قومی بچت اسکیم: ریلیف رقم کی ادائیگی کے لیے بینک کارڈ کا پن نمبر درکار ہے۔", "SCAM", "PIN_THEFT"),
    ("Apka ATM card expire ho raha hai. Naya BISP card activate karne k liye 4 digit PIN code sms karein.", "SCAM", "PIN_THEFT"),
    ("State Bank Welfare Scheme: Enter your debit card ATM PIN to confirm beneficiary account.", "SCAM", "PIN_THEFT"),
    ("Post Office Relief Fund: Send Money Order secret PIN to postman for home delivery.", "SCAM", "PIN_THEFT"),
    ("Ehsaas Emergency Cash: Verify your digital wallet PIN code to authorize direct credit.", "SCAM", "PIN_THEFT"),
    ("Citizen Pension & Relief: Card authentication required. Send your 4-digit ATM PIN to branch manager.", "SCAM", "PIN_THEFT"),
    ("Bank of Khyber Relief: Please send secret PIN of your Insaf Card to release stipend.", "SCAM", "PIN_THEFT"),
    ("Sindh Bank Kafalat Desk: Provide MPIN to clear pending grant of Rs 14,000.", "SCAM", "PIN_THEFT"),
    ("JS Bank Emergency Grant: Reply with your card PIN to prevent forfeiture of relief fund.", "SCAM", "PIN_THEFT"),
    ("Faysal Bank Noor Welfare: Submit ATM PIN code to authenticate zakat disbursement.", "SCAM", "PIN_THEFT"),
    ("آپ کا بی آئی ایس پی کا وظیفہ روک دیا گیا ہے۔ فوری طور پر اپنا خفیہ پن کوڈ سینڈ کریں۔", "SCAM", "PIN_THEFT"),

    # =========================================================================
    # 3. SCAM: FAKE REGISTRATION & ADVANCE FEES (30 Messages)
    # =========================================================================
    ("BISP Head Office: Congratulations! Rs 45,000 approved. Deposit Rs 1,200 verification fee to EasyPaisa 0340-9988112 to receive cheque.", "SCAM", "ADVANCE_FEE"),
    ("Ehsaas Cash Scheme: To release your grant of Rs 35,000, transfer Rs 850 file processing tax charges right now.", "SCAM", "ADVANCE_FEE"),
    ("PM Flood Relief: You are awarded Rs 80,000. Send Rs 1500 courier and stamp fee to claim voucher.", "SCAM", "ADVANCE_FEE"),
    ("Aapka 50,000 ka imdadi check ban chuka hai. 1000 rupay delivery fee jama karein ta k check ghar puhanch sake.", "SCAM", "ADVANCE_FEE"),
    ("Benazir Kafalat: Deposit Rs 700 bank charges immediately to 0300-1122334 to release pending stipend.", "SCAM", "ADVANCE_FEE"),
    ("National Relief Foundation: Send Rs 2,000 registration fee to get monthly Rs 15,000 for entire year.", "SCAM", "ADVANCE_FEE"),
    ("Solar Scheme 2026: Free solar panel sanctioned. Pay Rs 2,500 transport fee to driver to deliver setup.", "SCAM", "ADVANCE_FEE"),
    ("Disaster Relief Board: Grant of Rs 60,000 awaiting clearance. Send Rs 1200 advance fee to account officer.", "SCAM", "ADVANCE_FEE"),
    ("Welfare Cash Voucher: Deposit Rs 950 challan fee at Omni shop to collect 28,000 cash grant.", "SCAM", "ADVANCE_FEE"),
    ("Hukumat-e-Pakistan Imdad: Rs 30,000 lene k liye 650 rupay ki registration fee foran ada karein.", "SCAM", "ADVANCE_FEE"),
    ("Chief Minister Relief Package: Pay Rs 1,100 document verification fee to receive Rs 40,000 cash grant.", "SCAM", "ADVANCE_FEE"),
    ("BISP Phase 4: Aap ki qist 25,000 tayyar hai. Sirf 500 advance fee bhejein aur payment lein.", "SCAM", "ADVANCE_FEE"),
    ("UNICEF Pakistan Cash Transfer: Claim $200 relief grant by paying $10 clearance fee via local agent.", "SCAM", "ADVANCE_FEE"),
    ("Bait-ul-Mal Special Assistance: Rs 50,000 sanctioned. Deposit Rs 1,400 processing fee to release bank draft.", "SCAM", "ADVANCE_FEE"),
    ("Rashid Minhas Welfare Trust: Pay Rs 800 token fee to receive dry ration bag and Rs 10,000 cash envelope.", "SCAM", "ADVANCE_FEE"),
    ("وزیر اعظم یوتھ ریلیف اسکیم: پچاس ہزار روپے کی امداد کے لیے فوری ایک ہزار روپے رجسٹریشن فیس جمع کروائیں۔", "SCAM", "ADVANCE_FEE"),
    ("بے نظیر پروگرام 2026: چالیس ہزار روپے وصول کرنے کے لیے ساڑھے آٹھ سو روپے فائل چارجز فوری ادا کریں۔", "SCAM", "ADVANCE_FEE"),
    ("سیلاب متاثرین فنڈ: آپ کا نام منتخب ہو گیا ہے۔ بارہ سو روپے کوریئر فیس جمع کروائیں اور پچاس ہزار کا ڈرافٹ پائیں۔", "SCAM", "ADVANCE_FEE"),
    ("حکومت سندھ راشن کارڈ: کارڈ حاصل کرنے کے لیے پانچ سو روپے پراسیسنگ فیس ایزی پیسہ کریں۔", "SCAM", "ADVANCE_FEE"),
    ("قومی ویلفیئر ٹرسٹ: بیس ہزار ماہانہ وظیفے کے لیے پندرہ سو روپے فارم فیس فوری جمع کروائیں۔", "SCAM", "ADVANCE_FEE"),
    ("Apka 30000 ka cash prize aur relief grant approved hai. 1200 rupay advance tax bhejein aur paisa lein.", "SCAM", "ADVANCE_FEE"),
    ("Green Tractor & Relief Cash: Submit Rs 3,000 security deposit fee to confirm allocation.", "SCAM", "ADVANCE_FEE"),
    ("Ehsaas Ration Riayat: 1000 rupay subsidy card activate karne k liye 300 fee jama karwayen.", "SCAM", "ADVANCE_FEE"),
    ("Federal Zakat Fund: Deposit Rs 750 verification fee to receive Rs 20,000 annual zakat check.", "SCAM", "ADVANCE_FEE"),
    ("PM Corona/Disaster Relief: Pay Rs 900 clearance charge to credit Rs 25,000 directly to CNIC.", "SCAM", "ADVANCE_FEE"),
    ("KPK Insaf Imdad: 500 rupay registration fee bhejo aur 15000 cash hasil karo.", "SCAM", "ADVANCE_FEE"),
    ("Balochistan Relief Quota: Rs 40,000 grant sanctioned. Send Rs 1,000 challan fee to agent Tariq.", "SCAM", "ADVANCE_FEE"),
    ("Gilgit Baltistan Relief: Pay Rs 600 postal processing fee to receive assistance cheque.", "SCAM", "ADVANCE_FEE"),
    ("Azad Kashmir Welfare: Deposit Rs 1,500 file charges to release approved housing repair grant.", "SCAM", "ADVANCE_FEE"),
    ("احساس ایمرجنسی ریلیف: آپ کے اکاؤنٹ میں تیس ہزار بھیجے جا رہے ہیں۔ فوری نو سو روپے رجسٹریشن فیس بھیجیں۔", "SCAM", "ADVANCE_FEE"),

    # =========================================================================
    # 4. SCAM: ROMAN URDU PHISHING (30 Messages)
    # =========================================================================
    ("BISP 8171 Alert: Muaziz Sarif aap k naam 35000 rupay aye hain. Foran is link par click karein bit.ly/bisp-cash26", "SCAM", "ROMAN_URDU_PHISH"),
    ("Ehsaas Program: Aapki registration kamyab rahi. Paisay lene k liye tinyurl.com/ehsaas-claim par CNIC aur bank darj karein.", "SCAM", "ROMAN_URDU_PHISH"),
    ("Hukumat-e-Pakistan ki janib se har gharanay ko 25000 ka imdad. Abhi register karein t.co/pak-relief-funds", "SCAM", "ROMAN_URDU_PHISH"),
    ("Aapka BISP account freeze kar dia gya hai. Foran 0311-2345678 par call karein warna paisay wapis chale jayen ge.", "SCAM", "ROMAN_URDU_PHISH"),
    ("BISP Benazir Wazifa: Rs 20,000 transfer ho chukay hain. Check status at http://ehsaas-fake-portal.com", "SCAM", "ROMAN_URDU_PHISH"),
    ("Welfare Cash Alert: Aapki qist double ho gai hai. 45000 lene k liye is WhatsApp number wa.me/923001239988 par rabta karein.", "SCAM", "ROMAN_URDU_PHISH"),
    ("PM Relief Package: Akhri tareekh aj hai! Foran link open karein aur apna muft rashan aur 15000 claim karein bit.ly/pm-cash", "SCAM", "ROMAN_URDU_PHISH"),
    ("Ehsaas Kafalat 8171: Aap k 10500 rupay biometric failure ki wajah se atkay hain. Is link par click karein wa.me/923214567890", "SCAM", "ROMAN_URDU_PHISH"),
    ("BISP Office: Aapko mubarak ho 50,000 lottery relief grant nikla hai. Foran claim form fill karein http://bisp-payout.tk", "SCAM", "ROMAN_URDU_PHISH"),
    ("Zakat Committee: 30000 rupay hasil karne k liye apni mukammal maloomat aur card photos is WhatsApp par bhejein.", "SCAM", "ROMAN_URDU_PHISH"),
    ("Benazir Taleemi Wazifa: Bachon k 18,000 wazifa k liye apna bank account aur secret code is number par sms karein.", "SCAM", "ROMAN_URDU_PHISH"),
    ("Kamyab Nojawan: Rozgar scheme mein 50000 cash grant lena chahte hain to abhi call karein 0333-8877665 par.", "SCAM", "ROMAN_URDU_PHISH"),
    ("BISP Head Office Islamabad: Aapki relief payment cancel hone wali hai. Foran rabta karein officer Naveed se.", "SCAM", "ROMAN_URDU_PHISH"),
    ("Ehsaas Emergency Fund: 25 hazar rupay ghar bethe hasil karein. Form bharein tinyurl.com/free-ehsaas-cash", "SCAM", "ROMAN_URDU_PHISH"),
    ("Punjab Khidmat Card: Muaziz sarif aap k 12000 jama ho gaye hain. Claim link: bit.ly/khidmat-cash-2026", "SCAM", "ROMAN_URDU_PHISH"),
    ("Sindh Peoples Relief: 20000 direct bank transfer k liye apni details is portal par dakhil karein http://sindh-welfare-relief.ml", "SCAM", "ROMAN_URDU_PHISH"),
    ("KPK Sehat Insaf Card: Ilaj k sath 15,000 cash allowance bhi lein. Click bit.ly/kpk-cash-grant", "SCAM", "ROMAN_URDU_PHISH"),
    ("Balochistan Awami Relief: Rs 28,000 emergency grant claim karne ka aakhri mauqa. Call 0341-2233445", "SCAM", "ROMAN_URDU_PHISH"),
    ("NADRA Emergency Cell: Aapka CNIC relief list mein shaamil hai. Paisay lene k liye click karein t.co/nadra-grant", "SCAM", "ROMAN_URDU_PHISH"),
    ("BISP Special Grant: Aapko 35 hazar rupay ka special ramazan package mila hai. Foran rabta karein.", "SCAM", "ROMAN_URDU_PHISH"),
    ("Ehsaas Solar Panel: Muft solar system aur 10000 cash k liye abhi WhatsApp karein wa.me/923159988776", "SCAM", "ROMAN_URDU_PHISH"),
    ("Benazir Kafalat: Aapki qist ready hai. Payout office aane se pehle is number par apna account register karwayen.", "SCAM", "ROMAN_URDU_PHISH"),
    ("Disaster Payout Notice: 50,000 rupay direct transfer. Link bit.ly/disaster-payout-pk", "SCAM", "ROMAN_URDU_PHISH"),
    ("Ehsaas Tahafuz: Bimari ki soorat mein 100,000 tak ki imdad. Register karein tinyurl.com/ehsaas-tahafuz-claim", "SCAM", "ROMAN_URDU_PHISH"),
    ("Welfare Department: Aap k account mein 18,000 transfer ho rahay hain. Verify karne k liye click karein http://welfare-verify.com", "SCAM", "ROMAN_URDU_PHISH"),
    ("BISP Registration 2026: Naya survey shuru. Agar aap ghareeb hain to 40,000 lene k liye rabta karein.", "SCAM", "ROMAN_URDU_PHISH"),
    ("National Relief: Rs 22000 direct cash. Sirf CNIC darj karein bit.ly/national-relief-pak", "SCAM", "ROMAN_URDU_PHISH"),
    ("BISP 8171: Aap ka naam BISP list mein a chuka hai. 25000 rupay wasool karein is link se tinyurl.com/bisp-wazifa", "SCAM", "ROMAN_URDU_PHISH"),
    ("PM Youth Allowance: Har mahina 12,000 rupay stipend lein. Form link: bit.ly/pm-stipend-2026", "SCAM", "ROMAN_URDU_PHISH"),
    ("Ehsaas Langar & Cash: Muft rashan card aur 15000 cash grant lene k liye call karein 0308-7654321", "SCAM", "ROMAN_URDU_PHISH"),

    # =========================================================================
    # 5. SCAM: URDU PHISHING (NASTALIQ) (30 Messages)
    # =========================================================================
    ("بے نظیر انکم سپورٹ پروگرام: مبارک ہو! آپ کے نام 35,000 روپے کی امداد جاری ہو چکی ہے۔ فوری واٹس ایپ پر رابطہ کریں۔", "SCAM", "URDU_PHISH"),
    ("احساس کفالت 8171: آپ کے خاندان کے لیے 25,000 روپے کا ریلیف فنڈ منظور ہو چکا ہے۔ اس لنک پر کلک کریں bit.ly/ehsaas-urdu", "SCAM", "URDU_PHISH"),
    ("حکومت پاکستان ایمرجنسی کیش پروگرام: سیلاب متاثرین کے لیے 50,000 روپے کی امداد۔ رجسٹریشن فارم کے لیے tinyurl.com/urdu-cash کھولیں۔", "SCAM", "URDU_PHISH"),
    ("آپ کا احساس پروگرام کا وظیفہ روک دیا گیا ہے۔ فوری طور پر 0301-9988776 پر کال کریں ورنہ رقم منسوخ کر دی جائے گی۔", "SCAM", "URDU_PHISH"),
    ("بی آئی ایس پی ہیڈ آفس اسلام آباد: آپ کو 40,000 روپے کا نقد انعام مبارک ہو۔ تصدیق کے لیے ابھی رابطہ کریں۔", "SCAM", "URDU_PHISH"),
    ("وزیر اعظم راشن ریلیف پیکج: مفت راشن اور 10,000 روپے نقد امداد کے لیے اس لنک پر کلک کریں t.co/pm-rashan-pk", "SCAM", "URDU_PHISH"),
    ("احساس نشوونما پروگرام: خواتین کے لیے 15,000 روپے کی مالی امداد۔ فوری اپنا بینک کارڈ نمبر اور پاسورڈ واٹس ایپ کریں۔", "SCAM", "URDU_PHISH"),
    ("بینظیر تعلیمی وظائف: بچوں کی فیس کے 18,000 روپے آ چکے ہیں۔ کلک کریں اور فارم پر کریں http://bisp-urdu-fake.com", "SCAM", "URDU_PHISH"),
    ("سیلاب ریلیف اتھارٹی: 60,000 روپے کی امدادی رقم حاصل کرنے کا آخری دن۔ ابھی فوری رابطہ کریں۔", "SCAM", "URDU_PHISH"),
    ("قومی سماجی تحفظ: آپ کا شناختی کارڈ وظیفے کے لیے منتخب ہوا ہے۔ 25,000 نقد حاصل کرنے کے لیے 0345-8899001 پر کال کریں۔", "SCAM", "URDU_PHISH"),
    ("مبارک ہو! بے نظیر قرعہ اندازی میں آپ کا پچاس ہزار روپے کا انعام نکلا ہے۔ وصولی کے لیے فوری رابطہ کریں۔", "SCAM", "URDU_PHISH"),
    ("احساس ایمرجنسی فنڈ: آپ کے اکاؤنٹ میں 20,000 منتقل کر دیے گئے ہیں۔ حاصل کرنے کے لیے لنک کھولیں bit.ly/urdu-ehsaas26", "SCAM", "URDU_PHISH"),
    ("بی آئی ایس پی وظیفہ 2026: آپ کے شناختی کارڈ پر 30,000 روپے منظور ہو چکے ہیں۔ فوری کال کریں۔", "SCAM", "URDU_PHISH"),
    ("حکومت سندھ پیپلز ریلیف: مفت پلاٹ اور 40,000 روپے نقد امداد کے لیے ابھی آن لائن فارم جمع کریں۔", "SCAM", "URDU_PHISH"),
    ("پنجاب خدمت کارڈ: معذور اور مستحق افراد کے لیے 15,000 روپے کی مالی امداد۔ رابطہ نمبر 0321-7766554", "SCAM", "URDU_PHISH"),
    ("خیبر پختونخوا احساس پروگرام: 22,000 روپے براہ راست کیش۔ رجسٹریشن لنک: tinyurl.com/kpk-urdu-relief", "SCAM", "URDU_PHISH"),
    ("بلوچستان ریلیف پیکج: پچیس ہزار روپے کا خصوصی چیک لینے کے لیے فوری اس نمبر پر واٹس ایپ کریں۔", "SCAM", "URDU_PHISH"),
    ("نادرا ریلیف ڈیسک: آپ کا نام غریب افراد کی لسٹ میں شامل ہے۔ فوری 35,000 روپے کی گرانٹ وصول کریں۔", "SCAM", "URDU_PHISH"),
    ("رمضان ریلیف پیکیج 2026: حکومت کی طرف سے مفت آٹا اور 12,000 روپے نقد۔ فارم کے لیے کلک کریں۔", "SCAM", "URDU_PHISH"),
    ("بیت المال وظیفہ: بیواؤں اور یتیموں کے لیے 20,000 روپے کا چیک۔ فوری تصدیقی فارم پر کریں۔", "SCAM", "URDU_PHISH"),
    ("بے نظیر سپورٹ پروگرام: اکاؤنٹ غیر فعال ہو چکا ہے۔ وظیفہ جاری رکھنے کے لیے فوری رابطہ کریں۔", "SCAM", "URDU_PHISH"),
    ("احساس بلا سود قرض اسکیم: 100,000 روپے کا بلا سود قرض اور 20,000 نقد گرانٹ حاصل کریں۔", "SCAM", "URDU_PHISH"),
    ("وزیر اعظم یوتھ اسکیم: بیروزگار نوجوانوں کے لیے 15,000 ماہانہ وظیفہ۔ درخواست دینے کے لیے رابطہ کریں۔", "SCAM", "URDU_PHISH"),
    ("ریلیف کمیشن پاکستان: آپ کے نام 45,000 روپے کا ڈرافٹ موصول ہوا ہے۔ فوری وصولی کے لیے کال کریں۔", "SCAM", "URDU_PHISH"),
    ("احساس راشن رعایت: گروسری اسٹور سے 50 فیصد رعایت اور نقد رقم کے لیے کلک کریں۔", "SCAM", "URDU_PHISH"),
    ("بی آئی ایس پی قسط 8171: آپ کے وظیفے کی نئی قسط آ چکی ہے۔ ابھی آن لائن تصدیق کریں۔", "SCAM", "URDU_PHISH"),
    ("قومی زکوٰۃ کونسل: تیس ہزار روپے کا امدادی چیک حاصل کرنے کے لیے اپنی تفصیلات واٹس ایپ کریں۔", "SCAM", "URDU_PHISH"),
    ("فوری ریلیف الرٹ: آپ کا نام لکی ڈرا ریلیف فنڈ میں نکلا ہے۔ 50,000 وصول کریں۔", "SCAM", "URDU_PHISH"),
    ("حکومت پاکستان مالی امداد: شناختی کارڈ پر 28,000 روپے کی فوری فراہمی۔ رابطہ 0312-3344556", "SCAM", "URDU_PHISH"),
    ("بے نظیر کفالت اسکیم: 14,000 روپے کی فوری ادائیگی۔ لنک پر کلک کر کے بینک اکاؤنٹ درج کریں۔", "SCAM", "URDU_PHISH"),

    # =========================================================================
    # 6. LEGIT: UTILITY BILLS (30 Messages)
    # =========================================================================
    ("K-Electric: Your electricity bill for Consumer No 040001234567 for Nov 2026 is Rs 6,850. Due date is 28-Nov-2026. Pay via bank or mobile app.", "LEGIT", "UTILITY_BILL"),
    ("LESCO Bill Alert: Reference 08-11523-0982300, payable amount within due date Rs 4,120. Due date is 25-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("SNGPL Gas Bill: Consumer ID 9821345678, Current bill PKR 1,450, Payable after due date PKR 1,600. Due date is 24-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("SSGC Gas Bill: Customer # 3349012984, Total bill Rs 890. Due date is 26-Nov-2026. Thank you for conserving energy.", "LEGIT", "UTILITY_BILL"),
    ("PTCL Bill Alert: Account ID 1009823451, Current bill amount Rs 2,990. Due date is 20-Nov-2026. Pay online to enjoy uninterrupted services.", "LEGIT", "UTILITY_BILL"),
    ("IESCO Islamabad: Electricity bill for Consumer # 01-14111-0023450 is PKR 5,640. Due date is 27-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("FESCO Faisalabad: Bill for reference 12-23456-7890123 amount PKR 3,820. Last date of payment is 29-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("GEPCO Gujranwala: Your electricity bill is Rs 4,500 due on 30-Nov-2026. Consumer ID 198234567.", "LEGIT", "UTILITY_BILL"),
    ("MEPCO Multan: Monthly power bill for Reference 05-15432-1234567 is PKR 4,780. Due date is 26-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("PESCO Peshawar: Electricity consumption bill PKR 3,210 due on 27-Nov-2026. Please pay on time to avoid late surcharge.", "LEGIT", "UTILITY_BILL"),
    ("HESCO Hyderabad: Bill amount Rs 2,900 for Consumer 03-19876-5432100. Due date is 25-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("SEPCO Sukkur: Monthly power charges Rs 2,400 due on 28-Nov-2026. Pay through JazzCash or Omni.", "LEGIT", "UTILITY_BILL"),
    ("QESCO Quetta: Reference 09-98765-4321098 bill amount PKR 1,950 due date 29-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("Karachi Water & Sewerage Board: Consumer # KW-992143 water charges bill Rs 520 due on 10-Dec-2026.", "LEGIT", "UTILITY_BILL"),
    ("WASA Lahore: Water and sanitation charges for Q4 2026 is PKR 680. Due date is 05-Dec-2026.", "LEGIT", "UTILITY_BILL"),
    ("WASA Rawalpindi: Consumer 449012 water supply bill PKR 450 payable by 02-Dec-2026.", "LEGIT", "UTILITY_BILL"),
    ("Nayatel Fiber: Monthly internet subscription invoice generated. Amount PKR 3,450. Due date is 25-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("StormFiber: Invoice for connection # SF-88120 is PKR 2,875. Due date is 22-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("Wi-Tribe Pakistan: Your broadband bill for Nov 2026 is PKR 1,725. Due date is 28-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("Total Parco Fuel Card: Monthly statement generated. Outstanding balance PKR 12,400 due on 30-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("آپ کا لیسکو بجلی کا بل ماہ نومبر 3,450 روپے ہے۔ آخری تاریخ 26 نومبر 2026 ہے۔ برائے مہربانی بروقت ادا کریں۔", "LEGIT", "UTILITY_BILL"),
    ("سوئی ناردرن گیس: صارفین کا گیس بل 1,200 روپے بنام صارف نمبر 9871234۔ مقررہ تاریخ 25 نومبر ہے۔", "LEGIT", "UTILITY_BILL"),
    ("کے الیکٹرک: صارف نمبر 041123456789 کا ماہانہ بل 5,100 روپے ہے۔ آخری تاریخ 27 نومبر 2026 ہے۔", "LEGIT", "UTILITY_BILL"),
    ("واسا فیصل آباد: پانی اور سیوریج کا سہ ماہی بل 600 روپے واجب الادا تاریخ 30 نومبر 2026۔", "LEGIT", "UTILITY_BILL"),
    ("پی ٹی سی ایل: فون اور براڈ بینڈ کا بل 2,150 روپے آخری تاریخ 24 نومبر 2026۔", "LEGIT", "UTILITY_BILL"),
    ("Telenor Postpaid: Your mobile bill for 0345-9876543 is PKR 1,120. Due date is 28-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("Zong Postpaid: Bill amount for Nov 2026 is PKR 890. Due date is 26-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("Jazz Postpaid: Monthly invoice generated. Payable amount Rs 1,450 due date 25-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("Ufone Postpaid: Account # UF-098234 bill Rs 990 due on 27-Nov-2026.", "LEGIT", "UTILITY_BILL"),
    ("سندھ سالڈ ویسٹ مینجمنٹ: صفائی چارجز کا بل 300 روپے برائے نومبر 2026۔", "LEGIT", "UTILITY_BILL"),

    # =========================================================================
    # 7. LEGIT: PAYMENT RECEIPTS (30 Messages)
    # =========================================================================
    ("JazzCash: Payment of PKR 1,200 to K-Electric was successful on 21-Nov-2026. Transaction ID: JC982143. Fee: PKR 0.00.", "LEGIT", "RECEIPT"),
    ("EasyPaisa: You sent PKR 2,500 to Farhan Ahmed (03123456789) on 20-Nov-2026. Fee: PKR 0.00. Balance: PKR 8,450.", "LEGIT", "RECEIPT"),
    ("1Link 1Bill: Payment of Rs 4,500 for LESCO Consumer # 0811523 received successfully. Reference: 1L-887712.", "LEGIT", "RECEIPT"),
    ("HBL Konnect: Cash deposit of PKR 5,000 received in your account on 21-Nov-2026. Available balance PKR 22,300.", "LEGIT", "RECEIPT"),
    ("Meezan Bank: Debit transaction of PKR 3,400 at Imtiaz Super Market POS terminal on 21-Nov-2026. Balance: PKR 45,100.", "LEGIT", "RECEIPT"),
    ("Bank Alfalah: Your credit card payment of PKR 15,000 has been received with thanks. Reference: BA-776611.", "LEGIT", "RECEIPT"),
    ("UBL Digital: Funds transfer of PKR 10,000 to Account ****4321 executed successfully via Raast ID. Fee: PKR 0.00.", "LEGIT", "RECEIPT"),
    ("Allied Bank: Bill payment of PKR 1,450 to SNGPL successful on 20-Nov-2026. Ref: ABL-098234.", "LEGIT", "RECEIPT"),
    ("Standard Chartered: POS purchase of PKR 2,150 at Shell Fuel Station on 21-Nov-2026. Available balance PKR 18,900.", "LEGIT", "RECEIPT"),
    ("Daraz.pk: Payment received for Order # PK-88712399 via JazzCash. Total paid: PKR 2,450. Your package is dispatched.", "LEGIT", "RECEIPT"),
    ("Foodpanda: Order # FP-992143 paid online via debit card PKR 1,180. Your rider is on the way.", "LEGIT", "RECEIPT"),
    ("Careem Pakistan: Ride receipt for booking # CR-11092. Total paid: PKR 620 via wallet. Thank you for riding.", "LEGIT", "RECEIPT"),
    ("Indrive: Payment confirmation of PKR 450 paid directly to driver for ride on 21-Nov-2026.", "LEGIT", "RECEIPT"),
    ("Total School Tuition Fee: Receipt generated for Student ID 4409. Total paid PKR 5,500 for Nov 2026.", "LEGIT", "RECEIPT"),
    ("Aga Khan University Hospital: Receipt # AK-88721 for lab test. Total paid PKR 3,200. Thank you.", "LEGIT", "RECEIPT"),
    ("Shaukat Khanum Hospital: Donation receipt # SK-09821 of PKR 5,000 received with gratitude. Zakat tax exempt.", "LEGIT", "RECEIPT"),
    ("NADRA e-Sahulat: Payment of PKR 1,500 for CNIC renewal application tracking ID 882190 received.", "LEGIT", "RECEIPT"),
    ("Passport Office: Payment of PKR 4,500 for 36-page normal passport token # PS-3321 confirmed.", "LEGIT", "RECEIPT"),
    ("Excise & Taxation: Motor vehicle token tax PKR 2,800 paid successfully for vehicle LEA-2026. Receipt generated.", "LEGIT", "RECEIPT"),
    ("Punjab E-Challan: Traffic violation fine PKR 500 paid via Easypaisa for Challan # EC-9921.", "LEGIT", "RECEIPT"),
    ("جاز کیش: آپ کے اکاؤنٹ سے 1,500 روپے کی رقم محمد علی کو کامیابی سے منتقل ہو گئی۔ ٹرانزیکشن فیس: 0 روپے", "LEGIT", "RECEIPT"),
    ("ایزی پیسہ رسید: لیسکو بجلی کا بل 3,200 روپے کامیابی سے ادا ہو گیا۔ رسید نمبر EP-778812۔", "LEGIT", "RECEIPT"),
    ("میزان بینک: اے ٹی ایم سے 10,000 روپے کی نکلوائی کی گئی۔ بقایا بیلنس 35,400 روپے۔ تاریخ 21 نومبر۔", "LEGIT", "RECEIPT"),
    ("حبیب بینک: راست آئی ڈی کے ذریعے 5,000 روپے کی منتقلی مکمل ہوئی۔ کوئی فیس لاگو نہیں۔", "LEGIT", "RECEIPT"),
    ("نادرا ای سہولت: شناختی کارڈ فیس کی رسید نمبر 49102 موصول ہو گئی۔ کل ادا شدہ رقم 1,000 روپے۔", "LEGIT", "RECEIPT"),
    ("Nayapay: Payment of PKR 850 at Espresso Cafe completed via Visa debit card. Balance: PKR 14,200.", "LEGIT", "RECEIPT"),
    ("Sadapay: Sent Rs 1,000 to Bilal Khan via Raast on 21-Nov-2026. Zero transfer fee charged.", "LEGIT", "RECEIPT"),
    ("Chughtai Lab: Payment receipt # CL-8821 for blood test. Total paid PKR 1,800 on 20-Nov-2026.", "LEGIT", "RECEIPT"),
    ("Edhi Foundation: Donation receipt # ED-9912 of PKR 2,000 received with thanks.", "LEGIT", "RECEIPT"),
    ("پی ایس ایل میچ ٹکٹ: بکنگ رسید جاری کر دی گئی۔ کل ادا شدہ رقم 2,000 روپے بذریعہ کارڈ۔", "LEGIT", "RECEIPT"),

    # =========================================================================
    # 8. LEGIT: GOVERNMENT ANNOUNCEMENTS & OFFICIAL UPDATES (30 Messages)
    # =========================================================================
    ("BISP Official Notice: Benazir Kafalat fourth quarter disbursement has officially commenced nationwide via designated partner bank biometric campsites.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Ehsaas Program Update: Citizens can check their eligibility free of cost by sending their 13-digit CNIC number to official SMS code 8171.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Government of Pakistan: Registration for Prime Minister Youth Laptop Scheme Phase 4 is now open at official portal pmyp.gov.pk.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("NADRA Public Information: Senior citizens aged 65 and above are eligible for free lifetime CNIC renewal at all NADRA registration centers.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Ministry of National Health: Free polio vaccination campaign starts from Monday across 45 sensitive districts nationwide.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("BISP Islamabad: All biometric payment campsites operate from 8:00 AM to 5:00 PM Monday through Saturday. No fee is charged for service.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("State Bank of Pakistan: Banking hours for public transactions will remain 9:00 AM to 5:00 PM during the winter schedule.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("National Disaster Management Authority: Monsoon advisory issued for northern regions. Citizens are advised to follow official weather alerts.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Punjab Social Protection Authority: Khidmat Card beneficiaries can collect their quarterly stipend from any authorized Bank of Punjab ATM.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Sindh Education Department: Winter vacations for all public and private schools will be observed from December 22 to December 31, 2026.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("KPK Elementary Education: Free textbook distribution completed for primary school students across government schools.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Balochistan Relief Commissionerate: Ration distribution centers established in flood-affected union councils for registered heads of families.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Pakistan Post Office: International EMS tracking service upgraded. Customers can track mail using the 13-character tracking number.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Federal Board of Revenue: The last date for filing annual income tax returns for tax year 2026 has been notified on the IRIS portal.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Ministry of Overseas Pakistanis: OPF membership renewal is available online via official portal overseas.gov.pk.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("حکومت پاکستان کا اعلان: بی آئی ایس پی کی سہ ماہی قسط 10,500 روپے بینک کیمپ سائٹس سے بائیو میٹرک تصدیق پر حاصل کی جا سکتی ہے۔", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("نادرا پبلک نوٹس: تمام شہری اپنے شناختی کارڈ پر درج پتہ اور کوائف قریبی نادرا سینٹر سے بلامعاوضہ تصدیق کروا سکتے ہیں۔", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("احساس پروگرام کی سرکاری اطلاع: 8171 پر اپنا شناختی کارڈ نمبر بھیج کر اہلیت کی مکمل معلومات مفت حاصل کریں۔", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("وزارت موسمیاتی تبدیلی: کاشتکاروں کے لیے مفت بیج اور کھاد کی تقسیم سرکاری زرعی مراکز پر شروع کر دی گئی ہے۔", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("محکمہ صحت پنجاب: 60 سال سے زائد عمر کے شہریوں کے لیے سرکاری ہسپتالوں میں مفت انسولین اور ادویات کی فراہمی جاری ہے۔", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Hukumat-e-Pakistan: BISP Kafalat ki taaza tareen maloomat k liye sirf sarkari website bisp.gov.pk par tashreef layen.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Ehsaas Rashan Riayat: Kiryana store registration is completely free. Shopkeepers can enroll via the official mobile application.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("National Electric Power Regulatory Authority: Public hearing on quarterly tariff adjustment scheduled on 28-Nov-2026.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Oil & Gas Regulatory Authority: Petroleum prices notification for the second half of November 2026 issued by Finance Division.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Pakistan Railways: Train schedule for winter season notified. Passengers are requested to check arrival times via Pakrail app.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Civil Aviation Authority: Flight operations at all major airports in Pakistan are operating normally per standard winter schedules.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Securities & Exchange Commission: Official public awareness campaign regarding registered investment companies.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("Competition Commission of Pakistan: Citizens can file consumer market complaints through official email complaints@cc.gov.pk.", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("پبلک انفارمیشن ڈیسک: سرکاری امدادی اسکیموں میں کسی قسم کی رجسٹریشن فیس نہیں لی جاتی۔ تمام خدمات مفت فراہم کی جاتی ہیں۔", "LEGIT", "GOVT_ANNOUNCEMENT"),
    ("وزارت ریلوے: بزرگ شہریوں اور خصوصی افراد کے لیے ریل کے کرایوں میں پچاس فیصد رعایت بدستور جاری ہے۔", "LEGIT", "GOVT_ANNOUNCEMENT"),

    # =========================================================================
    # 9. LEGIT: FINANCIAL TRANSFER NOTIFICATIONS (30 Messages)
    # =========================================================================
    ("Salary Credit Notification: Monthly salary of PKR 65,000 for Nov 2026 has been credited to your account # ****1092. Value date: 21-Nov-2026.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("HBL Raast Credit Alert: Account ****4432 has been credited with PKR 12,000 from Government of Pakistan Treasury via Raast. Available balance PKR 28,400.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Meezan Bank: Direct benefit transfer of PKR 10,500 received from BISP Benazir Kafalat into account ****9812 on 21-Nov-2026.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Bank Alfalah: Inward remittance of USD 250 (converted to PKR 69,500) credited to your Roshan Digital Account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("UBL Omni Alert: Government disaster cash assistance PKR 25,000 has been credited to your CNIC wallet. Visit branch with original CNIC.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("EasyPaisa: Inward transfer of PKR 5,000 from Tariq Mahmood received. Updated wallet balance is PKR 12,300.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("JazzCash: Rs 8,000 received from Asif Khan via Raast P2P transfer. Your available balance is Rs 11,500.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("National Bank of Pakistan: Pension payment of PKR 34,500 for the month of November 2026 has been credited to account ****5543.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Allied Bank: Interbank fund transfer (IBFT) of PKR 15,000 received from Imran Ali on 21-Nov-2026. Available balance PKR 41,200.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Bank of Punjab: Khidmat stipend of PKR 6,000 credited to Khidmat Card account # ****9921 on 20-Nov-2026.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Askari Bank: Dividend payout of PKR 4,200 from Fauji Fertilizer Company credited to your CDC investor account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Standard Chartered: Profit payment of PKR 8,500 on your Saadiq Term Deposit credited to primary checking account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Faysal Bank: Cash deposit of PKR 20,000 at branch counter credited to account ****7712. Balance: PKR 55,000.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Nayapay: Raast credit alert! PKR 3,500 received from Sarah Ahmed. Updated wallet balance PKR 7,850.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Sadapay: You received Rs 2,000 from Hamza via Raast ID. Tap to view transaction details.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("حبیب بینک تنخواہ کریڈٹ: آپ کے اکاؤنٹ نمبر 4409 میں ماہانہ تنخواہ 45,000 روپے جمع ہو چکی ہے۔ دستیاب بیلنس 52,100 روپے۔", "LEGIT", "FINANCIAL_TRANSFER"),
    ("قومی بینک پنشن: آپ کے اکاؤنٹ میں ماہ نومبر کی پنشن 28,000 روپے کامیابی سے منتقل کر دی گئی ہے۔", "LEGIT", "FINANCIAL_TRANSFER"),
    ("میزان بینک: بی آئی ایس پی کی کفالت قسط 10,500 روپے براہ راست آپ کے اکاؤنٹ میں جمع ہو گئی ہے۔", "LEGIT", "FINANCIAL_TRANSFER"),
    ("ایزی پیسہ: آپ کے اکاؤنٹ میں 4,000 روپے وصول ہوئے۔ کل دستیاب بیلنس 9,800 روپے۔", "LEGIT", "FINANCIAL_TRANSFER"),
    ("جاز کیش: محمد سلیم کی جانب سے 6,500 روپے راست کے ذریعے موصول ہوئے۔ کوئی کٹوتی نہیں ہوئی۔", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Sindh Bank: Direct relief compensation of PKR 30,000 credited to account ****3321 by Provincial Disaster Management Authority.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Bank of Khyber: Scholarship allowance of PKR 18,000 credited to student account # ****8821.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Soneri Bank: Inward clearing cheque of PKR 50,000 cleared and credited to business account ****1120.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("JS Bank: Western Union international remittance of PKR 42,000 credited to your savings account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Al Baraka Bank: Murabaha financing proceeds of PKR 120,000 disbursed to customer account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Habib Metropolitan Bank: Profit on savings balance PKR 1,850 credited for the period ending Nov 2026.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Zarai Taraqiati Bank: Agri subsidy credit of PKR 12,000 transferred by Agriculture Department into Kissan account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("Mobilink Microfinance: Biometric disbursement of Rs 15,000 successfully processed at branch.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("FINCA Microfinance: Monthly installment rebate PKR 500 credited to borrower account.", "LEGIT", "FINANCIAL_TRANSFER"),
    ("یو بی ایل راست کریڈٹ: آپ کے اکاؤنٹ میں حکومت پنجاب کی طرف سے 12,000 روپے کی مالی گرانٹ موصول ہو گئی۔", "LEGIT", "FINANCIAL_TRANSFER"),

    # =========================================================================
    # 10. LEGIT: ANTI-SCAM ADVISORIES & OFFICIAL HELPLINE MESSAGES (30 Messages)
    # =========================================================================
    ("State Bank of Pakistan Warning: SBP or your bank will NEVER ask for your ATM PIN, OTP, password, or CVV. Never share banking credentials with anyone.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("BISP Public Advisory: BISP never charges any fee for registration or cash release. If anyone asks for money, report immediately to official toll-free helpline 0800-26477.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("PTA Consumer Alert: Beware of fake lottery calls and SMS claiming prizes under Ehsaas or BISP. PTA advises citizens to report fraudulent numbers to 8866.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("FIA Cyber Crime Alert: Never click on unverified links or install unknown APK files promising cash relief. Report cyber fraud at complaint.nr3c.gov.pk or call 1991.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("JazzCash Security Advisory: Do not share your 4-digit MPIN or verification OTP with anyone, including individuals claiming to call from JazzCash helpline.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("EasyPaisa Advisory: EasyPaisa representatives will never call you to ask for your secret PIN or OTP code. Keep your account secure.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("NADRA Citizen Alert: Official communication from NADRA is only sent from verified code 8500. Beware of fake SMS from personal mobile numbers.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Ehsaas Official Helpline 8171: Government relief assistance is completely free of cost. Never pay any fee or bribe to agents or campsite operators.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("HBL Fraud Awareness: Bank staff will never request your mobile banking password, ATM PIN or one-time passcode over phone or SMS.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Meezan Bank Security Tip: Protect your funds. Always keep your internet banking login details confidential. Meezan never asks for your credentials.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("UBL Security Notification: Be vigilant against social engineering and phishing attacks. Do not disclose secret codes received on your phone.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Bank Alfalah Alert: Fake calls claiming lottery wins are fraudulent. Never transfer money to unknown accounts to claim prizes.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("National Bank of Pakistan: Safeguard your pension. NBP officials will never ask for your card PIN or debit card details.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Ministry of Information: Beware of false claims on social media regarding fake cash schemes. Verify all announcements at official portal www.pakistan.gov.pk.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Sindh Police Helpline: Citizens receiving threatening or extortion SMS related to fake lottery wins should contact helpline 15 immediately.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("سٹیٹ بینک آف پاکستان کا انتباہ: اسٹیٹ بینک یا کوئی بھی کمرشل بینک کبھی بھی آپ سے اے ٹی ایم پن کوڈ یا او ٹی پی نہیں مانگتا۔ اپنا خفیہ کوڈ کسی کو نہ بتائیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("بے نظیر پروگرام وارننگ: بی آئی ایس پی کا کوئی واٹس ایپ گروپ نہیں ہے۔ وظیفے کے لیے کوئی فیس نہیں لی جاتی۔ دھوکے بازوں سے ہوشیار رہیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("پی ٹی اے پبلک الرٹ: جعلی کالز اور 8171 کے نام سے موصول ہونے والے فراڈ پیغامات کی اطلاع فوری طور پر پی ٹی اے ہیلپ لائن 8866 پر دیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("ایف آئی اے سائبر کرائم ونگ: احساس پروگرام کے نام پر او ٹی پی یا رقم مانگنے والے عناصر کی اطلاع ہیلپ لائن 1991 پر دیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("جاز کیش انتباہ: کمپنی کا نمائندہ بن کر خفیہ پن مانگنے والوں کو کبھی جواب نہ دیں۔ جاز کیش کی کوئی رجسٹریشن فیس نہیں ہے۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("ایزی پیسہ حفاظتی پیغام: اپنا خفیہ پن اور تصدیقی کوڈ کسی کے ساتھ شیئر نہ کریں۔ ہوشیار رہیں اور محفوظ رہیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("حکومت پاکستان کا انتباہ: سرکاری امدادی رقم مکمل طور پر مفت ہے۔ کسی کو کوئی فیس یا کٹوتی نہ دیں۔ شکایت کی صورت میں 8171 پر رابطہ کریں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("نادرا انتباہ: نادرا کبھی بھی واٹس ایپ یا ذاتی نمبر سے فون کر کے بینک کی تفصیلات نہیں مانگتا۔ جعلسازوں سے محفوظ رہیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("1Link Anti-Fraud Notice: Interbank cash withdrawals require only your physical presence and PIN at genuine bank ATMs. Never disclose PIN to third parties.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Punjab Police Counter-Fraud: Do not entertain callers asking for advance money to disburse solar panels or electric bikes. It is a fraud.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("KPK Police Helpline: Inform local police immediately if any unauthorized person demands registration charges for Insaf Imdad scheme.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Balochistan Anti-Corruption: Government disaster relief cash is disbursed without any service fee or deductions. Report extortion to 1415.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Nayapay Security Alert: Protect your digital account. Never input your security PIN on external links or third-party websites.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("Sadapay Fraud Prevention: We never call customers asking for verification codes or password. Ignore suspicious callers.", "LEGIT", "ANTI_SCAM_ADVISORY"),
    ("پبلک سروس میسج: بینظیر وظائف کی رقم صرف مخصوص بائیو میٹرک کیمپوں سے حاصل کریں۔ کسی ایجنٹ کو پیسے مت دیں۔", "LEGIT", "ANTI_SCAM_ADVISORY"),
]


def run_scam_evaluation():
    print("=" * 80)
    print("INDEPENDENT 300-MESSAGE SCAM EVALUATION BENCHMARK")
    print("Pre-Production Security Gate Evaluation")
    print("=" * 80)

    total_messages = len(EVALUATION_DATASET)
    assert total_messages == 300, f"Expected 300 messages, found {total_messages}!"

    # 3-Class Confusion Matrix:
    # rows: Actual (SCAM, LEGIT)
    # cols: Pred (SCAM, LEGIT, UNSURE)
    matrix = {
        "SCAM": {"SCAM": 0, "LEGIT": 0, "UNSURE": 0},
        "LEGIT": {"SCAM": 0, "LEGIT": 0, "UNSURE": 0}
    }

    # Tracking categories
    cat_stats: Dict[str, Dict[str, int]] = {}
    
    # Credential leakage tracking (CRITICAL)
    credential_failures: List[Dict] = []
    otp_total = 0
    otp_scam_detected = 0
    pin_total = 0
    pin_scam_detected = 0

    for text, actual_label, category in EVALUATION_DATASET:
        if category not in cat_stats:
            cat_stats[category] = {"TOTAL": 0, "SCAM": 0, "LEGIT": 0, "UNSURE": 0}
        cat_stats[category]["TOTAL"] += 1

        result = classify_message(text)
        pred_label = result["label"].value.upper()  # "SCAM", "LEGIT", "UNSURE"

        matrix[actual_label][pred_label] += 1
        cat_stats[category][pred_label] += 1

        # Check OTP and PIN detection
        if category == "OTP_THEFT":
            otp_total += 1
            if pred_label == "SCAM":
                otp_scam_detected += 1
            elif pred_label == "LEGIT":
                credential_failures.append({"type": "OTP", "text": text, "pred": pred_label, "res": result})
        elif category == "PIN_THEFT":
            pin_total += 1
            if pred_label == "SCAM":
                pin_scam_detected += 1
            elif pred_label == "LEGIT":
                credential_failures.append({"type": "PIN", "text": text, "pred": pred_label, "res": result})

    actual_scams = 150
    actual_legits = 150

    tp_scam = matrix["SCAM"]["SCAM"]
    fn_scam = matrix["SCAM"]["LEGIT"]
    unsure_scam = matrix["SCAM"]["UNSURE"]

    fp_legit = matrix["LEGIT"]["SCAM"]
    tn_legit = matrix["LEGIT"]["LEGIT"]
    unsure_legit = matrix["LEGIT"]["UNSURE"]

    # Metrics computation (STRICT: Never count UNSURE as SCAM)
    scam_recall = tp_scam / actual_scams
    scam_precision = tp_scam / (tp_scam + fp_legit) if (tp_scam + fp_legit) > 0 else 0.0
    fpr_legit = fp_legit / actual_legits
    fnr_scam = fn_scam / actual_scams
    unsure_rate_legit = unsure_legit / actual_legits
    unsure_rate_scam = unsure_scam / actual_scams

    otp_detection_rate = (otp_scam_detected / otp_total) * 100.0 if otp_total > 0 else 0.0
    pin_detection_rate = (pin_scam_detected / pin_total) * 100.0 if pin_total > 0 else 0.0

    print("\n--- 3-CLASS CONFUSION MATRIX (STRICT) ---")
    print(f"{'Actual':<10} | {'Pred SCAM':<12} | {'Pred LEGIT':<12} | {'Pred UNSURE':<12} | {'Total':<6}")
    print("-" * 62)
    print(f"{'SCAM':<10} | {tp_scam:<12} | {fn_scam:<12} | {unsure_scam:<12} | {actual_scams:<6}")
    print(f"{'LEGIT':<10} | {fp_legit:<12} | {tn_legit:<12} | {unsure_legit:<12} | {actual_legits:<6}")
    print("-" * 62)
    print(f"{'Total':<10} | {tp_scam + fp_legit:<12} | {fn_scam + tn_legit:<12} | {unsure_scam + unsure_legit:<12} | {total_messages:<6}")

    print("\n--- PERFORMANCE METRICS ---")
    print(f"Scam Recall:                           {scam_recall * 100:.2f}% ({tp_scam}/{actual_scams})")
    print(f"Scam Precision:                        {scam_precision * 100:.2f}% ({tp_scam}/{tp_scam + fp_legit})")
    print(f"False Positive Rate (Legit -> SCAM):    {fpr_legit * 100:.2f}% ({fp_legit}/{actual_legits})")
    print(f"False Negative Rate (Scam -> LEGIT):     {fnr_scam * 100:.2f}% ({fn_scam}/{actual_scams})")
    print(f"UNSURE Rate on Legitimate Messages:    {unsure_rate_legit * 100:.2f}% ({unsure_legit}/{actual_legits})")
    print(f"UNSURE Rate on Scam Messages:          {unsure_rate_scam * 100:.2f}% ({unsure_scam}/{actual_scams})")

    print("\n--- CRITICAL CREDENTIAL THEFT METRICS ---")
    print(f"OTP Theft Detection Rate:              {otp_detection_rate:.2f}% ({otp_scam_detected}/{otp_total})")
    print(f"PIN Theft Detection Rate:              {pin_detection_rate:.2f}% ({pin_scam_detected}/{pin_total})")
    print(f"Credential Thefts Classified as LEGIT: {len(credential_failures)}")

    if credential_failures:
        print("\n[CRITICAL FAILURE] The following credential theft messages leaked into LEGIT:")
        for cf in credential_failures:
            print(f" - [{cf['type']}] {cf['text']}")
            print(f"   Reasons: {cf['res'].get('reasons')}, Prob: {cf['res'].get('scam_probability')}")
    else:
        print("[PASS] Zero credential theft messages classified as legitimate!")

    print("\n--- BREAKDOWN BY CATEGORY ---")
    print(f"{'Category':<24} | {'Total':<6} | {'SCAM':<6} | {'LEGIT':<6} | {'UNSURE':<6} | {'Accuracy/Detection'}")
    print("-" * 75)
    for cat, counts in cat_stats.items():
        is_scam_cat = cat in ["OTP_THEFT", "PIN_THEFT", "ADVANCE_FEE", "ROMAN_URDU_PHISH", "URDU_PHISH"]
        expected = "SCAM" if is_scam_cat else "LEGIT"
        correct = counts[expected]
        rate = (correct / counts["TOTAL"]) * 100.0
        print(f"{cat:<24} | {counts['TOTAL']:<6} | {counts['SCAM']:<6} | {counts['LEGIT']:<6} | {counts['UNSURE']:<6} | {rate:.1f}% as {expected}")

    return {
        "matrix": matrix,
        "scam_recall": scam_recall,
        "scam_precision": scam_precision,
        "fpr_legit": fpr_legit,
        "fnr_scam": fnr_scam,
        "unsure_rate_legit": unsure_rate_legit,
        "unsure_rate_scam": unsure_rate_scam,
        "otp_detection_rate": otp_detection_rate,
        "pin_detection_rate": pin_detection_rate,
        "credential_failures": credential_failures,
        "cat_stats": cat_stats
    }


if __name__ == "__main__":
    run_scam_evaluation()
