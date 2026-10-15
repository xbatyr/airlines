# Working as a team of three

This is a suggested split. Replace Student 1/2/3 with your real names and record
each person's actual work in the final report. The initial code was prepared
with AI assistance; follow your course's rules for acknowledging assistance.
Each teammate should understand and be able to modify every part at the defense.

| Teammate | Main area | Suggested work |
| --- | --- | --- |
| Student 1 | `database.py` | Understand the schema, improve sample data, explain foreign keys and `random` |
| Student 2 | `airline.py` | Check reservation rules, validation with `re`, calculations, and export |
| Student 3 | `main.py` | Improve prompts/tables, demonstrate all menu paths, capture screenshots |

All three review changes, run tests, and contribute to the report/presentation.
Keep the public method names agreed between modules; discuss interface changes
before modifying another teammate's file.

## Before working

```bash
git switch main
git pull --ff-only
git switch -c feature/your-task
```

Choose a distinct branch name, such as `feature/menu-prompts`,
`feature/sample-data`, or `feature/report-format`.

## After making changes

Keep the code beginner-friendly and use only Python's standard library.
Every non-empty Python line must have a lowercase English explanatory comment
in the format `# does ...`. Run the tests and try the relevant menu path:

```bash
python3 -m unittest discover -s tests -v
python3 main.py
git status
git add main.py
git commit -m "Improve menu prompts"
git push -u origin feature/your-task
```

Replace `main.py` and the commit message with the files and change you actually
made. Open a pull request on GitHub and ask another teammate to review it.
Merge after checks pass, then pull the updated `main` before starting new work.

## Local database and report

Each teammate has a separate local `project.db` and `results.txt`; Git ignores
both. The source code recreates the same initial sample dataset in an empty
database. Database edits are not shared through Git.

To reset sample data intentionally, first stop the program and rename the old
database to a backup **outside this repository**. Then run `python3 main.py`.
This creates a new sample database. Keep the backup if it contains work you need.
Do not reset the shared final submission data without discussing it with the team.

Choose one teammate to collect the final files and verify the dataset minimums.
Export the final report from that exact database so the calculations agree.
