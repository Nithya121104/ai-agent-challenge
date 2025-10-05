<img width="1024" height="1536" alt="a378d052-f96e-44be-b690-19fc9f796ed9" src="https://github.com/user-attachments/assets/e68ff68b-1f00-469c-bd6b-3cc833b290c5" />
Coding agent challenge which write custom parsers for Bank statement PDF.
This project is part of the challenge to build an autonomous agent that generates custom parsers for bank statement PDFs, validates them against expected CSV outputs, and self-corrects when tests fail.
Run Instructions:
1. Setup Python environment
2. Install dependencies
3. Prepare input data
4. Run Agent
5. Review results
 ┌─────────────────────────────┐
 │       START (Agent Loop)    │
 └───────────────┬─────────────┘
                 │
                 ▼
       ┌───────────────────────┐
       │   1. PLAN             │
       │ - Analyze PDF layout  │
       │ - Read CSV schema     │
       │ - Understand reqs     │
       └───────────┬───────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │   2. GENERATE         │
       │ - LLM writes parser   │
       │ - Use pdfplumber +    │
       │   pandas              │
       └───────────┬───────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │   3. TEST             │
       │ - Run parser          │
       │ - Compare output      │
       │   (DataFrame.equals)  │
       └───────────┬───────────┘
                   │
         ┌─────────┴───────────┐
         │ Test Passed?         │
         │ (Within 3 loops?)    │
         └─────────┬───────────┘
                   │Yes
                   ▼
       ┌───────────────────────┐
       │   SUCCESS (Exit)      │
       └───────────────────────┘

                   │No
                   ▼
       ┌───────────────────────┐
       │   4. REFINE           │
       │ - Self-debug errors   │
       │ - Modify parser code  │
       └───────────┬───────────┘
                   │
                   └──► (Back to PLAN, max 3 cycles)
