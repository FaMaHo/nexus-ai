# Integration Points

## Overview

nexus-ai integrates with several external systems to provide a seamless productivity and planning experience. This document outlines current and planned integration points.

## Current Integrations

### Google Calendar
- **Purpose**: Sync events, analyze schedule, suggest optimal task times
- **Method**: OAuth 2.0, Google Calendar API
- **Features**: Read events, find free time, classify event types

### Reclaim.ai
- **Purpose**: Export tasks for advanced scheduling
- **Method**: Export compatible task lists
- **Features**: Monitor scheduled tasks, learn from execution patterns

## Planned Integrations

### Notion
- **Purpose**: Sync project notes and knowledge bases
- **Status**: Planned (see Future Features)

### GitHub
- **Purpose**: Link coding goals to repositories, track progress via commits
- **Status**: Planned

### Todoist/Any.do
- **Purpose**: Import existing tasks and habits
- **Status**: Planned

### Apple Health / Google Fit
- **Purpose**: Correlate health data with productivity
- **Status**: Planned

## Integration Architecture
- All integrations are modular and can be enabled/disabled
- Data privacy is maintained: only necessary data is synced
- API keys and tokens are stored securely

---

_Created: {{date}} | Last Updated: {{date}}_ _Tags: #integration #architecture #external-systems_
