#!/bin/bash
# Accept Signal Group Invitation

PHONE_NUMBER="+16572463906"

echo "Checking for Signal group invitations..."

# Check for incoming messages/invitations
MESSAGES=$(curl -s -X GET "http://localhost:8080/v1/receive/$PHONE_NUMBER")
echo "Incoming messages: $MESSAGES"

# Check current groups
GROUPS=$(curl -s -X GET "http://localhost:8080/v1/groups/$PHONE_NUMBER")
echo "Current groups: $GROUPS"

# If we find a group invitation, we would accept it here
# The exact method depends on the Signal CLI REST API version

echo "Done checking for invitations."