# Move the frontend suite census into scripts/test.sh frontend

> What the user said, verbatim. Not summarised, not corrected -- this is the input the rest of the process interprets.

spec/design/testing.md section What only CI can answer names the frontend suite census as a declared gap: only CI refuses a vitest run that collected zero tests (the frontend job's step The frontend suite collected tests), while test.sh e2e carries the equivalent for the black box inside the script. Article XII asks for the check to live in scripts/test.sh frontend, where check.sh reaches it and a workstation answers the same question CI does.
