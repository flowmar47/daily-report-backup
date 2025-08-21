#!/usr/bin/env python3
import os
import shutil

def check_disk_usage():
    """Check disk usage for key directories"""
    
    print("=== DISK USAGE CHECK ===")
    
    # Check overall disk usage
    statvfs = os.statvfs('/')
    total = statvfs.f_frsize * statvfs.f_blocks
    free = statvfs.f_frsize * statvfs.f_avail
    used = total - free
    
    print(f"Root filesystem:")
    print(f"  Total: {total / 1024**3:.1f} GB")
    print(f"  Used:  {used / 1024**3:.1f} GB ({used/total*100:.1f}%)")
    print(f"  Free:  {free / 1024**3:.1f} GB")
    
    # Check /tmp
    try:
        statvfs_tmp = os.statvfs('/tmp')
        total_tmp = statvfs_tmp.f_frsize * statvfs_tmp.f_blocks
        free_tmp = statvfs_tmp.f_frsize * statvfs_tmp.f_avail
        used_tmp = total_tmp - free_tmp
        
        print(f"\n/tmp filesystem:")
        print(f"  Total: {total_tmp / 1024**2:.1f} MB")
        print(f"  Used:  {used_tmp / 1024**2:.1f} MB ({used_tmp/total_tmp*100:.1f}%)")
        print(f"  Free:  {free_tmp / 1024**2:.1f} MB")
    except:
        print("\nCould not check /tmp")
    
    # Check specific directories
    dirs_to_check = [
        '/home/ohms/.cache/ms-playwright',
        '/home/ohms/OhmsAlertsReports/daily-report/logs',
        '/home/ohms/OhmsAlertsReports/daily-report/venv',
        '/home/ohms/OhmsAlertsReports/daily-report/__pycache__'
    ]
    
    print("\n=== DIRECTORY SIZES ===")
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            try:
                size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(dir_path)
                          for filename in filenames)
                print(f"{dir_path}: {size / 1024**2:.1f} MB")
            except Exception as e:
                print(f"{dir_path}: Error calculating size - {e}")
        else:
            print(f"{dir_path}: Does not exist")

def clean_specific_items():
    """Clean specific items that we know can be safely removed"""
    
    print("\n=== CLEANING UP ===")
    
    # Remove playwright duplicate if it exists
    playwright_dup = "/home/ohms/.cache/ms-playwright/chromium_headless_shell-1169"
    if os.path.exists(playwright_dup):
        try:
            shutil.rmtree(playwright_dup)
            print(f"✓ Removed: {playwright_dup}")
        except Exception as e:
            print(f"✗ Could not remove {playwright_dup}: {e}")
    else:
        print(f"✓ Playwright duplicate already gone")
    
    # Clean empty log files
    log_dir = "/home/ohms/OhmsAlertsReports/daily-report/logs"
    if os.path.exists(log_dir):
        for log_file in os.listdir(log_dir):
            log_path = os.path.join(log_dir, log_file)
            if os.path.isfile(log_path) and os.path.getsize(log_path) == 0:
                try:
                    os.remove(log_path)
                    print(f"✓ Removed empty log: {log_file}")
                except Exception as e:
                    print(f"✗ Could not remove {log_file}: {e}")
    
    # Remove any __pycache__ in the main project (not venv)
    for root, dirs, files in os.walk("/home/ohms/OhmsAlertsReports"):
        # Skip venv directory
        if 'venv' in root:
            continue
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"✓ Removed: {pycache_path}")
            except Exception as e:
                print(f"✗ Could not remove {pycache_path}: {e}")

if __name__ == "__main__":
    check_disk_usage()
    clean_specific_items()
    print("\n=== DISK USAGE AFTER CLEANUP ===")
    check_disk_usage()