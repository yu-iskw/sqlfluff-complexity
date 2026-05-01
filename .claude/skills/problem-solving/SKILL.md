---
name: problem-solving
description: Broadly and deeply analyze user intent (avoiding XY problems) and evaluate multiple solution approaches (default 5) with scores from 0 to 100.
---

# Problem Solving

## Purpose

This skill enables a systematic and thorough evaluation of potential solutions for a given issue. It goes beyond the stated problem to identify the user's true underlying intent, avoiding the "XY Problem" (asking for a solution to an intermediate step rather than the root goal). It ensures that multiple perspectives are considered and that the final recommendation is backed by a structured scoring process.

## Instructions

1.  **Analyze Intent & Issue**: Perform a broad and deep analysis.
    - **Identify Stated Problem (X)**: What did the user explicitly ask for?
    - **Discover Underlying Intent (Y)**: What is the user _actually_ trying to achieve? Look for the root goal.
    - **XY Problem Check**: Explicitly evaluate if the user's request (X) is a sub-optimal path to their goal (Y). Challenge the premise if necessary.
2.  **Determine Approaches**: Generate $n$ different approaches to satisfy the **Underlying Intent (Y)**.
    - By default, $n = 5$.
    - If the user specifies a different number of approaches, use that number.
    - Include approaches that solve (Y) directly, even if they bypass the user's stated (X).
3.  **Define Scoring Criteria**: Based on the nature of the issue and the underlying intent, define the most relevant criteria for evaluation (e.g., Feasibility, Complexity, Performance, Maintainability, Security).
4.  **Score Approaches**: Evaluate each approach against the defined criteria using a scale of 0 to 100.
5.  **Generate Report**: Use the `assets/templates/analysis-report.md` template to present your findings.
    - Ensure the report is comprehensive and clearly justifies the scores and the final recommendation in the context of the true intent.

## Examples

### Example 1: High-level architectural change

**Input**: "We need to migrate our legacy monolith to microservices. Analyze the approaches."
**Output**: A report identifying the intent (e.g., "Improve scalability and deployment speed"). The XY check might note that microservices are a _means_, not the _end_. Approaches might include "Modular Monolith" or "Serverless" alongside traditional microservices.

### Example 2: The XY Problem (Custom Parser)

**Input**: "How do I fix this regex for parsing nested HTML tags in my custom scraper?"
**Output**: A report identifying the Stated Problem (Regex fix) and the Underlying Intent (Extracting data from HTML). The XY check would note that regex is unsuitable for nested HTML. Approaches would include "Use BeautifulSoup/Cheerio", "Use a dedicated HTML parser library", etc., scoring them much higher than the "Fix Regex" approach.

## Additional Resources

- Template: [assets/templates/analysis-report.md](assets/templates/analysis-report.md)
