---
name: product-research-blueprint
description: >-
  Blueprint for website product analysis and deep competitor research.
  Combines SEO audit, deep research methodology, and competitive analysis.
metadata:
  hermes:
    blueprint:
      name: product-research-workflow
      description: "Analyze a website product and perform deep competitor research"
      default_schedule: "every 24h"
      slots:
        - name: target_url
          description: "The URL of the product website to analyze"
          type: string
          required: true
        - name: competitors
          description: "Comma-separated list of known competitor URLs (optional)"
          type: string
          required: false
---

# Product Research & Website Analysis Workflow

This skill acts as a comprehensive blueprint for product research. It combines techniques from site auditing, competitive analysis, and deep research.

## Workflow Execution

When running this analysis:
1.  **Site Audit**: Use web_extract/web_search to gather the technical and content structure of `{{target_url}}`.
2.  **Product Positioning**: Identify the core value proposition, target audience, and pricing models.
3.  **Competitor Mapping**: 
    - If `{{competitors}}` are provided, extract their positioning.
    - Otherwise, use `web_search` to find competitors and map the landscape.
4.  **Deep Research Synthesis**: Generate a structured report comparing features, market gaps, and strategies.

## Instructions
1. First, navigate to the target product website.
2. Extract the main landing page, pricing page, and features page.
3. Search the web for reviews and competitor comparisons.
4. Compile a SWOT analysis based on the collected data.