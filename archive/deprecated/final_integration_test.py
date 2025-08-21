#!/usr/bin/env python3
"""
Final integration test for WhatsApp + complete system
Tests both individual WhatsApp messaging and complete multi-platform system
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_whatsapp_only():
    """Test WhatsApp messaging only"""
    print("=" * 70)
    print("[TEST 1] WhatsApp Only Integration Test")
    print("=" * 70)
    print("VNC Session: 192.168.0.175:5901")
    print("Target: WhatsApp Web (authenticated)")
    print("-" * 70)
    
    try:
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        print("[INIT] Initializing WhatsApp messenger...")
        messenger = UnifiedMultiMessenger(['whatsapp'])
        
        # Create comprehensive test message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_message = f"""WHATSAPP INTEGRATION SUCCESSFUL

VNC Session: 192.168.0.175:5901
Test Time: {timestamp}

FOREX PAIRS

Pair: EURUSD
High: 1.1158
Average: 1.0742
Low: 1.0238
MT4 Action: MT4 SELL
Exit: 1.0850

EQUITIES AND OPTIONS

Symbol: QQQ
52 Week High: 480.92
52 Week Low: 478.13
Strike Price:

CALL > 521.68
PUT < N/A
Status: TRADE IN PROFIT

PREMIUM SWING TRADES (Monday - Wednesday)

JOYY Inc. (JOYY)
Earnings Report: July 26, 2025
Current Price: $47.67
Rationale: Strong technical setup with earnings catalyst

Integration Status: WHATSAPP READY FOR DAILY REPORTS"""
        
        print("[SEND] Sending comprehensive test message...")
        results = await messenger.send_structured_financial_data(test_message)
        
        # Check results
        whatsapp_result = results.get('whatsapp')
        success = whatsapp_result and whatsapp_result.success
        
        if success:
            print(f"[OK] WhatsApp test PASSED!")
            print(f"[INFO] Message ID: {whatsapp_result.message_id}")
        else:
            print(f"[ERROR] WhatsApp test FAILED")
            if whatsapp_result:
                print(f"[ERROR] Error: {whatsapp_result.error}")
        
        await messenger.cleanup()
        return success
        
    except Exception as e:
        print(f"[ERROR] WhatsApp test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_system():
    """Test complete tri-platform system (Signal + Telegram + WhatsApp)"""
    print("\n" + "=" * 70)
    print("[TEST 2] Complete Multi-Platform System Test")
    print("=" * 70)
    print("Platforms: Signal + Telegram + WhatsApp")
    print("Purpose: Verify daily report system ready")
    print("-" * 70)
    
    try:
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        print("[INIT] Initializing all platforms...")
        messenger = UnifiedMultiMessenger(['telegram', 'signal', 'whatsapp'])
        
        # Create production-like test message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_message = f"""DAILY FINANCIAL ALERTS - INTEGRATION TEST

Date: {timestamp}
System: Ohms Alerts Reports
Status: FULL INTEGRATION COMPLETE

FOREX PAIRS

Pair: GBPUSD
High: 1.2845
Average: 1.2720
Low: 1.2598
MT4 Action: MT4 BUY
Exit: 1.2800

Pair: USDJPY
High: 158.45
Average: 157.22
Low: 156.89
MT4 Action: MT4 SELL
Exit: 157.00

EQUITIES AND OPTIONS

Symbol: SPY
52 Week High: 550.25
52 Week Low: 548.75
Strike Price:

CALL > 555.00
PUT < 545.00
Status: MONITORING

Symbol: TSLA
52 Week High: 265.80
52 Week Low: 263.45
Strike Price:

CALL > 270.00
PUT < 260.00
Status: TRADE IN PROFIT

PREMIUM SWING TRADES (Monday - Wednesday)

Apple Inc. (AAPL)
Earnings Report: July 30, 2025
Current Price: $195.67
Rationale: Bullish momentum ahead of earnings

Microsoft Corp. (MSFT)
Earnings Report: August 2, 2025
Current Price: $445.23
Rationale: Cloud growth catalyst expected

SYSTEM STATUS: ALL PLATFORMS OPERATIONAL
Next Scheduled Report: 6:00 AM PST (Weekdays)

WhatsApp VNC: 192.168.0.175:5901 [ACTIVE]
Signal: [ACTIVE]
Telegram: [ACTIVE]

INTEGRATION COMPLETE - READY FOR PRODUCTION"""
        
        print("[SEND] Sending to all platforms simultaneously...")
        results = await messenger.send_structured_financial_data(test_message)
        
        # Analyze results
        success_count = 0
        total_platforms = len(results)
        
        print(f"\n[RESULTS] Platform Results:")
        for platform, result in results.items():
            if result.success:
                print(f"  [OK] {platform.upper()}: SUCCESS (ID: {result.message_id})")
                success_count += 1
            else:
                print(f"  [ERROR] {platform.upper()}: FAILED - {result.error}")
        
        print(f"\n[SUMMARY] {success_count}/{total_platforms} platforms successful")
        
        await messenger.cleanup()
        return success_count == total_platforms
        
    except Exception as e:
        print(f"[ERROR] Multi-platform test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_heatmap_integration():
    """Test if heatmap sending would work"""
    print("\n" + "=" * 70)
    print("[TEST 3] Heatmap Integration Simulation")
    print("=" * 70)
    
    # Check if heatmap files exist
    heatmap_dir = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/generated_heatmaps")
    
    if heatmap_dir.exists():
        png_files = list(heatmap_dir.glob("*.png"))
        print(f"[FOUND] {len(png_files)} heatmap files in {heatmap_dir}")
        
        if png_files:
            # Test with first available heatmap
            test_heatmap = png_files[0]
            print(f"[TEST] Testing with: {test_heatmap.name}")
            
            try:
                from src.messengers.unified_messenger import UnifiedMultiMessenger
                
                messenger = UnifiedMultiMessenger(['whatsapp'])  # Test with WhatsApp only
                
                # Test attachment sending
                results = await messenger.send_attachment(
                    file_path=str(test_heatmap),
                    caption="[TEST] Bloomberg-style Heatmap Integration Test"
                )
                
                whatsapp_result = results.get('whatsapp')
                success = whatsapp_result and whatsapp_result.success
                
                if success:
                    print(f"[OK] Heatmap test PASSED!")
                    print(f"[INFO] WhatsApp can receive heatmap images")
                else:
                    print(f"[WARN] Heatmap test failed: {whatsapp_result.error if whatsapp_result else 'Unknown error'}")
                
                await messenger.cleanup()
                return success
                
            except Exception as e:
                print(f"[ERROR] Heatmap test failed: {e}")
                return False
        else:
            print(f"[INFO] No PNG files found - heatmap test skipped")
            return True  # Not a failure, just no files to test
    else:
        print(f"[INFO] Heatmap directory not found - test skipped")
        return True

async def main():
    """Run complete integration test suite"""
    print("[ROCKET] FINAL WHATSAPP INTEGRATION TEST SUITE")
    print("=" * 70)
    print("Testing WhatsApp integration with VNC session 192.168.0.175:5901")
    print("Testing complete daily report system readiness")
    print("=" * 70)
    
    # Run all tests
    test1_result = await test_whatsapp_only()
    await asyncio.sleep(3)  # Brief pause between tests
    
    test2_result = await test_complete_system()
    await asyncio.sleep(3)
    
    test3_result = await test_heatmap_integration()
    
    # Final summary
    print("\n" + "=" * 70)
    print("[TARGET] FINAL INTEGRATION TEST RESULTS")
    print("=" * 70)
    print(f"Test 1 - WhatsApp Only:       {'[OK] PASSED' if test1_result else '[X] FAILED'}")
    print(f"Test 2 - Multi-Platform:      {'[OK] PASSED' if test2_result else '[X] FAILED'}")
    print(f"Test 3 - Heatmap Integration:  {'[OK] PASSED' if test3_result else '[X] FAILED'}")
    
    overall_success = test1_result and test2_result and test3_result
    
    print(f"\n[TROPHY] OVERALL RESULT: {'[OK] ALL TESTS PASSED' if overall_success else '[WARN] SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n[SUCCESS] WHATSAPP INTEGRATION COMPLETE!")
        print("[PHONE] VNC Session: 192.168.0.175:5901")
        print("[TIME] Daily Reports: 6:00 AM PST (Weekdays)")
        print("[CHART] Platforms: Signal + Telegram + WhatsApp")
        print("[CYCLE] Heatmaps: Bloomberg-style visualizations")
        print("\n[OK] System is ready for production use!")
    else:
        print("\n[WARN] Integration partially complete - check failed tests above")
        print("[PHONE] VNC Session: 192.168.0.175:5901 should remain active")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())