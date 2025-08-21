# Signal Group Invite Link Instructions

## Getting the Invite Link from Signal App

Since the Signal CLI REST API doesn't support generating invite links directly, you'll need to create it from the Signal app:

### 📱 Steps to Get Group Invite Link:

1. **Open Signal** on your phone (linked to +16572463906)

2. **Go to the Group**
   - Find "Ohms Alerts Reports" in your conversations

3. **Access Group Settings**
   - Tap the group name at the top of the chat

4. **Enable Group Link**
   - Scroll down to "Group link"
   - Toggle it ON if it's off
   - You'll see options:
     - Share link
     - Reset link
     - Turn off group link

5. **Copy the Link**
   - Tap "Share link"
   - Choose "Copy" or share directly

The link will look something like:
```
https://signal.group/#CjQKIFmWfWRPpv7xc8Z7i790H56Zikz91gpM_AXRMFGq5ZFYEhD...
```

## 🔐 Group Details for Manual Addition

If you prefer to add members manually:

- **Group Name**: Ohms Alerts Reports
- **Group ID**: `group.V1paOVpFK20vdkZ6eG51THYzUWZucG1LVFAzV0NrejhCZEV3VWFybGtWWT0=`
- **Admin Phone**: +16572463906

## 👥 Adding Members via API

You can also add members programmatically if you know their Signal numbers:

```bash
curl -X PUT http://localhost:8080/v1/groups/+16572463906 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "group.V1paOVpFK20vdkZ6eG51THYzUWZucG1LVFAzV0NrejhCZEV3VWFybGtWWT0=",
    "members": ["+16572463906", "+1NEWMEMBERNUMBER"]
  }'
```

## 🤖 Automated Alerts

Once members join the group, they'll automatically receive:
- Daily financial reports at 8 AM PST
- Forex signals from MyMama
- Same content as the Telegram group

## 📊 Current Group Status

- **Members**: 1 (admin only)
- **Type**: Private group
- **Purpose**: Automated financial alerts
- **Delivery**: Daily at 8 AM PST on weekdays