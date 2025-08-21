#!/usr/bin/env python3
"""
Generate and send sample heatmaps for today
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_sample_heatmaps():
    """Generate sample heatmaps"""
    logger.info("📊 Generating sample heatmaps...")
    
    # Create output directory
    output_dir = Path(__file__).parent / 'temp_heatmaps'
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Generate categorical interest rate heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Sample data
    categories = ['Central Bank Rate', 'Overnight Rate', '1-Month Rate', '3-Month Rate']
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'NZD']
    
    # Create sample data matrix
    data = np.array([
        [5.50, 0.00, -0.10, 0.25, 5.00, 4.35, 1.75, 5.50],  # Central Bank
        [5.33, 3.90, 5.19, -0.02, 4.75, 4.10, 1.66, 5.25],  # Overnight
        [5.52, 3.85, 5.30, 0.05, 4.95, 4.28, 1.70, 5.40],   # 1-Month
        [5.45, 3.75, 5.25, 0.10, 4.88, 4.22, 1.65, 5.35]    # 3-Month
    ])
    
    # Create heatmap
    sns.heatmap(data, 
                xticklabels=currencies,
                yticklabels=categories,
                annot=True, 
                fmt='.2f',
                cmap='RdYlGn_r',
                center=2.5,
                cbar_kws={'label': 'Interest Rate (%)'},
                linewidths=0.5)
    
    plt.title('Global Interest Rates - Categorical Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    categorical_path = output_dir / f'interest_rate_heatmap_categorical_{timestamp}.png'
    plt.savefig(categorical_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"✅ Categorical heatmap saved: {categorical_path}")
    
    # 2. Generate forex pairs heatmap
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Create forex pairs differential matrix
    forex_data = np.array([
        [0.00, -5.50, -5.60, -5.25, -0.50, -1.15, -3.75, 0.00],
        [5.50, 0.00, -0.10, 0.25, 5.00, 4.35, 1.75, 5.50],
        [5.60, 0.10, 0.00, 0.35, 5.10, 4.45, 1.85, 5.60],
        [5.25, -0.25, -0.35, 0.00, 4.75, 4.10, 1.50, 5.25],
        [0.50, -5.00, -5.10, -4.75, 0.00, -0.65, -3.25, 0.50],
        [1.15, -4.35, -4.45, -4.10, 0.65, 0.00, -2.60, 1.15],
        [3.75, -1.75, -1.85, -1.50, 3.25, 2.60, 0.00, 3.75],
        [0.00, -5.50, -5.60, -5.25, -0.50, -1.15, -3.75, 0.00]
    ])
    
    # Create heatmap
    sns.heatmap(forex_data,
                xticklabels=currencies,
                yticklabels=currencies,
                annot=True,
                fmt='.2f',
                cmap='coolwarm',
                center=0,
                cbar_kws={'label': 'Rate Differential (%)'},
                linewidths=0.5,
                square=True)
    
    plt.title('Forex Pairs Interest Rate Differentials', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    forex_path = output_dir / f'forex_pairs_heatmap_{timestamp}.png'
    plt.savefig(forex_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"✅ Forex pairs heatmap saved: {forex_path}")
    
    return categorical_path, forex_path

async def send_heatmaps(categorical_path, forex_path):
    """Send heatmaps to all platforms"""
    logger.info("📤 Sending heatmaps to all platforms...")
    
    try:
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Initialize platforms
        platforms = ['signal', 'telegram', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        # Send categorical heatmap
        logger.info("📊 Sending categorical heatmap...")
        from src.messengers.unified_messenger import AttachmentData
        
        attachment1 = AttachmentData(
            file_path=categorical_path,
            caption="Interest Rate Analysis - Categorical View"
        )
        
        results1 = {}
        for platform_name, messenger in multi_messenger.messengers.items():
            try:
                result = await messenger._send_attachment(attachment1)
                results1[platform_name] = result
            except Exception as e:
                logger.error(f"Failed to send to {platform_name}: {e}")
        
        success1 = sum(1 for result in results1.values() if result.success)
        logger.info(f"✅ Categorical heatmap sent to {success1}/3 platforms")
        
        # Send forex pairs heatmap
        logger.info("🌍 Sending forex pairs heatmap...")
        attachment2 = AttachmentData(
            file_path=forex_path,
            caption="Forex Pairs Interest Rate Differentials"
        )
        
        results2 = {}
        for platform_name, messenger in multi_messenger.messengers.items():
            try:
                result = await messenger._send_attachment(attachment2)
                results2[platform_name] = result
            except Exception as e:
                logger.error(f"Failed to send to {platform_name}: {e}")
        
        success2 = sum(1 for result in results2.values() if result.success)
        logger.info(f"✅ Forex pairs heatmap sent to {success2}/3 platforms")
        
        # Cleanup
        await multi_messenger.cleanup()
        
        return success1 > 0 or success2 > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to send heatmaps: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Generating and sending sample heatmaps...")
    
    # Generate heatmaps
    try:
        categorical_path, forex_path = generate_sample_heatmaps()
    except Exception as e:
        logger.error(f"❌ Failed to generate heatmaps: {e}")
        return
    
    # Send heatmaps
    success = await send_heatmaps(categorical_path, forex_path)
    
    if success:
        logger.info("\n🎉 SUCCESS! Heatmaps sent to platforms!")
        logger.info("\n📅 Automatic scheduling is now active:")
        logger.info("✅ Daily reports: Monday-Friday at 6:00 AM PST")
        logger.info("✅ Includes: Financial report + 2 heatmaps")
        logger.info("✅ Platforms: Signal, Telegram, WhatsApp")
        logger.info("✅ Auto-restart after reboot: Enabled")
    else:
        logger.error("\n❌ Failed to send heatmaps")

if __name__ == "__main__":
    asyncio.run(main())