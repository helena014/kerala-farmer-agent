# Kerala Farmer Advisory Agent

AI system that automatically sends personalized farming advisories to Kerala farmers in native language.

## Problem Statement

Small and marginal farmers in Kerala lack access to real-time crop prices, weather advisories, and pest alerts in their native languages. They are forced to rely on middlemen for pricing information, often selling their crops below market value. Weather and pest warnings from government sources exist but are not accessible to most farmers. This information gap leads to significant crop losses and financial hardship for thousands of farming families in Kerala.

---

# Components

## 1. Farmer Profile Store

SQLite database storing each farmer's:

* Name
* Crop
* District
* Phone number
* Language preference

In production this would be PostgreSQL.

---

## 2. Scheduled Data Fetcher

APScheduler triggers three parallel data fetches:

* Market prices from Agmarknet
* Weather forecasts from IMD
* Pest bulletins from Kerala Agriculture Department

Currently the data is simulated with:

* Real Kerala price ranges
* District-wise weather patterns

In production these would be live API calls.

---

## 3. Personalization Engine

Filters the fetched data for each specific farmer based on:

* Crop
* District
* Language preference

---

## 4. Message Composer Agent

Calls Google Gemini 2.0 Flash with a carefully engineered prompt.

It takes:

* Price data
* Weather forecast
* Pest alerts

and generates a conversational Malayalam WhatsApp message.

---

## 5. Reactive Q&A Handler

After receiving the morning message, farmers can reply with any question.

Gemini answers in Malayalam using conversation history for context.

---

## 6. Delivery Engine

Currently messages are shown in the dashboard.

In production, this sends messages via WhatsApp Business API.
