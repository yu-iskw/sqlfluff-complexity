---
name: initialize-project
description: Initialize a new project from the Python template by renaming packages, updating metadata, and cleaning up documentation. Use when starting a new project, "bootstrapping" from this template, or setting up a fresh repository.
---

# Initialize Project

## Purpose

This skill automates the initial setup of a new project derived from this template. It leverages AI capabilities to directly modify project metadata and documentation by replacing placeholders, ensuring a clean start for a new repository.

## Instructions

1. **Gather Information**: Ask the user for:
   - New project name (e.g., `my-awesome-app`)
   - Project description
   - Author name (e.g., `Your Name <your.email@example.com>`)
2. **Update Project Metadata**: Directly update the following files using the `Write` or `StrReplace` tools:
   - `pyproject.toml`: Update `project.name`, `project.description`, and `project.authors`.
   - Update `tool.hatch.build.targets.wheel.packages` to match the new source directory.
3. **Rename Source Package**:
   - Rename `src/your_package` to the new package name (e.g., `src/my_awesome_app`).
   - Update any internal imports if they reference `your_package`.
4. **Update README Placeholders**: Use the `StrReplace` tool to replace the placeholders in `README.md` with the gathered information:
   - `{PROJECT_NAME}` -> New project name
   - `{PROJECT_DESCRIPTION}` -> Project description
5. **Install Dependencies**: Run `make setup` to initialize the environment and update `uv.lock`.
6. **Final Cleanup**: Remove the initialization skill and its related files once bootstrapping is complete, if requested by the user.

## Examples

### Example 1: Initializing a new CLI tool

**Input**: User says "Initialize this project as 'json-fixer', a CLI tool to fix broken JSON files."
**Action**:

1. Gather details from the user (Name: json-fixer, Description: A CLI tool to fix broken JSON files, Author: [Author Name]).
2. Update `pyproject.toml` with the new metadata.
3. Rename `src/your_package` to `src/json_fixer`.
4. Use `StrReplace` on `README.md` to swap placeholders with actual values.
5. Run `make setup`.
