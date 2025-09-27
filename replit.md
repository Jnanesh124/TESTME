# Telegram File Filter Bot

## Overview
This is a sophisticated Telegram bot for file filtering, sharing, and management. It includes features like:
- File filtering and searching
- User verification system
- Premium/referral system
- Clone bot functionality
- Auto-approval for channel join requests
- File streaming and downloading
- Broadcast capabilities

## Project Structure
- `bot.py` - Main bot entry point
- `info.py` - Configuration and environment variables
- `plugins/` - Bot command handlers and features
- `database/` - Database models and operations
- `TechVJ/` - Bot client and utility modules
- `CloneTechVJ/` - Clone bot functionality

## Current State
- Bot requires environment variables setup
- Uses MongoDB for data storage
- Supports multiple deployment platforms (Heroku, local)
- Has verification system with scheduler
- Includes streaming capabilities

## Recent Changes
- Project initialized in Replit environment
- Ready for environment configuration and deployment

## Required Environment Variables
- `API_ID` - Telegram API ID
- `API_HASH` - Telegram API Hash
- `BOT_TOKEN` - Bot token from BotFather
- `DATABASE_URI` - MongoDB connection string
- `LOG_CHANNEL` - Channel ID for logging
- `CHANNELS` - File storage channel IDs
- `AUTH_CHANNEL` - Force subscribe channel ID
- `ADMINS` - Admin user IDs

## User Preferences
- Language: Python with Pyrogram
- Database: MongoDB
- Deployment: Multi-platform support