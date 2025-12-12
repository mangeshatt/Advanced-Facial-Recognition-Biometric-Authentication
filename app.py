import time
import redis
import json
import logging
from datetime import datetime

# ==========================================
# 1. SETUP LOGGING
# ==========================================
# We use a specific log for Ad Fraud evidence
ad_fraud_logger = logging.getLogger('ad_fraud_logger')
ad_fraud_logger.setLevel(logging.INFO)
if ad_fraud_logger.hasHandlers():
    ad_fraud_logger.handlers.clear()
# Log strictly to ad_bot_evidence.txt
ad_handler = logging.FileHandler('ad_bot_evidence.txt')
ad_handler.setFormatter(logging.Formatter('%(message)s'))
ad_fraud_logger.addHandler(ad_handler)

class AdBotGuard:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # RULES
        self.SPEED_LIMIT = 1.75        # Speed Rule (still applies)
        self.AD_BOT_LIMIT = 500        # The "Ad Bot" Volume Threshold

    def _log_ad_fraud(self, ip, count):
        """
        Logs evidence specifically for Ad Fraud analysis.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "risk": "CRITICAL_AD_FRAUD",
            "ip": ip,
            "hits_recorded": count,
            "message": "Traffic volume indicates automated ad-click bot."
        }
        ad_fraud_logger.info(json.dumps(entry))
        print(f"🚨 AD BOT DETECTED [{ip}]: Request #{count} BLOCKED.")

    def process_traffic(self, ip):
        """
        Main Filter Loop
        """
        vol_key = f"stats:vol:{ip}"

        # --- STEP 1: INCREMENT COUNTER ---
        # We increment first to see the current count
        current_vol = self.r.incr(vol_key)
        
        # If this is the first hit, set a 1-hour expiry window
        if current_vol == 1:
            self.r.expire(vol_key, 3600)

        # --- STEP 2: CHECK THE "500 to 501" THRESHOLD ---
        # The user requested: Identify if Hit > 500
        if current_vol > self.AD_BOT_LIMIT:
            # We specifically catch the 501st hit and onwards
            self._log_ad_fraud(ip, current_vol)
            return False, f"BLOCKED: Ad Bot Behavior Detected ({current_vol} > {self.AD_BOT_LIMIT})"

        # --- STEP 3: STANDARD PROCESSING ---
        return True, f"ALLOWED: Request {current_vol}/{self.AD_BOT_LIMIT}"

# ==========================================
# 2. THE TEST SIMULATION
# ==========================================
if __name__ == "__main__":
    guard = AdBotGuard()
    test_ip = "45.33.22.11" # Simulated Ad Bot IP

    print(f"--- STARTING STRESS TEST FOR IP: {test_ip} ---")
    print(f"Goal: Allow 500 requests, BLOCK the 501st.\n")

    # We simulate a loop of 505 requests to prove the boundary works
    # (We use a loop range logic to skip printing all 500 lines for clarity)
    
    start_time = time.time()
    
    for i in range(1, 506):
        allowed, msg = guard.process_traffic(test_ip)
        
        # VISUALIZATION LOGIC
        if i == 1:
            print(f"Request 1:   {msg}")
        elif i == 500:
            print(f"Request 500: {msg} (Limit Reached)")
        elif i == 501:
            print(f"\n---> TRIGGERING DETECTION AT 501 <---")
            print(f"Request 501: {msg}") # THIS SHOULD FAIL
        elif i > 501:
            print(f"Request {i}: {msg}") # THESE SHOULD ALSO FAIL

    print(f"\n--- TEST COMPLETE ---")
    print(f"Check 'ad_bot_evidence.txt' for the forensic log of the 501st hit.")
