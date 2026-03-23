# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# EgoZone - AI Digital Twin Project Guide

## Project Overview
EgoZone is a personal AI digital twin system based on Google Gemini, featuring personalized conversations, knowledge base management, voice interaction, and platform integration.

## Technical Architecture
- **Backend**: Python FastAPI
- **AI Engine**: Google Gemini (via Vertex AI SDK)
- **Database**: SQLite (default) or PostgreSQL + pgvector
- **Vector Store**: ChromaDB
- **Frontend**: React + TypeScript (located in web/ directory)

## Core Component Architecture
- [main.py](main.py): Application entry point, responsible for initializing all core components
- [core/](core/) directory contains:
  - [gemini_client.py](core/gemini_client.py): Wraps Vertex AI client, handles Gemini API calls
  - [personality_engine.py](core/personality_engine.py): Personalized conversation engine, integrates user profile, knowledge base, and conversation memory
  - [user_profile.py](core/user_profile.py): User profile management system
  - [knowledge_base.py](core/knowledge_base.py): Knowledge base management (using ChromaDB)
  - [memory.py](core/memory.py): Conversation memory and history management
- [api/](api/) directory contains all REST API routes

## Development Commands
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Development Server**: `python -m uvicorn main:app --reload`
- **Run Tests** (if available): `pytest` or `python -m pytest`
- **Run Single Test**: `python -m pytest path/to/test_file.py`

## Configuration Management
- Configuration is managed through the Settings class in [config.py](config.py)
- Environment variables are stored in `.env` file (see `.env.example`)
- Main configurations include: GCP project info, Gemini model settings, database connection, admin password, etc.

## API Endpoints
- `/api/chat/` - Chat functionality (send messages, get history)
- `/api/knowledge/` - Knowledge base management
- `/api/interview/` - Q&A collection functionality
- `/api/auth/` - Authentication functionality
- `/api/settings/` - Settings management

## Authentication Mechanism
- Admin features require password protection (default password in config.py)
- Chat functionality has public access password (to prevent abuse)

## Deployment Options
- **Local Run**: Start directly using uvicorn
- **Containerized**: Use [Dockerfile](Dockerfile), exposes port 8080
- **GCP Deployment**: Supports Cloud Run and other deployment methods (see DEPLOY.md)

## Important Notes
- Project uses Vertex AI SDK, requires proper GCP credential configuration
- Conversation history is stored in memory, can be persisted via GCS
- Default admin and access passwords need to be changed in production environment
