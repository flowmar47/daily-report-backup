#!/usr/bin/env python3
"""
Send heatmap images directly to Signal using REST API
"""

import os
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_image_to_signal(image_path, caption):
    """Send image to Signal group using REST API"""
    signal_phone = os.getenv('SIGNAL_PHONE_NUMBER')
    signal_group = os.getenv('SIGNAL_GROUP_ID')
    api_url = "http://localhost:8080"
    
    if not all([signal_phone, signal_group]):
        print("❌ Missing Signal credentials")
        return False
    
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Try sending with attachment using form data
        files = {
            'attachment': (os.path.basename(image_path), image_data, 'image/png')
        }
        
        data = {
            'number': signal_phone,
            'recipients': signal_group,
            'message': caption
        }
        
        print(f"📤 Sending {os.path.basename(image_path)} to Signal...")
        
        # Try v2 API with multipart form data
        response = requests.post(
            f"{api_url}/v2/send",
            files=files,
            data=data
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ {caption} sent to Signal successfully")
            return True
        else:
            print(f"❌ Failed to send to Signal: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending to Signal: {e}")
        return False

def main():
    """Send both heatmaps to Signal"""
    print("📊 Sending heatmaps to Signal...")
    
    # Use latest heatmaps
    heatmap_dir = "/home/ohms/OhmsAlertsReports/daily-report/heatmaps/reports/20250626_100437"
    categorical_path = f"{heatmap_dir}/categorical_heatmap.png"
    forex_path = f"{heatmap_dir}/forex_pairs_heatmap.png"
    
    success_count = 0
    
    # Send categorical heatmap
    if os.path.exists(categorical_path):
        if send_image_to_signal(categorical_path, "📊 Global Interest Rates - Categorical Analysis"):
            success_count += 1
    else:
        print(f"❌ Categorical heatmap not found: {categorical_path}")
    
    # Send forex heatmap
    if os.path.exists(forex_path):
        if send_image_to_signal(forex_path, "🌍 Forex Pairs Differential Matrix"):
            success_count += 1
    else:
        print(f"❌ Forex heatmap not found: {forex_path}")
    
    if success_count == 2:
        print("🎉 Both heatmaps sent to Signal successfully!")
        return True
    elif success_count == 1:
        print("⚠️ Only one heatmap sent successfully")
        return True
    else:
        print("❌ Failed to send heatmaps to Signal")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)