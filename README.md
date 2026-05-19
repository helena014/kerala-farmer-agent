Kerala Farmer Advisory Agent:
 AI system that automatically sends personalized farming advisories to Kerala farmers in native language
Problem Statement:
Small and marginal farmers in Kerala lack access to real-time crop prices, weather advisories, and pest alerts in their native languages. They are forced to rely on middlemen for pricing information, often selling their crops below market value. Weather and pest warnings from government sources exist but are  making them inaccessible to most farmers. This information gap leads to significant crop losses and financial hardship for thousands of farming families in Kerala.

It has 6 components:
  — Farmer Profile Store. SQLite database storing each farmer's name, crop, district, phone number and language preference. In production this would be PostgreSQL.
  — Scheduled Data Fetcher. APScheduler triggers three parallel data fetches — market prices from Agmarknet, weather forecasts from IMD, and pest bulletins from Kerala Agriculture Department. Here the data is simulated with real Kerala price ranges and district-wise weather patterns but in production these would be live API calls.
  — Personalization Engine. This filters the fetched data for each specific farmer. 
  — Message Composer Agent. This calls Google Gemini 2.0 Flash with a carefully engineered prompt. It takes the price data, weather forecast, and pest alert, and generates a conversational Malayalam WhatsApp message 
  — Reactive Q&A Handler. After receiving the morning message, farmers can reply with any question. Gemini answers in Malayalam using conversation history for context.
  — Delivery Engine.  messages are shown in the dashboard. In production, this sends via WhatsApp Business AP
