# Overview

CasualNotes.in is a web application that transforms text input into visual napkin-style infographics using AI. The application analyzes user-provided text content and generates hand-drawn, sketchy visual diagrams that resemble concepts sketched on napkins. It leverages Google Gemini AI to intelligently structure content into professional infographic layouts with various visual elements like flowcharts, concept maps, and hierarchical diagrams.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Single Page Application**: Built with vanilla HTML, CSS, and JavaScript for simplicity and fast loading times
- **Canvas-based Rendering**: Uses HTML5 canvas with Rough.js library to create authentic hand-drawn, sketchy aesthetic
- **Handwritten Typography**: Patrick Hand Google Font provides napkin-like handwritten appearance throughout the interface
- **Visual Components**: Supports multiple visual element types including boxes, arrows, and lists with color-coded sections for organization
- **Export Functionality**: HTML2Canvas library enables users to download generated infographics as PNG images
- **Responsive Design**: Mobile-friendly layout that adapts to different screen sizes and devices

## Backend Architecture
- **Flask Web Framework**: Lightweight Python web server with minimal complexity for rapid development and deployment
- **Single Route Design**: Main `/generate` endpoint processes text input and returns structured JSON responses
- **Error Handling**: Comprehensive exception handling with graceful degradation and fallback responses when AI services fail
- **Logging System**: Debug-level logging for monitoring AI interactions and troubleshooting system issues
- **Session Management**: Basic session handling with configurable secret key for security

## AI Integration
- **Google Gemini API**: Primary AI service for intelligent text analysis and automated infographic generation
- **Structured Prompting**: Strict JSON schema enforcement ensures consistent, parseable output format from AI responses
- **Professional Design Principles**: AI prompt includes visual hierarchy and layout design guidelines for business-quality output
- **Response Cleaning**: Regex-based JSON extraction handles inconsistent AI response formatting and ensures data integrity
- **Layout Intelligence**: AI determines optimal layout types including process_flow, concept_map, hierarchy, and comparison based on content analysis

## Data Flow Architecture
- **Processing Pipeline**: User text → AI analysis → Structured JSON → Canvas visualization in a streamlined workflow
- **Schema Validation**: Enforced JSON structure with title, layout, visual_flow, and sections array for consistent rendering
- **Visual Mapping**: JSON element types and properties directly mapped to specific canvas drawing functions
- **Color System**: Predefined color palette (blue, green, orange, red, purple, teal) ensures visual consistency across all generated infographics

# External Dependencies

## AI Services
- **Google Gemini API**: Core generative AI service for text-to-infographic conversion and intelligent content structuring
- **API Key Management**: Environment variable-based configuration for secure credential storage and deployment flexibility

## Frontend Libraries
- **Rough.js (v4.6.6)**: Specialized graphics library for creating hand-drawn style canvas rendering with authentic sketchy appearance
- **HTML2Canvas (v1.4.1)**: Client-side image generation library enabling PNG export functionality for user downloads
- **Google Fonts**: Patrick Hand font family provides authentic handwritten typography matching the napkin aesthetic

## Python Dependencies
- **Flask**: Lightweight web framework for HTTP request handling and template rendering
- **Google Generative AI**: Official Python client library for Google Gemini API integration and response processing