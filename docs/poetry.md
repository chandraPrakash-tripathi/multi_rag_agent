Goal: Create → Manage Dependencies → Run → Build → Publish
to generate poetry.lock : poetry install
1. Install Poetry
pip install poetry
2. Verify Installation
poetry --version
3. Create a New Project
poetry new my_project
4. Navigate into Project
cd my_project
5. Initialize Poetry in an Existing Project
poetry init
6. View Project Structure
my_project/
├── pyproject.toml
├── README.md
├── src/
├── tests/
└── poetry.lock
7. Understand Important Files
pyproject.toml → Project metadata & dependencies
poetry.lock → Exact dependency versions
.venv/ → Virtual environment (optional)
8. Configure Poetry to Create .venv Inside Project (Recommended)
poetry config virtualenvs.in-project true
9. Install All Dependencies
poetry install
10. Create/Activate Virtual Environment
poetry shell
11. Exit Virtual Environment
exit
12. Find Virtual Environment Path
poetry env info
13. Add a Dependency
poetry add requests
14. Add Multiple Dependencies
poetry add fastapi uvicorn httpx
15. Add Development Dependency
poetry add --group dev pytest black ruff mypy
16. Remove a Dependency
poetry remove requests
17. Update All Dependencies
poetry update
18. Update a Specific Package
poetry update fastapi
19. Show Installed Packages
poetry show
20. Show Dependency Tree
poetry show --tree
21. Run a Python Script
poetry run python main.py
22. Run Any Command
poetry run pytest
poetry run black .
poetry run ruff check .
23. Install Jupyter
poetry add jupyter
24. Export Requirements (if needed)
poetry export -f requirements.txt --output requirements.txt
25. Lock Dependencies Without Installing
poetry lock
26. Reinstall Everything Cleanly
rm -rf .venv poetry.lock
poetry install
27. Build Package
poetry build
28. Publish Package (PyPI)
poetry publish
29. Show Project Information
poetry check
30. Show Current Configuration
poetry config --list
31. Remove Virtual Environment
poetry env remove python
32. List All Virtual Environments
poetry env list
33. Use a Specific Python Version
poetry env use python3.12
34. Install Dependencies After Cloning a Repository
git clone <repo>
cd <repo>
poetry install
35. Typical Daily Workflow
1. git pull
2. poetry install          # only if dependencies changed
3. poetry shell            # or use poetry run
4. code...
5. poetry add <package>    # if new dependency
6. poetry run pytest
7. poetry run ruff check .
8. poetry run black .
9. git commit
10. git push