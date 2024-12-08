import time
import psutil
import os

def main():
    # Configuration parameters
    test_mode = False  # Set to False for actual shutdown
    CHECK_INTERVAL = 2  # seconds between checks
    HIGH_USAGE_THRESHOLD = 1 * 1024 * 1024  # ~1mb
    COOLDOWN_PERIOD = 5 * 60  # secs

    # State tracking
    downloading = False
    cooldown_start_time = None

    old_bytes_sent = psutil.net_io_counters().bytes_sent
    old_bytes_recv = psutil.net_io_counters().bytes_recv

    print("[INFO] Starting network usage monitoring...")
    print(f"[INFO] Test mode is {'ON' if test_mode else 'OFF'}")
    print(f"[INFO] Threshold: {HIGH_USAGE_THRESHOLD} bytes/s ({HIGH_USAGE_THRESHOLD / (1024*1024):.2f} MB/s)")
    print(f"[INFO] Cooldown Period: {COOLDOWN_PERIOD} seconds")
    print(f"[INFO] Check Interval: {CHECK_INTERVAL} seconds")

    while True:
        time.sleep(CHECK_INTERVAL)
        counters = psutil.net_io_counters()
        new_bytes_sent = counters.bytes_sent
        new_bytes_recv = counters.bytes_recv

        bytes_sent_diff = new_bytes_sent - old_bytes_sent
        bytes_recv_diff = new_bytes_recv - old_bytes_recv

        # Calculate rate in bytes/sec
        download_rate = bytes_recv_diff / CHECK_INTERVAL
        upload_rate = bytes_sent_diff / CHECK_INTERVAL

        old_bytes_sent = new_bytes_sent
        old_bytes_recv = new_bytes_recv

        print(f"[DEBUG] Current Rates -> Download: {download_rate/1024:.2f} KB/s, Upload: {upload_rate/1024:.2f} KB/s")

        if download_rate > HIGH_USAGE_THRESHOLD:
            # High usage detected
            print("[DEBUG] Download rate is ABOVE threshold.")
            if not downloading:
                # Switch to downloading state
                downloading = True
                cooldown_start_time = None
                print("[INFO] State Change: NOW DOWNLOADING. (downloading=True)")
            else:
                # Already downloading, check if we were in cooldown
                if cooldown_start_time is not None:
                    print("[INFO] Download resumed above threshold during cooldown. Canceling cooldown timer.")
                    cooldown_start_time = None
                else:
                    print("[DEBUG] Still in downloading state, no change.")
        else:
            # Usage below threshold
            print("[DEBUG] Download rate is BELOW threshold.")
            if downloading:
                # We were downloading before
                if cooldown_start_time is None:
                    cooldown_start_time = time.time()
                    print(f"[INFO] Starting cooldown timer at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                else:
                    elapsed = time.time() - cooldown_start_time
                    remaining = COOLDOWN_PERIOD - elapsed
                    print(f"[DEBUG] Cooldown in progress for {elapsed:.2f} seconds, {remaining:.2f} seconds remaining.")
                    if elapsed >= COOLDOWN_PERIOD:
                        print("[INFO] Cooldown finished. Download considered complete.")
                        if test_mode:
                            print("[TEST] Would shutdown now, but test mode is ON.")
                        else:
                            print("[INFO] Shutting down system...")
                            # Uncomment this line to actually shut down the PC:
                            os.system("shutdown /s /t 5")
                        # Reset state after completion
                        downloading = False
                        cooldown_start_time = None
                        print("[INFO] State Change: NO LONGER DOWNLOADING (reset to idle).")
                    else:
                        print("[DEBUG] Cooldown not yet complete, waiting more time.")
            else:
                # Not downloading and below threshold -> Idle
                if cooldown_start_time is not None:
                    # This would be unusual, but we handle it
                    print("[WARN] Cooldown timer found while not downloading. Resetting.")
                    cooldown_start_time = None
                else:
                    print("[DEBUG] Idle state, no action needed.")

if __name__ == "__main__":
    main()
