#!/usr/bin/env python3
"""Send heatmap images to Telegram"""

import os
import asyncio
from pathlib import Path
from telegram import Bot

async def send_heatmaps():
    """Send heatmap images to Telegram group"""
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    if not bot_token or not group_id:
        print("❌ Telegram credentials not configured")
        return
    
    bot = Bot(token=bot_token)
    
    # Find latest heatmaps
    heatmap_dir = Path("heatmaps/reports")
    
    if heatmap_dir.exists():
        # Get the latest directory
        dirs = [d for d in heatmap_dir.iterdir() if d.is_dir() and d.name.startswith("2025")]
        if dirs:
            latest_dir = max(dirs, key=lambda d: d.name)
            categorical = latest_dir / "categorical_heatmap.png"
            forex_pairs = latest_dir / "forex_pairs_heatmap.png"
            
            print(f"📊 Found heatmaps from: {latest_dir.name}")
            
            # Send categorical heatmap
            if categorical.exists():
                print("📤 Sending categorical heatmap...")
                with open(categorical, 'rb') as f:
                    await bot.send_photo(
                        chat_id=group_id,
                        photo=f,
                        caption="📊 Interest Rate Heatmap - Categorical Analysis"
                    )
                print("✅ Categorical heatmap sent!")
            
            # Send forex pairs heatmap
            if forex_pairs.exists():
                print("📤 Sending forex pairs heatmap...")
                with open(forex_pairs, 'rb') as f:
                    await bot.send_photo(
                        chat_id=group_id,
                        photo=f,
                        caption="💱 Interest Rate Heatmap - Forex Pairs"
                    )
                print("✅ Forex pairs heatmap sent!")
            
            print("\n🎉 Heatmaps sent successfully!")
        else:
            print("❌ No heatmap directories found")
    else:
        print("❌ Heatmap directory not found")

if __name__ == "__main__":
    asyncio.run(send_heatmaps())